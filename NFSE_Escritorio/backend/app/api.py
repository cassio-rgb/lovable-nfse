"""API interna do serviço fiscal (FastAPI) — contrato em docs/api-contract.md.

`create_app(deps)` recebe todas as dependências injetadas. Implementações em memória
(`durable = False`) só são aceitas com APP_ENV=test; em qualquer outro ambiente a
aplicação se recusa a iniciar. A inicialização real fica em `app/main.py`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol

from fastapi import FastAPI, File, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from . import emissions, imports, reviews
from .auth import AcessoNegado, CompanyDirectory, MembershipStore, Principal, principal_from_claims
from .config import ConfigError
from .domain.models import Ambiente, DadosRascunho, Emissao, Rascunho, parse_money
from .domain.transitions import ConflitoVersao
from .eligibility import OperacaoNaoLiberada, ReleaseRegistry
from .nfse.client import AdaptadorFiscalBloqueado
from .observability import event
from .repository import current_user_id

CSRF_HEADER = "x-requested-with"
CSRF_VALUE = "nfse-imoveis"
SESSION_COOKIE = "session"
MUTATING = {"POST", "PUT", "PATCH", "DELETE"}


class IdentityProvider(Protocol):
    def verify(self, token: str) -> dict: ...  # deve validar assinatura, iss, aud, exp
    def login_url(self, retorno: str) -> str: ...


@dataclass
class ApiSettings:
    app_env: str
    allowed_origins: tuple[str, ...]
    production_enabled: bool = False
    import_max_bytes: int = 5 * 1024 * 1024
    import_max_rows: int = 5000


@dataclass
class Deps:
    settings: ApiSettings
    repo: Any  # MemoryRepository (teste) ou pg.PostgresRepository
    members: MembershipStore
    companies: CompanyDirectory
    releases: ReleaseRegistry
    storage: Any
    identity: IdentityProvider | None
    extra: dict = field(default_factory=dict)


def assert_deployable(d: Deps) -> None:
    if d.identity is None:
        raise ConfigError("Verificador de identidade ausente: a API não inicia sem provedor real.")
    if d.settings.app_env != "test":
        volatile = [n for n in ("repo", "members", "companies", "releases", "storage")
                    if not getattr(getattr(d, n), "durable", False)]
        if volatile:
            raise ConfigError(f"Dependências não duráveis recusadas fora de teste: {', '.join(volatile)}")
    if not d.settings.allowed_origins:
        raise ConfigError("CORS/CSRF: nenhuma origem permitida configurada")


# ---------- Entrada validada ----------

class TomadorIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    documento: str = Field("", max_length=32)
    nome: str = Field("", max_length=200)
    email: str | None = Field(None, max_length=200)


class FiscalIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    catalogoId: str = Field("", max_length=80)
    servico: str = Field("", max_length=20)
    nbs: str = Field("", max_length=20)
    cst: str = Field("", max_length=20)
    cClassTrib: str = Field("", max_length=20)
    cIndOp: str = Field("", max_length=20)


class DadosIn(BaseModel):
    fiscal: FiscalIn | None = None
    model_config = ConfigDict(extra="forbid")
    tomador: TomadorIn
    operacao: str = Field("", max_length=32)
    competencia: str = Field("", max_length=7)
    valor: str = Field("", max_length=20)
    descricao: str = Field("", max_length=2000)
    imovel: str = Field("", max_length=500)

    def domain(self) -> DadosRascunho:
        return DadosRascunho(self.tomador.documento, self.tomador.nome, self.operacao, self.competencia,
                             self.valor, self.descricao, self.imovel, self.tomador.email or "",
                             self.fiscal.model_dump() if self.fiscal is not None else None)


class OrigemIn(BaseModel):
    tipo: str = Field("manual", pattern="^manual$")  # importação só pelo endpoint de importação


class CriarIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dados: DadosIn
    origem: OrigemIn = OrigemIn()


class AtualizarIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    versao_esperada: int = Field(ge=1)
    dados: DadosIn


class RevisaoIn(BaseModel):
    versao: int = Field(ge=1)


class EmissaoIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revisao_id: str = Field(max_length=64)
    versao: int = Field(ge=1)
    ambiente: Ambiente
    confirmacao_humana: bool


class LinhaIn(BaseModel):
    linha: int = Field(ge=2)
    sistema: str = Field("planilha", min_length=1, max_length=64)
    id_origem: str = Field(min_length=1, max_length=128)
    dados: DadosIn


class ImportarIn(BaseModel):
    linhas: list[LinhaIn] = Field(max_length=5000)


# ---------- Serialização no formato de src/lib/contracts.ts ----------

def ser_dados(d: DadosRascunho) -> dict:
    return {"tomador": {"documento": d.tomador_documento, "nome": d.tomador_nome, "email": d.tomador_email},
            "operacao": d.operacao, "competencia": d.competencia, "valor": d.valor,
            "descricao": d.descricao, "imovel": d.imovel, "fiscal": d.fiscal}


def ser_rascunho(t, r: Rascunho) -> dict:
    out = {"id": r.id, "empresaId": r.empresa_id, "versao": r.versao, "dados": ser_dados(r.dados),
           "origem": r.origem, "criadoEm": r.criado_em, "atualizadoEm": r.atualizado_em}
    v = t.latest_review(r.empresa_id, r.id)
    if v:
        out["revisao"] = {"id": v.id, "rascunhoId": r.id, "versao": v.versao, "hash": v.hash,
                          "em": v.em, "valida": reviews.is_valid_in(t, v)}
    if r.emissao_id:
        out["emissaoId"] = r.emissao_id
    return out


def ser_emissao(e: Emissao) -> dict:
    out = {"id": e.id, "empresaId": e.empresa_id, "rascunhoId": e.rascunho_id, "versao": e.versao,
           "ambiente": e.ambiente.value, "identidadeDps": e.identidade_dps, "snapshot": ser_dados(e.snapshot),
           "estado": e.estado.value, "simulacao": False, "criadoEm": e.criado_em, "atualizadoEm": e.atualizado_em}
    if e.resultado:
        out["retorno"] = {k: v for k, v in {"chave": e.resultado.official_key, "codigo": e.resultado.official_code,
                                            "mensagem": e.resultado.message}.items() if v}
    return out


def fmt_cnpj(c: str) -> str:
    d = "".join(ch for ch in c if ch.isdigit())
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}" if len(d) == 14 else c


def err(status: int, msg: str) -> HTTPException:
    return HTTPException(status, {"mensagem": msg})


def create_app(d: Deps) -> FastAPI:
    assert_deployable(d)
    s = d.settings
    app = FastAPI(title="NFS-e Imóveis — serviço fiscal", docs_url=None, redoc_url=None, openapi_url=None)
    repo, members = d.repo, d.members

    @app.middleware("http")
    async def guard(request: Request, call_next):
        origin = request.headers.get("origin")
        cors = {}
        if origin and origin in s.allowed_origins:
            cors = {"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Credentials": "true", "Vary": "Origin"}
        if request.method == "OPTIONS":
            if not cors:
                return Response(status_code=403)
            return Response(status_code=204, headers={**cors, "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
                                                      "Access-Control-Allow-Headers": "Authorization, Content-Type, Idempotency-Key, X-Requested-With",
                                                      "Access-Control-Max-Age": "600"})
        # CSRF: sessão em cookie exige origem permitida + cabeçalho customizado (força preflight).
        if request.method in MUTATING and (not cors or request.headers.get(CSRF_HEADER) != CSRF_VALUE):
            return JSONResponse({"detail": {"mensagem": "Origem não autorizada"}}, status_code=403, headers=cors)
        resp = await call_next(request)
        resp.headers.update(cors)
        resp.headers["Cache-Control"] = "private, no-store"
        return resp

    def principal(request: Request) -> Principal:
        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            raise err(401, "Sessão ausente")
        try:
            claims = d.identity.verify(token)  # type: ignore[union-attr]
        except Exception:
            raise err(401, "Sessão inválida")
        return principal_from_claims(claims)

    def allow(request: Request, empresa_id: str, perm: str) -> Principal:
        p = principal(request)
        members.require(p, empresa_id, perm)  # revalidado a cada requisição
        current_user_id.set(p.user_id)  # RLS no PostgreSQL
        return p

    @app.exception_handler(AcessoNegado)
    async def _denied(_r, _e):
        return JSONResponse({"detail": {"mensagem": "Conteúdo indisponível"}}, status_code=404)

    @app.exception_handler(ConflitoVersao)
    async def _conflict(_r, e):
        return JSONResponse({"detail": {"mensagem": str(e) or "Versão alterada"}}, status_code=409)

    @app.exception_handler(OperacaoNaoLiberada)
    @app.exception_handler(emissions.Bloqueado)
    @app.exception_handler(AdaptadorFiscalBloqueado)
    async def _locked(_r, e):
        return JSONResponse({"detail": {"mensagem": str(e)}}, status_code=423)

    @app.exception_handler(reviews.JaEnviado)
    async def _sent(_r, e):
        return JSONResponse({"detail": {"mensagem": str(e)}}, status_code=423)

    @app.exception_handler(reviews.Pendente)
    async def _pend(_r, e):
        return JSONResponse({"detail": {"mensagem": str(e)}}, status_code=422)

    # ----- sessão -----
    @app.get("/v1/auth/login")
    def login(retorno: str = Query(..., max_length=2000)):
        if not any(retorno == o or retorno.startswith(o + "/") for o in s.allowed_origins):
            raise err(400, "Retorno não permitido")
        return RedirectResponse(d.identity.login_url(retorno), status_code=302)  # type: ignore[union-attr]

    @app.post("/v1/auth/session", status_code=204)
    def criar_sessao(authorization: str | None = Header(None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise err(401, "Token de autenticação ausente")
        token = authorization.removeprefix("Bearer ").strip()
        try:
            d.identity.verify(token)  # type: ignore[union-attr]
        except Exception:
            raise err(401, "Token de autenticação inválido")
        resp = Response(status_code=204)
        resp.set_cookie(
            SESSION_COOKIE,
            token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
        )
        return resp

    @app.delete("/v1/auth/session", status_code=204)
    def encerrar_sessao():
        resp = Response(status_code=204)
        resp.delete_cookie(SESSION_COOKIE, path="/", secure=True, httponly=True, samesite="none")
        return resp

    @app.get("/v1/sessao")
    def sessao(request: Request):
        p = principal(request)
        current_user_id.set(p.user_id)  # RLS no PostgreSQL
        ids = members.empresas(p.user_id)
        empresas = [c for c in (d.companies.get(i) for i in ids) if c]
        return {"usuario": p.user_id, "papel": p.papel,
                "empresas": [{"id": c.id, "razaoSocial": c.razao_social, "cnpj": fmt_cnpj(c.cnpj), "municipio": c.municipio} for c in empresas],
                "liberacoes": [{"empresaId": r.empresa_id, "operacao": r.operacao, "ambiente": r.ambiente,
                                "versao": r.versao, "evidencia": r.evidencia} for c in empresas for r in d.releases.for_company(c.id)]}

    # ----- rascunhos -----
    base = "/v1/empresas/{empresa_id}"

    @app.get(base + "/rascunhos")
    def listar(empresa_id: str, request: Request):
        allow(request, empresa_id, "ler")
        with repo.tx() as t:
            return [ser_rascunho(t, r) for r in t.list_drafts(empresa_id)]

    @app.post(base + "/rascunhos", status_code=201)
    def criar(empresa_id: str, body: CriarIn, request: Request):
        allow(request, empresa_id, "editar")
        with repo.tx() as t:
            r = t.insert_draft(Rascunho(repo.new_id("rasc"), empresa_id, 1, body.dados.domain(), {"tipo": "manual"}))
            return ser_rascunho(t, r)

    @app.get(base + "/rascunhos/{rid}")
    def obter(empresa_id: str, rid: str, request: Request):
        allow(request, empresa_id, "ler")
        with repo.tx() as t:
            return ser_rascunho(t, t.get_draft(empresa_id, rid))

    @app.put(base + "/rascunhos/{rid}")
    def atualizar(empresa_id: str, rid: str, body: AtualizarIn, request: Request):
        allow(request, empresa_id, "editar")
        reviews.update_draft(repo, empresa_id, rid, body.versao_esperada, body.dados.domain())
        with repo.tx() as t:
            return ser_rascunho(t, t.get_draft(empresa_id, rid))

    @app.delete(base + "/rascunhos/{rid}", status_code=204)
    def descartar(empresa_id: str, rid: str, request: Request):
        allow(request, empresa_id, "editar")
        with repo.tx() as t:
            if t.get_draft(empresa_id, rid, lock=True).emissao_id:
                raise emissions.Bloqueado("Rascunho já enviado não pode ser descartado")
            t.delete_draft(empresa_id, rid)
        return Response(status_code=204)

    @app.post(base + "/rascunhos/{rid}/revisao")
    def revisar(empresa_id: str, rid: str, body: RevisaoIn, request: Request):
        p = allow(request, empresa_id, "editar")
        reviews.prepare(repo, p, empresa_id, rid, body.versao)
        with repo.tx() as t:
            return ser_rascunho(t, t.get_draft(empresa_id, rid))

    # ----- importação -----
    @app.get(base + "/importacoes/origens")
    def origens(empresa_id: str, request: Request):
        allow(request, empresa_id, "ler")
        with repo.tx() as t:
            return {f"{sis}|{ido}": c for (sis, ido), c in t.origins(empresa_id).items()}

    @app.post(base + "/importacoes/analisar")
    async def analisar(empresa_id: str, request: Request, arquivo: UploadFile = File(...)):
        allow(request, empresa_id, "editar")
        data = await arquivo.read(s.import_max_bytes + 1)
        try:
            rows = imports.read_rows(arquivo.filename or "", data, s.import_max_bytes)
            linhas = imports.preview(repo, empresa_id, rows, s.import_max_rows)
        except imports.ArquivoInvalido as e:
            raise err(422, str(e))
        t = imports.totals(linhas)
        return {"layout": imports.LAYOUT,
                "totais": {k: {"qtd": v["qtd"], "valor": str(v["valor"])} for k, v in t.items()},
                "linhas": [{"linha": l.linha, "sistema": l.sistema, "idOrigem": l.id_origem, "situacao": l.situacao,
                            "erros": l.erros, "dados": ser_dados(l.dados)} for l in linhas]}

    @app.post(base + "/importacoes/confirmar")
    def confirmar_importacao(empresa_id: str, body: ImportarIn, request: Request):
        allow(request, empresa_id, "editar")
        # Não confia na classificação do navegador: imports.confirm reclassifica cada linha no servidor.
        linhas = []
        for li in body.linhas:
            dd = li.dados.domain()
            try:
                valor = parse_money(dd.valor)
            except ValueError:
                valor = Decimal("0")
            linhas.append(imports.Linha(li.linha, li.sistema, li.id_origem, dd, "nao_classificada", [], valor))
        return imports.confirm(repo, empresa_id, linhas, {l.linha for l in linhas})

    # ----- emissões -----
    @app.post(base + "/rascunhos/{rid}/emissao", status_code=202)
    def emitir(empresa_id: str, rid: str, body: EmissaoIn, request: Request,
               idempotency_key: str = Header(..., min_length=8, max_length=200)):
        p = allow(request, empresa_id, "emitir")
        e = emissions.confirm(repo, members, d.releases, p, empresa_id, rid, body.revisao_id, body.versao, body.ambiente,
                              idempotency_key, body.confirmacao_humana, s.production_enabled)
        event("emissao_confirmada", e.id, empresa=empresa_id)
        return ser_emissao(e)

    @app.get(base + "/emissoes")
    def listar_emissoes(empresa_id: str, request: Request, rascunho_id: str | None = None, versao: int | None = None):
        allow(request, empresa_id, "ler")
        with repo.tx() as t:
            return [ser_emissao(e) for e in t.list_emissions(empresa_id, rascunho_id, versao)]

    @app.get(base + "/emissoes/{eid}")
    def obter_emissao(empresa_id: str, eid: str, request: Request):
        allow(request, empresa_id, "ler")
        with repo.tx() as t:
            return ser_emissao(t.get_emission(empresa_id, eid))

    @app.post(base + "/emissoes/{eid}/verificar")
    def verificar(empresa_id: str, eid: str, request: Request):
        allow(request, empresa_id, "ler")
        return ser_emissao(emissions.schedule_lookup(repo, empresa_id, eid))

    @app.get(base + "/emissoes/{eid}/documento")
    def documento(empresa_id: str, eid: str, request: Request):
        allow(request, empresa_id, "ler")
        with repo.tx() as t:
            e = t.get_emission(empresa_id, eid)
        if e.estado.value != "emitida" or not e.documento_ref:
            raise AcessoNegado()
        data = d.storage.get(empresa_id, e.documento_ref)
        return Response(data, media_type="application/xml",
                        headers={"Content-Disposition": f'attachment; filename="nfse-{e.id}.xml"'})

    return app
