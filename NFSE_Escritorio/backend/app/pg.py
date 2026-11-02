"""Persistência PostgreSQL durável (psycopg 3, SQL parametrizado, transações).

Esquema: backend/db/001_initial.sql + 002_isolation.sql. Cada `tx()` abre uma
transação READ COMMITTED; travas de linha (FOR UPDATE) só existem dentro dela —
nenhuma chamada externa acontece com transação aberta (ver worker.py).
RLS: quando `current_user_id` está definido, a transação faz
`set_config('app.user_id', ..., true)`; a API deve conectar com papel membro de `nfse_api`.
"""
from __future__ import annotations

import uuid as _uuidmod
from contextlib import contextmanager
from dataclasses import asdict
from typing import Iterator

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .auth import AcessoNegado, Company, Principal
from .domain.models import Ambiente, DadosRascunho, Emissao, Estado, FiscalResult, Outcome, Rascunho, Revisao
from .eligibility import OperacaoNaoLiberada, Release
from .emissions import UniqueRace
from .repository import Job, current_user_id, dps_identity, new_id


def _uuid_ok(v) -> bool:
    try:
        _uuidmod.UUID(str(v))
        return True
    except (ValueError, TypeError):
        return False


def _iso(v) -> str:
    return v.isoformat() if hasattr(v, "isoformat") else str(v)


def _dados(j: dict) -> DadosRascunho:
    return DadosRascunho(**j)


def _draft(r: dict) -> Rascunho:
    return Rascunho(str(r["id"]), str(r["company_id"]), r["versao"], _dados(r["dados"]), r["origem"],
                    str(r["emission_id"]) if r["emission_id"] else None, _iso(r["criado_em"]), _iso(r["atualizado_em"]))


def _result(j: dict | None) -> FiscalResult | None:
    if not j:
        return None
    return FiscalResult(Outcome(j["outcome"]), j["correlation_id"], j["dps_id"], j.get("official_key"),
                        j.get("official_code"), j.get("message"), j.get("artifact_ref"))


def _emission(r: dict) -> Emissao:
    return Emissao(str(r["id"]), str(r["company_id"]), str(r["draft_id"]), r["versao"], Ambiente(r["ambiente"]),
                   r["dps_identity"], _dados(r["snapshot"]), str(r["review_id"]), r["idempotency_key"],
                   Estado(r["estado"]), r["tentativas"], _result(r["resultado"]), r["fingerprint"],
                   r["documento_ref"], _iso(r["criado_em"]), _iso(r["atualizado_em"]))


def _job(r: dict) -> Job:
    return Job(str(r["company_id"]), str(r["emission_id"]), r["tipo"], r["situacao"], r["fence"], r["owner"],
               float(r["lease_epoch"] or 0))


JOB_COLS = "company_id, emission_id, tipo, situacao, fence, owner, extract(epoch from lease_until) AS lease_epoch"


class PgTx:
    def __init__(self, cur: psycopg.Cursor) -> None:
        self.c = cur

    def _one(self, sql, args=()):
        self.c.execute(sql, args)
        return self.c.fetchone()

    def _all(self, sql, args=()):
        self.c.execute(sql, args)
        return self.c.fetchall()

    # rascunhos
    def insert_draft(self, r):
        self.c.execute("INSERT INTO draft (company_id, id, versao, dados, origem, criado_em, atualizado_em) "
                       "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                       (r.empresa_id, r.id, r.versao, Jsonb(asdict(r.dados)), Jsonb(r.origem), r.criado_em, r.atualizado_em))
        return r

    def get_draft(self, empresa_id, rid, lock=False):
        if not (_uuid_ok(empresa_id) and _uuid_ok(rid)):
            raise AcessoNegado()
        row = self._one("SELECT * FROM draft WHERE company_id=%s AND id=%s" + (" FOR UPDATE" if lock else ""), (empresa_id, rid))
        if not row:
            raise AcessoNegado()
        return _draft(row)

    def list_drafts(self, empresa_id):
        return [_draft(r) for r in self._all("SELECT * FROM draft WHERE company_id=%s AND emission_id IS NULL "
                                             "ORDER BY atualizado_em DESC", (empresa_id,))]

    def save_draft(self, r):
        self.c.execute("UPDATE draft SET versao=%s, dados=%s, emission_id=%s, atualizado_em=%s WHERE company_id=%s AND id=%s",
                       (r.versao, Jsonb(asdict(r.dados)), r.emissao_id, r.atualizado_em, r.empresa_id, r.id))
        return r

    def delete_draft(self, empresa_id, rid):
        self.c.execute("DELETE FROM draft WHERE company_id=%s AND id=%s AND emission_id IS NULL", (empresa_id, rid))
        if self.c.rowcount != 1:
            raise AcessoNegado()

    # revisões
    def insert_review(self, rev):
        self.c.execute("INSERT INTO review (company_id, id, draft_id, versao, hash, user_id, em) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                       (rev.empresa_id, rev.id, rev.rascunho_id, rev.versao, rev.hash, rev.usuario_id, rev.em))

    @staticmethod
    def _rev(r):
        return Revisao(str(r["id"]), str(r["company_id"]), str(r["draft_id"]), r["versao"], r["hash"], r["user_id"], _iso(r["em"]))

    def get_review(self, empresa_id, rev_id):
        if not _uuid_ok(rev_id):
            return None
        r = self._one("SELECT * FROM review WHERE company_id=%s AND id=%s", (empresa_id, rev_id))
        return self._rev(r) if r else None

    def latest_review(self, empresa_id, rid):
        r = self._one("SELECT * FROM review WHERE company_id=%s AND draft_id=%s ORDER BY em DESC LIMIT 1", (empresa_id, rid))
        return self._rev(r) if r else None

    # importação
    def origins(self, empresa_id):
        return {(r["sistema_origem"], r["id_origem"]): r["conteudo"] for r in
                self._all("SELECT sistema_origem, id_origem, conteudo FROM import_row WHERE company_id=%s", (empresa_id,))}

    def insert_batch(self, empresa_id, batch_id, layout, totals):
        self.c.execute("INSERT INTO import_batch (company_id, id, layout, totals) VALUES (%s,%s,%s,%s)",
                       (empresa_id, batch_id, layout, Jsonb(totals)))

    def insert_origin(self, empresa_id, batch_id, linha, sistema, id_origem, conteudo, draft_id):
        r = self._one("INSERT INTO import_row (company_id, batch_id, linha, sistema_origem, id_origem, conteudo, draft_id) "
                      "VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (company_id, sistema_origem, id_origem) DO NOTHING RETURNING 1",
                      (empresa_id, batch_id, linha, sistema, id_origem, conteudo, draft_id))
        return r is not None

    # emissões
    def emission_by_key(self, empresa_id, key):
        r = self._one("SELECT * FROM emission WHERE company_id=%s AND idempotency_key=%s", (empresa_id, key))
        return _emission(r) if r else None

    def emission_for_version(self, empresa_id, rid, versao, ambiente):
        r = self._one("SELECT * FROM emission WHERE company_id=%s AND draft_id=%s AND versao=%s AND ambiente=%s",
                      (empresa_id, rid, versao, ambiente))
        return _emission(r) if r else None

    def insert_emission(self, e):
        try:
            with self.c.connection.transaction():  # savepoint
                self.c.execute(
                    "INSERT INTO emission (company_id, id, draft_id, versao, ambiente, dps_identity, snapshot, review_id, "
                    "idempotency_key, fingerprint, estado, tentativas, criado_em, atualizado_em) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (e.empresa_id, e.id, e.rascunho_id, e.versao, e.ambiente.value, e.identidade_dps, Jsonb(asdict(e.snapshot)),
                     e.revisao_id, e.chave_idempotente, e.fingerprint, e.estado.value, e.tentativas, e.criado_em, e.atualizado_em))
        except psycopg.errors.UniqueViolation as exc:
            raise UniqueRace() from exc

    def get_emission(self, empresa_id, eid, lock=False):
        if not (_uuid_ok(empresa_id) and _uuid_ok(eid)):
            raise AcessoNegado()
        r = self._one("SELECT * FROM emission WHERE company_id=%s AND id=%s" + (" FOR UPDATE" if lock else ""), (empresa_id, eid))
        if not r:
            raise AcessoNegado()
        return _emission(r)

    def list_emissions(self, empresa_id, rid=None, versao=None):
        if rid is not None and not _uuid_ok(rid):
            return []
        return [_emission(r) for r in self._all(
            "SELECT * FROM emission WHERE company_id=%s AND (%s::uuid IS NULL OR draft_id=%s::uuid) "
            "AND (%s::int IS NULL OR versao=%s::int) ORDER BY criado_em DESC", (empresa_id, rid, rid, versao, versao))]

    def save_emission(self, e):
        r = self._one("UPDATE emission SET estado=%s, tentativas=%s, resultado=%s, documento_ref=%s, atualizado_em=now() "
                      "WHERE company_id=%s AND id=%s RETURNING *",
                      (e.estado.value, e.tentativas, Jsonb({**asdict(e.resultado), "outcome": e.resultado.outcome.value}) if e.resultado else None,
                       e.documento_ref, e.empresa_id, e.id))
        return _emission(r)

    def reserve_dps(self, empresa_id, ambiente):
        r = self._one("INSERT INTO dps_sequence (company_id, ambiente, last_value) VALUES (%s,%s,1) "
                      "ON CONFLICT (company_id, ambiente) DO UPDATE SET last_value = dps_sequence.last_value + 1 "
                      "RETURNING last_value", (empresa_id, ambiente))
        return dps_identity(empresa_id, ambiente, r["last_value"])

    # jobs
    def insert_job(self, empresa_id, eid, tipo):
        self.c.execute("INSERT INTO job (company_id, emission_id, tipo, situacao) VALUES (%s,%s,%s,'pendente')", (empresa_id, eid, tipo))

    def get_job(self, empresa_id, eid, lock=False):
        r = self._one(f"SELECT {JOB_COLS} FROM job WHERE company_id=%s AND emission_id=%s" + (" FOR UPDATE" if lock else ""),
                      (empresa_id, eid))
        return _job(r) if r else None

    def save_job(self, j):
        self.c.execute("UPDATE job SET tipo=%s, situacao=%s, fence=%s, owner=%s, lease_until=to_timestamp(%s) "
                       "WHERE company_id=%s AND emission_id=%s",
                       (j.tipo, j.situacao, j.fence, j.dono, j.lease_ate, j.empresa_id, j.emissao_id))

    def next_claimable(self, now):
        r = self._one(f"SELECT {JOB_COLS} FROM job WHERE (situacao='pendente' AND run_at <= to_timestamp(%s)) "
                      "OR (situacao='em_execucao' AND lease_until < to_timestamp(%s)) "
                      "ORDER BY run_at LIMIT 1 FOR UPDATE SKIP LOCKED", (now, now))
        return _job(r) if r else None

    def insert_attempt(self, empresa_id, eid, fence):
        self.c.execute("INSERT INTO attempt (company_id, emission_id, fence) VALUES (%s,%s,%s)", (empresa_id, eid, fence))


class PostgresRepository:
    durable = True

    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise ValueError("DSN obrigatório")
        self.dsn = dsn

    @staticmethod
    def new_id(_prefix: str = "") -> str:
        return new_id()

    @contextmanager
    def tx(self) -> Iterator[PgTx]:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    uid = current_user_id.get()
                    if uid:
                        cur.execute("SELECT set_config('app.user_id', %s, true)", (uid,))
                    yield PgTx(cur)


class PgMemberships:
    durable = True

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def _q(self, sql, args=(), fetch=True):
        with psycopg.connect(self.dsn, row_factory=dict_row) as c:
            cur = c.execute(sql, args)
            return cur.fetchall() if fetch else None

    def grant(self, user_id, empresa_id, perms):
        self._q("INSERT INTO membership (user_id, company_id, permissions) VALUES (%s,%s,%s) ON CONFLICT (user_id, company_id) "
                "DO UPDATE SET permissions=EXCLUDED.permissions, revoked_at=NULL", (user_id, empresa_id, sorted(perms)), fetch=False)

    def revoke(self, user_id, empresa_id):
        self._q("UPDATE membership SET revoked_at=now() WHERE user_id=%s AND company_id=%s", (user_id, empresa_id), fetch=False)

    def empresas(self, user_id):
        return [str(r["company_id"]) for r in self._q("SELECT company_id FROM membership WHERE user_id=%s AND revoked_at IS NULL", (user_id,))]

    def require(self, p: Principal, empresa_id: str, perm: str) -> None:
        ok = _uuid_ok(empresa_id) and self._q(
            "SELECT 1 FROM membership WHERE user_id=%s AND company_id=%s AND revoked_at IS NULL AND %s = ANY(permissions)",
            (p.user_id, empresa_id, perm))
        if not ok:
            raise AcessoNegado()


class PgCompanies:
    durable = True

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def add(self, c: Company) -> None:
        with psycopg.connect(self.dsn) as conn:
            conn.execute("INSERT INTO company (id, cnpj, razao_social, municipio) VALUES (%s,%s,%s,%s)",
                         (c.id, "".join(ch for ch in c.cnpj if ch.isdigit()), c.razao_social, c.municipio))

    def get(self, cid: str) -> Company | None:
        if not _uuid_ok(cid):
            return None
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            r = conn.execute("SELECT * FROM company WHERE id=%s", (cid,)).fetchone()
        return Company(str(r["id"]), r["razao_social"], r["cnpj"], r["municipio"]) if r else None


class PgReleases:
    durable = True

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def register(self, r: Release) -> None:
        if not r.evidencia.strip():
            raise ValueError("Liberação exige evidência")
        with psycopg.connect(self.dsn) as conn:
            conn.execute("INSERT INTO operation_release (company_id, operacao, ambiente, versao, evidencia, autor) "
                         "VALUES (%s,%s,%s,%s,%s,%s)", (r.empresa_id, r.operacao, r.ambiente, r.versao, r.evidencia, r.autor))

    def _rows(self, where, args):
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            return conn.execute("SELECT DISTINCT ON (company_id, operacao, ambiente) * FROM operation_release WHERE "
                                + where + " AND valid_from <= now() AND (valid_to IS NULL OR valid_to > now()) "
                                "ORDER BY company_id, operacao, ambiente, versao DESC", args).fetchall()

    def require(self, empresa_id, operacao, ambiente) -> Release:
        rows = self._rows("company_id=%s AND operacao=%s AND ambiente=%s", (empresa_id, operacao, ambiente))
        if not rows:
            raise OperacaoNaoLiberada()
        r = rows[0]
        return Release(str(r["company_id"]), r["operacao"], r["ambiente"], r["versao"], r["evidencia"], r["autor"])

    def for_company(self, empresa_id):
        return [Release(str(r["company_id"]), r["operacao"], r["ambiente"], r["versao"], r["evidencia"], r["autor"])
                for r in self._rows("company_id=%s", (empresa_id,))]


def apply_migrations(dsn: str, paths: list[str]) -> None:
    with psycopg.connect(dsn, autocommit=True) as conn:
        for p in paths:
            conn.execute(open(p, encoding="utf-8").read())
