"""Contexto de assinatura delegada (procuração/representação NFS-e) — fail-closed.

Separação obrigatória:
- emitente fiscal = empresa cliente (CNPJ do prestador na DPS; nunca substituído);
- signatário = escritório titular do certificado A1 (CNPJ do SAN ICP-Brasil);
- autorização = resultado de um `ProvedorAutorizacao` confiável, por ambiente, outorgante,
  outorgado e serviço. Recibo WEB (captura de tela/declaração do usuário), booleano ou
  configuração NUNCA produzem resultado autorizado.

Não existe provedor oficial implementado (contrato da API de representação não capturado);
`ProvedorAutorizacaoAusente` bloqueia sempre. O provedor sintético existe só para testes offline
(APP_ENV=test) e não há allowlist de delegados embutida.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Protocol

from ..domain.models import Ambiente
from .certificado import CertificadoA1

SERVICO_RECEITA_NFSE = "00233"  # código de serviço da Receita para procuração NFS-e (fonte: gov.br/nfse 31/10/2026)


class DelegacaoRecusada(PermissionError):
    pass


@dataclass(frozen=True)
class ReciboWeb:
    """Registro informativo fornecido pelo usuário (ex.: captura do Emissor WEB). Não autoriza nada."""
    outorgante_cnpj: str
    outorgado_cnpj: str
    recebido_em: date
    fonte: str = "declaracao_usuario_web"
    status: str = "informativo_nao_verificado_api"


@dataclass(frozen=True)
class ResultadoAutorizacao:
    outorgante_cnpj: str
    outorgado_cnpj: str
    servico: str
    ambiente: Ambiente
    status: str  # "autorizada" | "revogada" | "inexistente" | "expirada"
    consultado_em: datetime
    valido_ate: datetime | None
    provedor: str


class ProvedorAutorizacao(Protocol):
    nome: str
    somente_teste: bool

    def consultar(self, outorgante_cnpj: str, outorgado_cnpj: str, servico: str,
                  ambiente: Ambiente) -> ResultadoAutorizacao: ...


class ProvedorAutorizacaoAusente:
    nome = "ausente"
    somente_teste = False

    def consultar(self, *a, **k) -> ResultadoAutorizacao:
        raise DelegacaoRecusada("Provedor de autorização governamental não implementado (contrato oficial não capturado)")


@dataclass(frozen=True)
class ContextoAssinatura:
    emitente_cnpj: str
    signatario_cnpj: str
    cert_fingerprint: str
    ambiente: Ambiente
    delegado: bool
    autorizacao: ResultadoAutorizacao | None


MAX_IDADE_CONSULTA_S = 300


def contexto_assinatura(emitente_cnpj: str, cert: CertificadoA1, ambiente: Ambiente,
                        provedor: ProvedorAutorizacao | None, agora: datetime | None = None,
                        recibo_web: ReciboWeb | None = None) -> ContextoAssinatura:
    """Recibo WEB é aceito apenas para registro e ignorado na decisão."""
    agora = agora or datetime.now(timezone.utc)
    if cert.cnpj_titular is None:
        raise DelegacaoRecusada("Identidade do certificado não determinada (sem CNPJ ICP-Brasil)")
    if cert.cnpj_titular == emitente_cnpj:
        return ContextoAssinatura(emitente_cnpj, cert.cnpj_titular, cert.fingerprint(), ambiente, False, None)
    if provedor is None:
        raise DelegacaoRecusada("Assinatura delegada exige resultado de autorização confiável; recibo WEB não basta")
    if getattr(provedor, "somente_teste", True) and os.environ.get("APP_ENV") != "test":
        raise DelegacaoRecusada("Provedor sintético só é aceito em testes offline")
    r = provedor.consultar(emitente_cnpj, cert.cnpj_titular, SERVICO_RECEITA_NFSE, ambiente)
    if not isinstance(r, ResultadoAutorizacao):
        raise DelegacaoRecusada("Resultado de autorização inválido")
    if (r.outorgante_cnpj, r.outorgado_cnpj, r.servico, r.ambiente) != (
            emitente_cnpj, cert.cnpj_titular, SERVICO_RECEITA_NFSE, ambiente):
        raise DelegacaoRecusada("Autorização não corresponde a outorgante/outorgado/serviço/ambiente")
    if r.status != "autorizada":
        raise DelegacaoRecusada(f"Autorização não vigente ({r.status})")
    if r.valido_ate is not None and r.valido_ate <= agora:
        raise DelegacaoRecusada("Autorização expirada")
    if not (0 <= (agora - r.consultado_em).total_seconds() <= MAX_IDADE_CONSULTA_S):
        raise DelegacaoRecusada("Resultado de autorização desatualizado")
    return ContextoAssinatura(emitente_cnpj, cert.cnpj_titular, cert.fingerprint(), ambiente, True, r)
