"""Testes de contrato da API real (FastAPI TestClient/ASGI) com dependências injetadas.

Identidade, repositório e storage aqui são dublês de TESTE; a API recusa iniciá-los fora de APP_ENV=test.
"""
import unittest

from fastapi.testclient import TestClient

from app import worker
from app.api import ApiSettings, Deps, create_app
from app.auth import Company, CompanyDirectory, MembershipStore
from app.config import ConfigError
from app.documents import MemoryStorage
from app.domain.models import Outcome
from app.eligibility import Release, ReleaseRegistry
from app.repository import MemoryRepository, current_user_id
from tests.helpers import FakeAdapter, dados as dados_fixture

ORIGIN = "https://app.exemplo.test"
H = {"Origin": ORIGIN, "X-Requested-With": "nfse-imoveis"}


class TestIdentity:
    """Dublê de teste: tokens fixos. Não é autenticação real."""

    tokens = {"tok-u1": {"sub": "u1", "papel": "escritorio"}, "tok-u2": {"sub": "u2", "papel": "cliente"}}

    def verify(self, token):
        if token not in self.tokens:
            raise ValueError("inválido")
        return self.tokens[token]

    def login_url(self, retorno):
        return f"https://idp.exemplo.test/authorize?redirect={retorno}"


DADOS = {"tomador": {"documento": "529.982.247-25", "nome": "Maria Fictícia", "email": ""}, "operacao": "locacao",
         "competencia": "2026-11", "valor": "350.00", "descricao": "Taxa de administração", "imovel": "", "fiscal": dados_fixture().fiscal}


def build(app_env="test"):
    repo, m, c, rel, st = MemoryRepository(), MembershipStore(), CompanyDirectory(), ReleaseRegistry(), MemoryStorage()
    c.add(Company("A", "Empresa A Fictícia", "11.222.333/0001-81", "Bariri/SP"))
    c.add(Company("B", "Empresa B Fictícia", "45.723.174/0001-10", "Pederneiras/SP"))
    m.grant("u1", "A", {"ler", "editar", "emitir"})
    m.grant("u2", "B", {"ler", "editar", "emitir"})
    rel.register(Release("A", "locacao", "producao_restrita", 1, "evidência de teste", "esc"))
    deps = Deps(ApiSettings(app_env, (ORIGIN,)), repo, m, c, rel, st, TestIdentity())
    client = TestClient(create_app(deps), base_url="https://testserver")
    client.cookies.set("session", "tok-u1")
    return client, deps


def novo(client, empresa="A", dados=DADOS):
    r = client.post(f"/v1/empresas/{empresa}/rascunhos", json={"dados": dados}, headers=H)
    assert r.status_code == 201, r.text
    return r.json()


def revisado(client):
    d = novo(client)
    r = client.post(f"/v1/empresas/A/rascunhos/{d['id']}/revisao", json={"versao": 1}, headers=H)
    assert r.status_code == 200, r.text
    return r.json()


def emitir(client, d, key="emissao:A:chave-estavel-1", ambiente="producao_restrita"):
    return client.post(f"/v1/empresas/A/rascunhos/{d['id']}/emissao",
                       json={"revisao_id": d["revisao"]["id"], "versao": d["versao"], "ambiente": ambiente, "confirmacao_humana": True},
                       headers={**H, "Idempotency-Key": key})


class RlsAuthorization(unittest.TestCase):
    def test_membership_receives_verified_identity_before_query(self):
        client, deps = build()
        original = deps.members.require

        def require(principal, empresa, permission):
            self.assertEqual(current_user_id.get(), principal.user_id)
            return original(principal, empresa, permission)

        deps.members.require = require
        marker = current_user_id.set("caller-context")
        try:
            for token, company, status in [
                ("tok-u1", "A", 200), ("tok-u1", "B", 404),
                ("tok-u2", "B", 200), ("tok-u2", "A", 404),
                ("tok-u1", "A", 200),
            ]:
                client.cookies.clear()
                self.assertEqual(client.post("/v1/auth/session", headers={
                    **H, "Authorization": f"Bearer {token}",
                }).status_code, 204)
                self.assertEqual(client.get(f"/v1/empresas/{company}/rascunhos").status_code, status)
                self.assertEqual(current_user_id.get(), "caller-context")
            deps.members.revoke("u1", "A")
            self.assertEqual(client.get("/v1/empresas/A/rascunhos").status_code, 404)
            self.assertEqual(client.delete("/v1/auth/session", headers=H).status_code, 204)
            self.assertEqual(client.get("/v1/empresas/A/rascunhos").status_code, 401)
            self.assertEqual(current_user_id.get(), "caller-context")
        finally:
            current_user_id.reset(marker)
            client.close()


class Startup(unittest.TestCase):
    def test_refuses_memory_outside_test(self):
        with self.assertRaises(ConfigError):
            build("production")

    def test_refuses_without_identity(self):
        deps = build()[1]
        deps.identity = None
        with self.assertRaises(ConfigError):
            create_app(deps)

    def test_main_refuses_to_start(self):
        import importlib, os
        os.environ.update(APP_ENV="production", NFSE_ENVIRONMENT="producao_restrita", IDENTITY_ISSUER="x",
                          IDENTITY_AUDIENCE="y", DATABASE_URL="postgresql://x")
        with self.assertRaises(ConfigError):
            importlib.import_module("app.main")


class Session(unittest.TestCase):
    def test_token_exchange_sets_secure_http_only_cookie(self):
        c, _ = build()
        c.cookies.clear()
        r = c.post(
            "/v1/auth/session",
            headers={**H, "Authorization": "Bearer tok-u1"},
        )
        self.assertEqual(r.status_code, 204)
        cookie = r.headers.get("set-cookie", "")
        self.assertIn("session=tok-u1", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Secure", cookie)
        self.assertIn("SameSite=none", cookie)
        self.assertEqual(c.get("/v1/sessao").status_code, 200)

    def test_invalid_exchange_token_rejected(self):
        c, _ = build()
        c.cookies.clear()
        r = c.post(
            "/v1/auth/session",
            headers={**H, "Authorization": "Bearer forjado"},
        )
        self.assertEqual(r.status_code, 401)

    def test_logout_clears_cookie(self):
        c, _ = build()
        c.cookies.clear()
        self.assertEqual(
            c.post("/v1/auth/session", headers={**H, "Authorization": "Bearer tok-u1"}).status_code,
            204,
        )
        self.assertEqual(c.get("/v1/sessao").status_code, 200)
        r = c.delete("/v1/auth/session", headers=H)
        self.assertEqual(r.status_code, 204)
        self.assertIn("session=", r.headers.get("set-cookie", ""))
        self.assertEqual(c.get("/v1/sessao").status_code, 401)

    def test_sessao_lists_only_authorized(self):
        c, _ = build()
        j = c.get("/v1/sessao").json()
        self.assertEqual([e["id"] for e in j["empresas"]], ["A"])
        self.assertEqual(j["liberacoes"][0]["operacao"], "locacao")

    def test_invalid_token_401(self):
        c, _ = build()
        c.cookies.set("session", "forjado")
        self.assertEqual(c.get("/v1/sessao").status_code, 401)

    def test_login_redirect_only_to_allowed_origin(self):
        c, _ = build()
        self.assertEqual(c.get("/v1/auth/login", params={"retorno": "https://mal.test/x"}, follow_redirects=False).status_code, 400)
        self.assertEqual(c.get("/v1/auth/login", params={"retorno": ORIGIN + "/"}, follow_redirects=False).status_code, 302)


class Csrf(unittest.TestCase):
    def test_mutation_without_origin_or_header_rejected(self):
        c, deps = build()
        self.assertEqual(c.post("/v1/empresas/A/rascunhos", json={"dados": DADOS}).status_code, 403)
        self.assertEqual(c.post("/v1/empresas/A/rascunhos", json={"dados": DADOS}, headers={"Origin": ORIGIN}).status_code, 403)
        self.assertEqual(c.post("/v1/empresas/A/rascunhos", json={"dados": DADOS},
                                headers={"Origin": "https://mal.test", "X-Requested-With": "nfse-imoveis"}).status_code, 403)
        self.assertEqual(len(deps.repo.rascunhos), 0)


class Drafts(unittest.TestCase):
    def test_crud_and_version_conflict(self):
        c, _ = build()
        d = novo(c)
        self.assertEqual(c.get(f"/v1/empresas/A/rascunhos/{d['id']}").json()["versao"], 1)
        up = c.put(f"/v1/empresas/A/rascunhos/{d['id']}", json={"versao_esperada": 1, "dados": {**DADOS, "valor": "400.00"}}, headers=H)
        self.assertEqual(up.json()["versao"], 2)
        stale = c.put(f"/v1/empresas/A/rascunhos/{d['id']}", json={"versao_esperada": 1, "dados": DADOS}, headers=H)
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(len(c.get("/v1/empresas/A/rascunhos").json()), 1)
        self.assertEqual(c.delete(f"/v1/empresas/A/rascunhos/{d['id']}", headers=H).status_code, 204)
        self.assertEqual(c.get(f"/v1/empresas/A/rascunhos/{d['id']}").status_code, 404)

    def test_server_side_validation(self):
        c, _ = build()
        bad = {**DADOS, "valor": "1" * 30}
        self.assertEqual(c.post("/v1/empresas/A/rascunhos", json={"dados": bad}, headers=H).status_code, 422)
        self.assertEqual(c.post("/v1/empresas/A/rascunhos", json={"dados": {**DADOS, "extra": 1}}, headers=H).status_code, 422)
        d = novo(c, dados={**DADOS, "tomador": {"documento": "000", "nome": "", "email": ""}})
        r = c.post(f"/v1/empresas/A/rascunhos/{d['id']}/revisao", json={"versao": 1}, headers=H)
        self.assertEqual(r.status_code, 422)

    def test_cross_company_generic_404(self):
        c, _ = build()
        d = novo(c)
        c.cookies.set("session", "tok-u2")
        for r in (c.get(f"/v1/empresas/A/rascunhos/{d['id']}"), c.get(f"/v1/empresas/B/rascunhos/{d['id']}"),
                  c.get("/v1/empresas/A/emissoes"), c.put(f"/v1/empresas/B/rascunhos/{d['id']}", json={"versao_esperada": 1, "dados": DADOS}, headers=H)):
            self.assertEqual(r.status_code, 404)
            self.assertEqual(r.json()["detail"]["mensagem"], "Conteúdo indisponível")

    def test_revocation_applies_immediately(self):
        c, deps = build()
        d = revisado(c)
        deps.members.revoke("u1", "A")
        self.assertEqual(c.get(f"/v1/empresas/A/rascunhos/{d['id']}").status_code, 404)
        self.assertEqual(emitir(c, d).status_code, 404)
        self.assertEqual(c.get("/v1/sessao").json()["empresas"], [])


class Review(unittest.TestCase):
    def test_stale_review_blocks_emission(self):
        c, deps = build()
        d = revisado(c)
        self.assertTrue(d["revisao"]["valida"])
        c.put(f"/v1/empresas/A/rascunhos/{d['id']}", json={"versao_esperada": 1, "dados": {**DADOS, "valor": "999.00"}}, headers=H)
        cur = c.get(f"/v1/empresas/A/rascunhos/{d['id']}").json()
        self.assertFalse(cur["revisao"]["valida"])
        r = emitir(c, {**d, "versao": 2})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(len(deps.repo.emissoes), 0)

    def test_not_released_423(self):
        c, _ = build()
        d = novo(c, dados={**DADOS, "operacao": "venda"})
        d = c.post(f"/v1/empresas/A/rascunhos/{d['id']}/revisao", json={"versao": 1}, headers=H).json()
        self.assertEqual(emitir(c, d).status_code, 423)

    def test_production_disabled(self):
        c, _ = build()
        self.assertEqual(emitir(c, revisado(c), ambiente="producao").status_code, 423)


class Imports(unittest.TestCase):
    CSV = ("id_origem;tomador_documento;tomador_nome;operacao;competencia;valor;descricao\n"
           "A1;529.982.247-25;Maria;locacao;11/2026;100,00;Administração nov\n"
           "A2;000;Inválido;locacao;11/2026;50,00;Administração nov\n").encode()

    def test_analyze_confirm_and_repeat(self):
        c, deps = build()
        a = c.post("/v1/empresas/A/importacoes/analisar", files={"arquivo": ("x.csv", self.CSV, "text/csv")}, headers=H).json()
        self.assertEqual(a["totais"]["valida"]["qtd"], 1)
        linhas = [{"linha": l["linha"], "sistema": l["sistema"], "id_origem": l["idOrigem"], "dados": l["dados"]} for l in a["linhas"]]
        # O navegador envia também a linha inválida: o servidor revalida e a ignora.
        r = c.post("/v1/empresas/A/importacoes/confirmar", json={"linhas": linhas}, headers=H).json()
        self.assertEqual(r, {"criados": 1, "ignorados": 1})
        again = c.post("/v1/empresas/A/importacoes/confirmar", json={"linhas": linhas}, headers=H).json()
        self.assertEqual(again["criados"], 0)
        self.assertIn("planilha|A1", c.get("/v1/empresas/A/importacoes/origens").json())
        self.assertEqual(len(deps.repo.rascunhos), 1)
        self.assertEqual(len(deps.repo.emissoes), 0)

    def test_rejects_bad_file(self):
        c, _ = build()
        r = c.post("/v1/empresas/A/importacoes/analisar", files={"arquivo": ("x.exe", b"MZ", "application/octet-stream")}, headers=H)
        self.assertEqual(r.status_code, 422)


class Emission(unittest.TestCase):
    def test_lost_confirmation_response_recovers_same_operation(self):
        """Resposta do POST de confirmação perdida: o cliente consulta e reutiliza a mesma chave; nunca 2 operações."""
        c, deps = build()
        d = revisado(c)
        first = emitir(c, d)  # servidor persistiu; suponha que a resposta nunca chegou ao navegador
        self.assertEqual(first.status_code, 202)
        found = c.get("/v1/empresas/A/emissoes", params={"rascunho_id": d["id"], "versao": 1}).json()
        self.assertEqual([e["id"] for e in found], [first.json()["id"]])
        retry = emitir(c, d)  # mesma chave estável
        self.assertEqual(retry.json()["id"], first.json()["id"])
        other_key = emitir(c, d, key="emissao:A:outra-chave")
        self.assertEqual(other_key.json()["id"], first.json()["id"])
        self.assertEqual(len(deps.repo.emissoes), 1)
        self.assertEqual(len(deps.repo.jobs), 1)

    def test_same_key_other_environment_conflicts(self):
        c, deps = build()
        deps.settings.production_enabled = True
        deps.releases.register(Release("A", "locacao", "producao", 1, "evidência", "esc"))
        d = revisado(c)
        emitir(c, d)
        self.assertEqual(emitir(c, d, ambiente="producao").status_code, 409)

    def test_unknown_result_only_lookup_and_document_authorization(self):
        c, deps = build()
        d = revisado(c)
        e = emitir(c, d).json()
        worker.run_once(deps.repo, FakeAdapter(submit=Outcome.UNKNOWN), now=0)
        self.assertEqual(c.get(f"/v1/empresas/A/emissoes/{e['id']}").json()["estado"], "resultado_desconhecido")
        self.assertEqual(c.get(f"/v1/empresas/A/emissoes/{e['id']}/documento").status_code, 404)
        new_key = emitir(c, d, key="emissao:A:tentativa-nova")
        self.assertEqual(new_key.status_code, 423)
        self.assertEqual(c.post(f"/v1/empresas/A/emissoes/{e['id']}/verificar", headers=H).json()["estado"], "resultado_desconhecido")
        ad = FakeAdapter(lookup=Outcome.ACCEPTED)
        worker.run_once(deps.repo, ad, now=1)
        self.assertEqual((ad.submits, ad.lookups), (0, 1))
        em = deps.repo.emissoes[e["id"]]
        ref, _ = deps.storage.put("A", "nfse", b"<NFSe/>")
        from dataclasses import replace
        deps.repo.save_emission(replace(em, documento_ref=ref))
        doc = c.get(f"/v1/empresas/A/emissoes/{e['id']}/documento")
        self.assertEqual((doc.status_code, doc.content), (200, b"<NFSe/>"))
        self.assertEqual(doc.headers["cache-control"], "private, no-store")
        c.cookies.set("session", "tok-u2")
        self.assertEqual(c.get(f"/v1/empresas/A/emissoes/{e['id']}/documento").status_code, 404)

    def test_requires_idempotency_key(self):
        c, _ = build()
        d = revisado(c)
        r = c.post(f"/v1/empresas/A/rascunhos/{d['id']}/emissao",
                   json={"revisao_id": d["revisao"]["id"], "versao": 1, "ambiente": "producao_restrita", "confirmacao_humana": True}, headers=H)
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main()
