"""Estados, valores monetários exatos e invariantes do domínio fiscal."""
from __future__ import annotations

from ..catalogos import canonical_catalogo

import hashlib
import json
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import Enum
from datetime import datetime, timezone


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_money(raw: str) -> Decimal:
    """Aceita "1234.56" ou "1.234,56". Rejeita >2 casas em vez de arredondar."""
    s = (raw or "").strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        value = Decimal(s)
        if not value.is_finite() or value <= 0:
            raise ValueError("Valor monetário inválido")
        cents = value.quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError("Valor monetário inválido") from exc
    if cents != value:
        raise ValueError("Informe no máximo duas casas decimais")
    return cents


def only_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def valid_cpf(raw: str) -> bool:
    d = only_digits(raw)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for n in (9, 10):
        s = sum(int(d[i]) * (n + 1 - i) for i in range(n))
        if (s * 10 % 11) % 10 != int(d[n]):
            return False
    return True


def valid_cnpj(raw: str) -> bool:
    d = only_digits(raw)
    if len(d) != 14 or len(set(d)) == 1:
        return False
    for n, w in ((12, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]), (13, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])):
        r = sum(int(d[i]) * w[i] for i in range(n)) % 11
        if (0 if r < 2 else 11 - r) != int(d[n]):
            return False
    return True


class Operacao(str, Enum):
    LOCACAO = "locacao"
    VENDA = "venda"
    ARRENDAMENTO = "arrendamento"
    ADMINISTRACAO = "administracao"


class Ambiente(str, Enum):
    PRODUCAO_RESTRITA = "producao_restrita"
    PRODUCAO = "producao"


class Estado(str, Enum):
    RASCUNHO = "rascunho"
    COM_PENDENCIAS = "com_pendencias"
    REVISADO = "revisado"
    NA_FILA = "na_fila"
    TRANSMITINDO = "transmitindo"
    RESULTADO_DESCONHECIDO = "resultado_desconhecido"
    EMITIDA = "emitida"
    REJEITADA = "rejeitada"
    ERRO_PRE_ENVIO = "erro_pre_envio"


class Outcome(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNKNOWN = "unknown"
    PRE_SEND_FAILURE = "pre_send_failure"


@dataclass(frozen=True)
class FiscalResult:
    outcome: Outcome
    correlation_id: str
    dps_id: str
    official_key: str | None = None
    official_code: str | None = None
    message: str | None = None
    artifact_ref: str | None = None


@dataclass
class DadosRascunho:
    tomador_documento: str
    tomador_nome: str
    operacao: str
    competencia: str  # AAAA-MM
    valor: str  # decimal canônico
    descricao: str
    imovel: str = ""
    tomador_email: str = ""
    fiscal: dict | None = None

    def canonical(self) -> str:
        return json.dumps(
            [only_digits(self.tomador_documento), self.tomador_nome.strip(), self.operacao, self.competencia,
             self.valor, self.descricao.strip(), self.imovel.strip()] +
            ([canonical_catalogo(self.fiscal)] if self.fiscal else []),
            ensure_ascii=False,
        )


def pendencias(d: DadosRascunho) -> dict[str, str]:
    p: dict[str, str] = {}
    doc = only_digits(d.tomador_documento)
    if re.search(r"[A-Za-z]", d.tomador_documento or ""):
        p["documento"] = "CPF/CNPJ com letras (CNPJ alfanumérico) ainda não é suportado."
    elif not doc:
        p["documento"] = "Informe o CPF ou CNPJ do tomador."
    elif not (valid_cpf(doc) if len(doc) == 11 else valid_cnpj(doc) if len(doc) == 14 else False):
        p["documento"] = "CPF ou CNPJ inválido."
    if not d.tomador_nome.strip():
        p["nome"] = "Informe o nome do tomador."
    if d.operacao not in {o.value for o in Operacao}:
        p["operacao"] = "Selecione o tipo de operação."
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", d.competencia or ""):
        p["competencia"] = "Informe a competência (mês/ano)."
    try:
        parse_money(d.valor)
    except ValueError as e:
        p["valor"] = str(e)
    if len(d.descricao.strip()) < 5:
        p["descricao"] = "Descreva o serviço (mínimo 5 caracteres)."
    return p


def content_hash(empresa_id: str, d: DadosRascunho) -> str:
    return hashlib.sha256(f"{empresa_id}|{d.canonical()}".encode()).hexdigest()


@dataclass
class Rascunho:
    id: str
    empresa_id: str
    versao: int
    dados: DadosRascunho
    origem: dict = field(default_factory=lambda: {"tipo": "manual"})
    emissao_id: str | None = None
    criado_em: str = field(default_factory=utcnow)
    atualizado_em: str = field(default_factory=utcnow)


@dataclass(frozen=True)
class Revisao:
    id: str
    empresa_id: str
    rascunho_id: str
    versao: int
    hash: str
    usuario_id: str
    em: str = field(default_factory=utcnow)


@dataclass
class Emissao:
    id: str
    empresa_id: str
    rascunho_id: str
    versao: int
    ambiente: Ambiente
    identidade_dps: str
    snapshot: DadosRascunho
    revisao_id: str
    chave_idempotente: str
    estado: Estado = Estado.NA_FILA
    tentativas: int = 0
    resultado: FiscalResult | None = None
    fingerprint: str = ""
    documento_ref: str | None = None
    criado_em: str = field(default_factory=utcnow)
    atualizado_em: str = field(default_factory=utcnow)
