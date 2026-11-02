"""Adaptador da API Nacional NFS-e — transporte preparado, transmissão BLOQUEADA.

Confirmado no manual de contribuintes v1.2 (out/2025): POST /nfse, GET /nfse/{chaveAcesso},
GET /dps/{id}, HEAD /dps/{id}. NÃO verificado: envelope HTTP (campos JSON, compactação/base64),
códigos de resposta e perfil criptográfico vigente — o OpenAPI oficial respondeu 403/503 em
2026-10-31. Por isso `submit`/`lookup` falham explicitamente; nenhum simulador vira emissão.
"""
from __future__ import annotations

import re
import ssl
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urlsplit

from ..domain.models import Ambiente, Emissao, FiscalResult

MOTIVO_BLOQUEIO = (
    "Adaptador fiscal oficial bloqueado: contrato HTTP (envelope de requisição/resposta) e perfil "
    "criptográfico vigentes não verificados — OpenAPI oficial indisponível (403/503 em 2026-10-31); "
    "faltam também certificado autorizado e smoke em produção restrita."
)


class AdaptadorFiscalBloqueado(RuntimeError):
    def __init__(self, motivo: str = MOTIVO_BLOQUEIO) -> None:
        super().__init__(motivo)


class UrlRecusada(ValueError):
    pass


@dataclass(frozen=True)
class Destino:
    host: str
    base: str  # derivado dos links oficiais de documentação; confirmar no spike
    base_verificada: bool = False


DESTINOS = {
    Ambiente.PRODUCAO_RESTRITA: Destino("sefin.producaorestrita.nfse.gov.br", "/API/SefinNacional"),
    Ambiente.PRODUCAO: Destino("sefin.nfse.gov.br", "/SefinNacional"),
}

_ID_DPS = re.compile(r"DPS[0-9]{42}")
_CHAVE = re.compile(r"[0-9]{50}")


def caminhos_permitidos(d: Destino) -> list[tuple[str, re.Pattern]]:
    b = re.escape(d.base)
    return [("POST", re.compile(rf"{b}/nfse")), ("GET", re.compile(rf"{b}/nfse/[0-9]{{50}}")),
            ("GET", re.compile(rf"{b}/dps/DPS[0-9]{{42}}")), ("HEAD", re.compile(rf"{b}/dps/DPS[0-9]{{42}}"))]


def validar_url(method: str, url: str, destino: Destino) -> str:
    """Allowlist exata por URL analisada: https, host exato, porta 443, caminho exato, sem userinfo/query."""
    if not isinstance(url, str) or len(url) > 300 or any(c in url for c in "%\\@ \t\r\n#?") or ".." in url:
        raise UrlRecusada("URL com caracteres não permitidos")
    s = urlsplit(url)
    if s.scheme != "https" or not url.startswith("https://"):
        raise UrlRecusada("Somente https")
    if s.username or s.password or s.query or s.fragment:
        raise UrlRecusada("Componentes não permitidos")
    if s.port not in (None, 443) or s.netloc not in (destino.host, f"{destino.host}:443"):
        raise UrlRecusada("Host fora da allowlist")
    if (s.hostname or "") != destino.host:
        raise UrlRecusada("Host fora da allowlist")
    if not any(m == method and rx.fullmatch(s.path) for m, rx in caminhos_permitidos(destino)):
        raise UrlRecusada("Caminho/método fora da allowlist")
    return url


class MaterialMtls(Protocol):
    """Fornecido pelo cofre (não implementado). Nunca serializa a chave."""
    def contexto_ssl(self) -> ssl.SSLContext: ...


def contexto_tls_base() -> ssl.SSLContext:
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


@dataclass(frozen=True)
class ConfigTransporte:
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    verificar_tls: bool = True
    seguir_redirecionamento: bool = False
    tentativas_post: int = 1  # nunca repetir POST automaticamente

    def __post_init__(self) -> None:
        if not self.verificar_tls:
            raise ValueError("Verificação TLS não pode ser desligada")
        if self.seguir_redirecionamento:
            raise ValueError("Redirecionamentos são proibidos")
        if self.tentativas_post != 1:
            raise ValueError("POST fiscal não pode ser repetido automaticamente")
        if not (0 < self.connect_timeout <= 30 and 0 < self.read_timeout <= 120):
            raise ValueError("Timeouts inválidos")


@dataclass(frozen=True)
class RequisicaoPreparada:
    method: str
    url: str
    timeout: tuple[float, float]
    allow_redirects: bool
    contrato_corpo_verificado: bool
    corpo: bytes = field(repr=False, default=b"")


class NationalNfseClient:
    def __init__(self, ambiente: Ambiente, transporte: ConfigTransporte | None = None,
                 mtls: MaterialMtls | None = None, destino: Destino | None = None) -> None:
        self.ambiente = ambiente
        self.destino = destino or DESTINOS[ambiente]
        if self.destino != DESTINOS[ambiente]:
            raise UrlRecusada("Destino não corresponde ao ambiente/allowlist")
        self.transporte = transporte or ConfigTransporte()
        self.mtls = mtls

    def _url(self, method: str, path: str) -> str:
        return validar_url(method, f"https://{self.destino.host}{self.destino.base}{path}", self.destino)

    def preparar_envio(self, dps_assinada: bytes) -> RequisicaoPreparada:
        return RequisicaoPreparada("POST", self._url("POST", "/nfse"),
                                   (self.transporte.connect_timeout, self.transporte.read_timeout), False,
                                   contrato_corpo_verificado=False, corpo=dps_assinada)

    def preparar_consulta_dps(self, id_dps: str, head: bool = False) -> RequisicaoPreparada:
        if not _ID_DPS.fullmatch(id_dps):
            raise UrlRecusada("Id DPS inválido")
        m = "HEAD" if head else "GET"
        return RequisicaoPreparada(m, self._url(m, f"/dps/{id_dps}"),
                                   (self.transporte.connect_timeout, self.transporte.read_timeout), False, False)

    def preparar_consulta_nfse(self, chave: str) -> RequisicaoPreparada:
        if not _CHAVE.fullmatch(chave):
            raise UrlRecusada("Chave de acesso inválida")
        return RequisicaoPreparada("GET", self._url("GET", f"/nfse/{chave}"),
                                   (self.transporte.connect_timeout, self.transporte.read_timeout), False, False)

    def submit(self, emissao: Emissao) -> FiscalResult:
        raise AdaptadorFiscalBloqueado()

    def lookup(self, emissao: Emissao) -> FiscalResult:
        raise AdaptadorFiscalBloqueado()
