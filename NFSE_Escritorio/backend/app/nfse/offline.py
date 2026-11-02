"""Preparação OFFLINE da DPS de uma emissão já confirmada.

Gera, valida (XSD do ambiente) e opcionalmente assina o XML a partir do snapshot imutável da
emissão e de parâmetros fiscais explícitos. Não altera estado, não transmite e não é NFS-e:
o artefato é sempre `transmissivel=False` enquanto contrato/perfil oficial não estiverem confirmados.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime

from ..domain.models import Emissao, Estado
from .dps import NS, PERFIS, EntradaFiscalInvalida, build_dps, entrada_da_emissao
from .signing import Assinador

AVISO = "Artefato offline de validação — não é NFS-e emitida e não foi transmitido."


@dataclass(frozen=True)
class ArtefatoOffline:
    emissao_id: str
    id_dps: str
    perfil_esquema: str
    sha256: str
    assinado: bool
    perfil_cripto: str | None
    perfil_cripto_status: str | None
    transmissivel: bool
    aviso: str
    xml: bytes

    def __repr__(self) -> str:  # sem XML integral em logs
        return f"ArtefatoOffline({self.emissao_id}, {self.id_dps[:10]}…, sha256={self.sha256[:12]}, assinado={self.assinado})"


def preparar(emissao: Emissao, empresa_cnpj: str, parametros_port, d_compet: date | None,
             dh_emi: datetime, assinador: Assinador | None = None,
             contexto=None) -> ArtefatoOffline:
    """`contexto` (delegacao.ContextoAssinatura) é obrigatório para assinatura delegada: o CNPJ do
    prestador na DPS continua sendo `empresa_cnpj` (cliente); o escritório só assina."""
    if contexto is not None:
        if assinador is None:
            raise EntradaFiscalInvalida(["Contexto de assinatura sem assinador"])
        if contexto.emitente_cnpj != empresa_cnpj or contexto.ambiente != emissao.ambiente:
            raise EntradaFiscalInvalida(["Contexto de assinatura de outra empresa/ambiente"])
        if contexto.cert_fingerprint != assinador.cert_fingerprint():
            raise EntradaFiscalInvalida(["Certificado do assinador difere do verificado no contexto"])
        if contexto.delegado and contexto.autorizacao is None:
            raise EntradaFiscalInvalida(["Assinatura delegada sem autorização verificada"])
    elif assinador is not None:
        from .certificado import _cnpjs
        titular = set(_cnpjs(assinador.certificado))
        if titular and titular != {empresa_cnpj}:
            raise EntradaFiscalInvalida(["Certificado de terceiro exige contexto de delegação verificado"])
    if emissao.estado in (Estado.EMITIDA, Estado.REJEITADA):
        raise EntradaFiscalInvalida(["Emissão já finalizada; artefato offline não se aplica"])
    if d_compet is None:
        raise EntradaFiscalInvalida(["dCompet completa (dia) não informada; o mês da competência não implica o dia"])
    params = parametros_port.parametros(emissao.empresa_id, emissao.snapshot.operacao, emissao.ambiente)
    if params is None:
        raise EntradaFiscalInvalida(["Parâmetros fiscais da empresa/operação não cadastrados"])
    xml = build_dps(entrada_da_emissao(emissao, empresa_cnpj, params, d_compet, dh_emi))
    from lxml import etree
    from . import secure_xml
    id_dps = secure_xml.parse_untrusted(xml).find(f"{{{NS}}}infDPS").get("Id")
    if assinador is not None:
        xml = assinador.assinar(xml)
    return ArtefatoOffline(
        emissao.id, id_dps, PERFIS[emissao.ambiente].nome, hashlib.sha256(xml).hexdigest(), assinador is not None,
        assinador.perfil.id if assinador else None, assinador.perfil.status if assinador else None,
        transmissivel=False, aviso=AVISO, xml=xml,
    )
