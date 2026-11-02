"""Entrada fiscal tipada e construção determinística da DPS (leiaute v1.01).

Ordem de elementos segue `TCInfDPS` dos XSD vendorizados. Nada é inferido da descrição do
rascunho: regime do emitente, códigos de tributação, município e data completa de competência
precisam ser informados explicitamente em `ParametrosFiscais`.

Escopo: somente DPS de emissão normal (sem substituição/cancelamento, sem IBS/CBS, sem
intermediário). Regras de negócio de tributação são validadas pela Receita/município, não aqui.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

from lxml import etree

from ..domain.models import Ambiente, parse_money, valid_cnpj, valid_cpf
from . import secure_xml

NS = "http://www.sped.fazenda.gov.br/nfse"
VERSAO_LEIAUTE = "1.01"


@dataclass(frozen=True)
class PerfilEsquema:
    nome: str
    ambiente: Ambiente
    tp_amb: str
    exige_fin_nfse: bool


PERFIS = {
    Ambiente.PRODUCAO: PerfilEsquema("producao_v1_01_20260209", Ambiente.PRODUCAO, "1", False),
    Ambiente.PRODUCAO_RESTRITA: PerfilEsquema("producao_restrita_20261020", Ambiente.PRODUCAO_RESTRITA, "2", True),
}


class EntradaFiscalInvalida(ValueError):
    def __init__(self, erros: list[str]) -> None:
        super().__init__("; ".join(erros))
        self.erros = erros


@dataclass(frozen=True)
class Prestador:
    cnpj: str  # 14 dígitos numéricos (CNPJ alfanumérico ainda não suportado pelo app)
    op_simp_nac: str  # TSOpSimpNac: 1, 2, 3
    reg_esp_trib: str  # TSRegEspTrib: 0..6, 9
    reg_ap_trib_sn: str | None = None
    inscricao_municipal: str | None = None


@dataclass(frozen=True)
class Tomador:
    documento: str  # CPF (11) ou CNPJ (14), somente dígitos
    nome: str


@dataclass(frozen=True)
class Servico:
    c_loc_prestacao: str  # IBGE 7
    c_trib_nac: str  # 6 dígitos
    descricao: str
    c_trib_mun: str | None = None
    c_nbs: str | None = None


@dataclass(frozen=True)
class Tributacao:
    trib_issqn: str  # 1..4
    tp_ret_issqn: str  # 1..3
    ind_tot_trib: str | None = None  # "0" (não informar valor aproximado)
    p_tot_trib_sn: str | None = None  # percentual Simples Nacional
    p_aliq: str | None = None


@dataclass(frozen=True)
class EntradaDPS:
    ambiente: Ambiente
    dh_emi: datetime
    ver_aplic: str
    serie: str
    n_dps: int
    d_compet: date
    tp_emit: str  # 1 prestador, 2 tomador, 3 intermediário
    c_loc_emi: str
    prestador: Prestador
    tomador: Tomador
    servico: Servico
    valor: Decimal
    tributacao: Tributacao
    fin_nfse: str | None = None  # exigido apenas pelo perfil de produção restrita (v20261020)
    extras: dict = field(default_factory=dict)


_D = lambda n: re.compile(rf"[0-9]{{{n}}}")


TIPO_INSCRICAO_CPF = "1"
TIPO_INSCRICAO_CNPJ = "2"


def id_dps(c_loc_emi: str, cnpj: str, serie: str, n_dps: int) -> str:
    """DPS + município(7) + tipo de inscrição federal(1) + inscrição(14) + série(5) + número(15).

    Anexo I (produção restrita 2026-10-20), aba "RN DPS_NFS-e 1.01", linha 151, regra E0004:
    tipo 1 = CPF, tipo 2 = CNPJ. O app só emite como prestador CNPJ, portanto sempre tipo 2."""
    return f"DPS{c_loc_emi}{TIPO_INSCRICAO_CNPJ}{cnpj}{int(serie):05d}{n_dps:015d}"


def _fmt_dh(dt: datetime) -> str:
    off = dt.utcoffset()
    if off is None:
        raise EntradaFiscalInvalida(["dhEmi precisa de fuso horário explícito"])
    if off.total_seconds() % 3600:
        raise EntradaFiscalInvalida(["dhEmi: fuso deve ser hora cheia"])
    h = int(off / timedelta(hours=1))
    return dt.replace(microsecond=0, tzinfo=None).isoformat() + f"{'-' if h < 0 else '+'}{abs(h):02d}:00"


def _money(v: Decimal) -> str:
    q = v.quantize(Decimal("0.01"))
    if q != v or v <= 0 or q >= Decimal("1e15"):
        raise EntradaFiscalInvalida(["valor inválido"])
    return f"{q:.2f}"


def validar_entrada(e: EntradaDPS, perfil: PerfilEsquema) -> list[str]:
    er: list[str] = []
    if e.ambiente != perfil.ambiente:
        er.append("ambiente da entrada difere do perfil de esquema")
    if not isinstance(e.d_compet, date) or isinstance(e.d_compet, datetime):
        er.append("dCompet deve ser data completa (AAAA-MM-DD)")
    if not _D(7).fullmatch(e.c_loc_emi):
        er.append("cLocEmi deve ter 7 dígitos IBGE")
    if not _D(7).fullmatch(e.servico.c_loc_prestacao):
        er.append("cLocPrestacao deve ter 7 dígitos IBGE")
    if not _D(14).fullmatch(e.prestador.cnpj):
        er.append("CNPJ do prestador: somente 14 dígitos numéricos são suportados (alfanumérico não suportado)")
    elif not valid_cnpj(e.prestador.cnpj):
        er.append("CNPJ do prestador inválido")
    d = e.tomador.documento
    if not ((len(d) == 11 and d.isdigit() and valid_cpf(d)) or (len(d) == 14 and d.isdigit() and valid_cnpj(d))):
        er.append("documento do tomador inválido ou não numérico")
    if not e.tomador.nome.strip():
        er.append("nome do tomador obrigatório")
    if not re.fullmatch(r"[0-9]{1,5}", e.serie or "") or int(e.serie) == 0:
        er.append("série inválida")
    if not (1 <= e.n_dps < 10**15):
        er.append("nDPS fora do intervalo")
    if e.tp_emit not in {"1", "2", "3"}:
        er.append("tpEmit não informado/ inválido")
    if e.prestador.op_simp_nac not in {"1", "2", "3"}:
        er.append("regime (opSimpNac) do emitente não informado")
    if e.prestador.reg_esp_trib not in {"0", "1", "2", "3", "4", "5", "6", "9"}:
        er.append("regEspTrib não informado")
    if not _D(6).fullmatch(e.servico.c_trib_nac):
        er.append("cTribNac (6 dígitos) obrigatório")
    if not e.servico.descricao.strip():
        er.append("descrição do serviço obrigatória")
    if e.tributacao.trib_issqn not in {"1", "2", "3", "4"}:
        er.append("tribISSQN não informado")
    if e.tributacao.tp_ret_issqn not in {"1", "2", "3"}:
        er.append("tpRetISSQN não informado")
    if (e.tributacao.ind_tot_trib is None) == (e.tributacao.p_tot_trib_sn is None):
        er.append("informe exatamente um entre indTotTrib e pTotTribSN")
    if perfil.exige_fin_nfse and e.fin_nfse is None:
        er.append("finNFSe obrigatório no perfil de produção restrita")
    if not perfil.exige_fin_nfse and e.fin_nfse is not None:
        er.append("finNFSe não existe no perfil de produção vigente")
    try:
        _money(e.valor)
    except EntradaFiscalInvalida as x:
        er += x.erros
    return er


def _sub(parent, tag, text=None):
    el = etree.SubElement(parent, f"{{{NS}}}{tag}")
    if text is not None:
        el.text = text
    return el


def build_dps(e: EntradaDPS) -> bytes:
    """Gera XML não assinado, determinístico, e valida contra o XSD do perfil do ambiente."""
    perfil = PERFIS[e.ambiente]
    er = validar_entrada(e, perfil)
    if er:
        raise EntradaFiscalInvalida(er)
    root = etree.Element(f"{{{NS}}}DPS", nsmap={None: NS})
    root.set("versao", VERSAO_LEIAUTE)
    inf = _sub(root, "infDPS")
    inf.set("Id", id_dps(e.c_loc_emi, e.prestador.cnpj, e.serie, e.n_dps))
    _sub(inf, "tpAmb", perfil.tp_amb)
    _sub(inf, "dhEmi", _fmt_dh(e.dh_emi))
    _sub(inf, "verAplic", e.ver_aplic)
    _sub(inf, "serie", e.serie)
    _sub(inf, "nDPS", str(e.n_dps))
    _sub(inf, "dCompet", e.d_compet.isoformat())
    _sub(inf, "tpEmit", e.tp_emit)
    if perfil.exige_fin_nfse:
        _sub(inf, "finNFSe", e.fin_nfse)
    _sub(inf, "cLocEmi", e.c_loc_emi)
    pr = _sub(inf, "prest")
    _sub(pr, "CNPJ", e.prestador.cnpj)
    if e.prestador.inscricao_municipal:
        _sub(pr, "IM", e.prestador.inscricao_municipal)
    rt = _sub(pr, "regTrib")
    _sub(rt, "opSimpNac", e.prestador.op_simp_nac)
    if e.prestador.reg_ap_trib_sn:
        _sub(rt, "regApTribSN", e.prestador.reg_ap_trib_sn)
    _sub(rt, "regEspTrib", e.prestador.reg_esp_trib)
    to = _sub(inf, "toma")
    _sub(to, "CPF" if len(e.tomador.documento) == 11 else "CNPJ", e.tomador.documento)
    _sub(to, "xNome", e.tomador.nome.strip())
    sv = _sub(inf, "serv")
    _sub(_sub(sv, "locPrest"), "cLocPrestacao", e.servico.c_loc_prestacao)
    cs = _sub(sv, "cServ")
    _sub(cs, "cTribNac", e.servico.c_trib_nac)
    if e.servico.c_trib_mun:
        _sub(cs, "cTribMun", e.servico.c_trib_mun)
    if e.servico.c_nbs:
        _sub(cs, "cNBS", e.servico.c_nbs)
    _sub(cs, "xDescServ", e.servico.descricao.strip())
    va = _sub(inf, "valores")
    _sub(_sub(va, "vServPrest"), "vServ", _money(e.valor))
    tr = _sub(va, "trib")
    tm = _sub(tr, "tribMun")
    _sub(tm, "tribISSQN", e.tributacao.trib_issqn)
    _sub(tm, "tpRetISSQN", e.tributacao.tp_ret_issqn)
    if e.tributacao.p_aliq:
        _sub(tm, "pAliq", e.tributacao.p_aliq)
    tt = _sub(tr, "totTrib")
    if e.tributacao.ind_tot_trib is not None:
        _sub(tt, "indTotTrib", e.tributacao.ind_tot_trib)
    else:
        _sub(tt, "pTotTribSN", e.tributacao.p_tot_trib_sn)
    erros = secure_xml.validate(perfil.nome, root)
    if erros:
        raise EntradaFiscalInvalida(["XSD: " + m for m in erros])
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


def validar_xml(ambiente: Ambiente, data: bytes) -> list[str]:
    """Valida bytes não confiáveis (parse seguro + XSD do perfil + coerência tpAmb/Id)."""
    perfil = PERFIS[ambiente]
    root = secure_xml.parse_untrusted(data)
    erros = secure_xml.validate(perfil.nome, root)
    if erros:
        return erros
    return coerencia(root, ambiente)


def coerencia(root, ambiente: Ambiente) -> list[str]:
    """Regras além do XSD: tpAmb do ambiente (E0006) e Id = concatenação dos campos (E0004)."""
    perfil = PERFIS[ambiente]
    inf = root.find(f"{{{NS}}}infDPS")
    if inf is None:
        return ["infDPS ausente"]
    if inf.findtext(f"{{{NS}}}tpAmb") != perfil.tp_amb:
        return ["tpAmb incompatível com o ambiente"]
    exp = id_dps(inf.findtext(f"{{{NS}}}cLocEmi"), inf.findtext(f"{{{NS}}}prest/{{{NS}}}CNPJ") or "",
                 inf.findtext(f"{{{NS}}}serie"), int(inf.findtext(f"{{{NS}}}nDPS")))
    if inf.get("Id") != exp:
        return ["Id da DPS não corresponde a cLocEmi/CNPJ/série/número"]
    return []


@dataclass(frozen=True)
class ParametrosFiscais:
    """Configuração fiscal explícita por empresa/operação, cadastrada por responsável. Nunca inferida."""
    c_loc_emi: str
    serie: str
    tp_emit: str
    prestador: Prestador
    c_loc_prestacao: str
    c_trib_nac: str
    tributacao: Tributacao
    ver_aplic: str
    c_trib_mun: str | None = None
    c_nbs: str | None = None
    fin_nfse: str | None = None


def entrada_da_emissao(emissao, empresa_cnpj: str, params: ParametrosFiscais, d_compet: date,
                       dh_emi: datetime) -> EntradaDPS:
    """Monta a entrada a partir do snapshot imutável e confere coerência (identidade/ambiente/CNPJ/valor)."""
    from ..repository import numero_reservado

    snap = emissao.snapshot
    er: list[str] = []
    if params.prestador.cnpj != empresa_cnpj:
        er.append("CNPJ do prestador difere do CNPJ da empresa da emissão")
    if d_compet.strftime("%Y-%m") != snap.competencia:
        er.append("dCompet não pertence à competência revisada")
    if any(c.isalpha() for c in snap.tomador_documento):
        er.append("documento do tomador alfanumérico não suportado")
    if er:
        raise EntradaFiscalInvalida(er)
    return EntradaDPS(
        ambiente=emissao.ambiente, dh_emi=dh_emi, ver_aplic=params.ver_aplic, serie=params.serie,
        n_dps=numero_reservado(emissao.identidade_dps, emissao.empresa_id, emissao.ambiente.value), d_compet=d_compet, tp_emit=params.tp_emit,
        c_loc_emi=params.c_loc_emi, prestador=params.prestador,
        tomador=Tomador("".join(ch for ch in snap.tomador_documento if ch.isdigit()), snap.tomador_nome),
        servico=Servico(params.c_loc_prestacao, params.c_trib_nac, snap.descricao, params.c_trib_mun, params.c_nbs),
        valor=parse_money(snap.valor), tributacao=params.tributacao, fin_nfse=params.fin_nfse,
    )
