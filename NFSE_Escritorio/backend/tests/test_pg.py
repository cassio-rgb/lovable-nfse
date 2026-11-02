"""Testes de integração PostgreSQL. Executam SOMENTE com TEST_DATABASE_URL explícito.

Salvaguardas (tests/pg_guard.py, checadas antes de importar/conectar): dbname exato
nfse_test ou nfse_test_<sufixo>, host local/unix socket e NFSE_PG_ALLOW_SCHEMA_RESET=
nfse_test_reset_public. O schema `public` é recriado (destrutivo). Sem fallback de banco.
"""
import os
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

DSN = os.environ.get("TEST_DATABASE_URL", "")
DB = Path(__file__).resolve().parent.parent / "db"

if DSN:
    from tests import pg_guard

    pg_guard.check(DSN, os.environ)  # falha antes de qualquer conexão
    import psycopg
    from fastapi.testclient import TestClient

    from app import emissions, imports, reviews, worker
    from app.api import ApiSettings, Deps, create_app
    from app.auth import Company, Principal
    from app.documents import MemoryStorage
    from app.domain.models import Ambiente, Estado, Outcome, Rascunho
    from app.eligibility import Release
    from app.pg import PgCompanies, PgMemberships, PgReleases, PostgresRepository, apply_migrations
    from app.repository import current_user_id
    from tests.helpers import FakeAdapter, dados


A = str(uuid.UUID(int=0xA))
B = str(uuid.UUID(int=0xB))
R = None


def reset():
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;")
    apply_migrations(DSN, [str(DB / "001_initial.sql"), str(DB / "002_isolation.sql")])
    comp, mem, rel = PgCompanies(DSN), PgMemberships(DSN), PgReleases(DSN)
    comp.add(Company(A, "Empresa A Fictícia", "11222333000181", "Bariri/SP"))
    comp.add(Company(B, "Empresa B Fictícia", "45723174000110", "Pederneiras/SP"))
    mem.grant("u1", A, {"ler", "editar", "emitir"})
    mem.grant("u2", B, {"ler", "editar", "emitir"})
    rel.register(Release(A, "locacao", "producao_restrita", 1, "evidência de teste", "esc"))
    return PostgresRepository(DSN), mem, comp, rel


def reviewed(repo, emp=A):
    rid = repo.new_id()
    with repo.tx() as t:
        t.insert_draft(Rascunho(rid, emp, 1, dados()))
    rev = reviews.prepare(repo, Principal("u1", "escritorio"), emp, rid, 1)
    return rid, rev


@unittest.skipUnless(DSN, "TEST_DATABASE_URL não definido — testes PostgreSQL NÃO executados")
class PgPersistence(unittest.TestCase):
    def setUp(self):
        self.repo, self.mem, self.comp, self.rel = reset()
        self.p = Principal("u1", "escritorio")

    def confirm(self, rid, rev, key):
        return emissions.confirm(self.repo, self.mem, self.rel, self.p, A, rid, rev.id, 1,
                                 Ambiente.PRODUCAO_RESTRITA, key, True)

    def test_durable_across_instances_and_review_invalidation(self):
        rid, rev = reviewed(self.repo)
        reviews.update_draft(self.repo, A, rid, 1, dados("999.00"))
        fresh = PostgresRepository(DSN)
        with fresh.tx() as t:
            self.assertEqual(t.get_draft(A, rid).versao, 2)
            self.assertFalse(reviews.is_valid_in(t, rev))

    def test_concurrent_confirms_one_emission(self):
        rid, rev = reviewed(self.repo)
        with ThreadPoolExecutor(8) as ex:
            ids = list(ex.map(lambda i: self.confirm(rid, rev, f"chave-{i % 3}-{rid}").id, range(8)))
        self.assertEqual(len(set(ids)), 1)
        with psycopg.connect(DSN) as c:
            self.assertEqual(c.execute("SELECT count(*) FROM emission").fetchone()[0], 1)
            self.assertEqual(c.execute("SELECT count(*) FROM job").fetchone()[0], 1)

    def test_concurrent_dps_reservation_unique(self):
        pairs = [reviewed(self.repo) for _ in range(6)]
        with ThreadPoolExecutor(6) as ex:
            es = list(ex.map(lambda pr: self.confirm(pr[0], pr[1], f"k-{pr[0]}"), pairs))
        self.assertEqual(len({e.identidade_dps for e in es}), 6)

    def test_same_key_other_content_conflicts(self):
        rid, rev = reviewed(self.repo)
        rid2, rev2 = reviewed(self.repo)
        self.confirm(rid, rev, "mesma")
        from app.domain.transitions import ConflitoVersao
        with self.assertRaises(ConflitoVersao):
            self.confirm(rid2, rev2, "mesma")

    def test_concurrent_import_no_duplicates(self):
        rows = imports.read_rows("x.csv", ("id_origem;tomador_documento;tomador_nome;operacao;competencia;valor;descricao\n"
                                           "Z1;529.982.247-25;Maria;locacao;11/2026;100,00;Administração nov\n").encode())
        linhas = imports.preview(self.repo, A, rows)
        with ThreadPoolExecutor(5) as ex:
            res = list(ex.map(lambda _: imports.confirm(self.repo, A, linhas, {2}), range(5)))
        self.assertEqual(sum(r["criados"] for r in res), 1)
        with self.repo.tx() as t:
            self.assertEqual(len(t.list_drafts(A)), 1)

    def test_worker_skip_locked_fencing_and_recovery(self):
        rid, rev = reviewed(self.repo)
        e = self.confirm(rid, rev, "w")
        barrier = threading.Barrier(2)
        import time
        self.t0 = time.time() + 1

        def grab(name):
            barrier.wait()
            return worker.claim(self.repo, name, 10, now=self.t0)

        with ThreadPoolExecutor(2) as ex:
            got = [j for j in ex.map(grab, ["w1", "w2"]) if j]
        self.assertEqual(len(got), 1)
        old = got[0]
        self.assertEqual(worker.run_once(self.repo, FakeAdapter(), job=old, crash_after_attempt=True), "crash")
        novo = worker.claim(self.repo, "w3", 10, now=self.t0 + 60)
        self.assertEqual((novo.tipo, novo.fence), ("consultar", old.fence + 1))
        self.assertEqual(worker.run_once(self.repo, FakeAdapter(submit=Outcome.REJECTED), job=replace(old, tipo="consultar")), "stale")
        ad = FakeAdapter(lookup=Outcome.ACCEPTED)
        self.assertEqual(worker.run_once(self.repo, ad, job=novo), "emitida")
        self.assertEqual(ad.submits, 0)
        with self.repo.tx() as t:
            self.assertEqual(t.get_emission(A, e.id).estado, Estado.EMITIDA)
        with psycopg.connect(DSN) as c:
            self.assertEqual(c.execute("SELECT count(*) FROM attempt").fetchone()[0], 1)

    def test_snapshot_immutable_trigger(self):
        rid, rev = reviewed(self.repo)
        e = self.confirm(rid, rev, "imut")
        with psycopg.connect(DSN) as c:
            with self.assertRaises(psycopg.errors.RaiseException):
                c.execute("UPDATE emission SET snapshot='{}'::jsonb WHERE id=%s", (e.id,))

    def test_rls_isolates_companies(self):
        reviewed(self.repo, A)
        with psycopg.connect(DSN, autocommit=True) as c:
            c.execute("INSERT INTO draft (company_id,id,dados,origem) VALUES (%s,%s,'{}','{}')", (B, str(uuid.uuid4())))
        with psycopg.connect(DSN) as c:
            c.execute("SET ROLE nfse_api")
            c.execute("SELECT set_config('app.user_id','u1',true)")
            seen = {str(r[0]) for r in c.execute("SELECT company_id FROM draft").fetchall()}
        self.assertEqual(seen, {A})
        with psycopg.connect(DSN) as c:
            c.execute("SET ROLE nfse_api")
            self.assertEqual(c.execute("SELECT count(*) FROM draft").fetchone()[0], 0)  # sem app.user_id: nada


@unittest.skipUnless(DSN, "TEST_DATABASE_URL não definido — testes PostgreSQL NÃO executados")
class PgApi(unittest.TestCase):
    """Mesma API (create_app) com dependências PostgreSQL duráveis; storage segue em memória (não conectado)."""

    def setUp(self):
        repo, mem, comp, rel = reset()
        from tests.test_api import ORIGIN, TestIdentity
        self.H = {"Origin": ORIGIN, "X-Requested-With": "nfse-imoveis"}
        self.c = TestClient(create_app(Deps(ApiSettings("test", (ORIGIN,)), repo, mem, comp, rel, MemoryStorage(), TestIdentity())))
        self.c.cookies.set("session", "tok-u1")
        self.mem = mem

    def test_flow_cross_company_revocation(self):
        from tests.test_api import DADOS
        j = self.c.get("/v1/sessao").json()
        self.assertEqual([(e["id"], e["cnpj"]) for e in j["empresas"]], [(A, "11.222.333/0001-81")])
        d = self.c.post(f"/v1/empresas/{A}/rascunhos", json={"dados": DADOS}, headers=self.H).json()
        d = self.c.post(f"/v1/empresas/{A}/rascunhos/{d['id']}/revisao", json={"versao": 1}, headers=self.H).json()
        body = {"revisao_id": d["revisao"]["id"], "versao": 1, "ambiente": "producao_restrita", "confirmacao_humana": True}
        e1 = self.c.post(f"/v1/empresas/{A}/rascunhos/{d['id']}/emissao", json=body, headers={**self.H, "Idempotency-Key": "chave-estavel-1"})
        e2 = self.c.post(f"/v1/empresas/{A}/rascunhos/{d['id']}/emissao", json=body, headers={**self.H, "Idempotency-Key": "chave-estavel-1"})
        self.assertEqual((e1.status_code, e1.json()["id"]), (202, e2.json()["id"]))
        found = self.c.get(f"/v1/empresas/{A}/emissoes", params={"rascunho_id": d["id"], "versao": 1}).json()
        self.assertEqual(len(found), 1)
        self.assertEqual(self.c.get(f"/v1/empresas/{A}/emissoes", params={"rascunho_id": "nao-uuid"}).json(), [])
        self.assertEqual(self.c.get(f"/v1/empresas/{A}/rascunhos/nao-uuid").status_code, 404)
        self.c.cookies.set("session", "tok-u2")
        self.assertEqual(self.c.get(f"/v1/empresas/{A}/emissoes/{e1.json()['id']}").status_code, 404)
        self.c.cookies.set("session", "tok-u1")
        self.mem.revoke("u1", A)
        self.assertEqual(self.c.get(f"/v1/empresas/{A}/rascunhos").status_code, 404)


if __name__ == "__main__":
    unittest.main()
