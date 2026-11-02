"""Carregamento de certificado A1 (PKCS#12 .pfx/.p12) — somente verificações ESTRUTURAIS locais.

Os bytes e a senha chegam por uma fronteira injetada (arquivo local do próprio usuário ou cofre);
este módulo não lê variáveis de ambiente, não acessa rede e não grava nada.

Status separados (nunca marcados como validados offline):
- estrutura local (chave↔certificado, RSA, X.509 v3, validade) — verificada aqui;
- cadeia ICP-Brasil e revogação (LCR/OCSP) — NÃO verificadas;
- autorização governamental (procuração/representação) — NÃO verificada (ver delegacao.py).

Identidade: o CNPJ só é extraído do SAN otherName OID 2.16.76.1.3.3 (DOC-ICP-04 v8.3, itens 7.1.2.2
e Anexo I: "nas 14 posições o número do CNPJ da pessoa jurídica titular"; OCTET STRING ou
PRINTABLE STRING; preenchido com zeros quando indisponível). CN, nome de arquivo e demais campos
nunca são usados como identidade.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12

OID_CNPJ = "2.16.76.1.3.3"
FONTE_OID = ("DOC-ICP-04 v8.3 (Resolução CG ICP-Brasil 179/2020 compilada), itens 7.1.2.2 e Anexo I; "
             "PDF gov.br/iti sha256 0603dbb47ea9f1928a5e6f72168a2f6dfe1ad2796b394aa6ad6ac92282a9c9a8, consultado 2026-11-02")
MAX_PFX = 64 * 1024
MIN_RSA = 2048
NAO_VERIFICADO = "nao_verificado"


class CertificadoInvalido(ValueError):
    """Mensagem sempre genérica e sanitizada (sem caminho, senha, serial, SAN ou exceção interna)."""


class SenhaA1:
    """Recipiente da senha: não aparece em repr/str e não é serializável."""
    __slots__ = ("_v",)

    def __init__(self, valor: bytes | str) -> None:
        self._v = valor.encode() if isinstance(valor, str) else bytes(valor)

    def __repr__(self) -> str:
        return "SenhaA1(***)"

    __str__ = __repr__

    def __reduce__(self):
        raise TypeError("SenhaA1 não é serializável")

    def _bytes(self) -> bytes:
        return self._v


def _ler_tlv(buf: bytes, i: int) -> tuple[int, bytes, int]:
    """TLV DER com comprimento curto ou longo de no máx. 2 octetos; limites estritos."""
    if i + 2 > len(buf):
        raise CertificadoInvalido("SAN malformado")
    tag, ln = buf[i], buf[i + 1]
    j = i + 2
    if ln & 0x80:
        n = ln & 0x7F
        if n == 0 or n > 2 or j + n > len(buf):
            raise CertificadoInvalido("SAN malformado")
        ln = int.from_bytes(buf[j:j + n], "big")
        if ln < 0x80 or (n == 2 and ln < 0x100):  # DER: forma mínima
            raise CertificadoInvalido("SAN malformado")
        j += n
    if j + ln > len(buf):
        raise CertificadoInvalido("SAN malformado")
    return tag, buf[j:j + ln], j + ln


def cnpj_de_othername(valor: bytes) -> str | None:
    """Decodifica o valor de otherName 2.16.76.1.3.3. Retorna None se todo zero (indisponível)."""
    if len(valor) > 64:
        raise CertificadoInvalido("SAN malformado")
    tag, conteudo, fim = _ler_tlv(valor, 0)
    if tag == 0xA0:  # alguns codificadores mantêm o [0] EXPLICIT
        if fim != len(valor):
            raise CertificadoInvalido("SAN malformado")
        interno = conteudo
        tag, conteudo, fim = _ler_tlv(interno, 0)
        if fim != len(interno):
            raise CertificadoInvalido("SAN malformado")
    elif fim != len(valor):
        raise CertificadoInvalido("SAN malformado")
    if tag not in (0x04, 0x13):  # OCTET STRING | PrintableString
        raise CertificadoInvalido("SAN com tipo não admitido")
    if len(conteudo) != 14 or not all(0x30 <= b <= 0x39 for b in conteudo):
        raise CertificadoInvalido("CNPJ do certificado fora do formato de 14 dígitos")
    s = conteudo.decode("ascii")
    return None if s == "0" * 14 else s


def _cnpjs(cert: x509.Certificate) -> list[str]:
    try:
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    except x509.ExtensionNotFound:
        return []
    out = []
    for on in san.get_values_for_type(x509.OtherName):
        if on.type_id.dotted_string == OID_CNPJ:
            v = cnpj_de_othername(on.value)
            if v:
                out.append(v)
    return out


@dataclass(frozen=True)
class CertificadoA1:
    chave: rsa.RSAPrivateKey = field(repr=False)
    certificado: x509.Certificate = field(repr=False)
    cnpj_titular: str | None  # None ⇒ identidade não determinada ⇒ NÃO PRONTO
    nao_antes: datetime
    nao_depois: datetime
    bits: int
    estrutura_local: str = "ok"
    cadeia_icp: str = NAO_VERIFICADO
    revogacao: str = NAO_VERIFICADO
    autorizacao_governo: str = NAO_VERIFICADO

    def __repr__(self) -> str:
        return f"CertificadoA1(fp={self.fingerprint()[:12]}…, cnpj={'definido' if self.cnpj_titular else 'ausente'})"

    def __reduce__(self):
        raise TypeError("CertificadoA1 não é serializável")

    def fingerprint(self) -> str:
        return self.certificado.fingerprint(hashes.SHA256()).hex()


def carregar_a1(dados: bytes, senha: SenhaA1, agora: datetime | None = None) -> CertificadoA1:
    if not isinstance(senha, SenhaA1):
        raise TypeError("senha deve ser SenhaA1")
    if not isinstance(dados, (bytes, bytearray)) or not dados or len(dados) > MAX_PFX:
        raise CertificadoInvalido("Arquivo PKCS#12 ausente ou com tamanho fora do limite")
    agora = agora or datetime.now(timezone.utc)
    try:
        chave, cert, extras = pkcs12.load_key_and_certificates(bytes(dados), senha._bytes())
    except Exception:  # noqa: BLE001 — não propagar detalhe interno
        raise CertificadoInvalido("Não foi possível abrir o PKCS#12 (senha incorreta ou arquivo inválido)") from None
    if chave is None:
        raise CertificadoInvalido("PKCS#12 sem chave privada")
    if cert is None:
        raise CertificadoInvalido("PKCS#12 sem certificado do titular")
    if not isinstance(chave, rsa.RSAPrivateKey):
        raise CertificadoInvalido("Tipo de chave não suportado (somente RSA)")
    if chave.key_size < MIN_RSA:
        raise CertificadoInvalido("Chave RSA abaixo de 2048 bits")
    pub = chave.public_key().public_numbers()
    if not isinstance(cert.public_key(), rsa.RSAPublicKey) or cert.public_key().public_numbers() != pub:
        raise CertificadoInvalido("Chave privada não corresponde ao certificado")
    for c in extras or []:
        k = c.public_key()
        if isinstance(k, rsa.RSAPublicKey) and k.public_numbers() == pub and c != cert:
            raise CertificadoInvalido("Identidade ambígua: mais de um certificado para a mesma chave")
    if cert.version != x509.Version.v3:
        raise CertificadoInvalido("Certificado não é X.509 v3")
    na, nd = cert.not_valid_before_utc, cert.not_valid_after_utc
    if agora < na:
        raise CertificadoInvalido("Certificado ainda não é válido")
    if agora > nd:
        raise CertificadoInvalido("Certificado expirado")
    cnpjs = set(_cnpjs(cert))
    if len(cnpjs) > 1:
        raise CertificadoInvalido("Identidade ambígua: mais de um CNPJ no certificado")
    return CertificadoA1(chave, cert, next(iter(cnpjs)) if cnpjs else None, na, nd, chave.key_size)


def resumo_sanitizado(c: CertificadoA1) -> dict:
    """Somente status — sem serial, SAN integral, chave ou certificado."""
    cnpj = c.cnpj_titular
    return {
        "estrutura_local": c.estrutura_local,
        "algoritmo": f"RSA {c.bits}",
        "valido_ate": c.nao_depois.date().isoformat(),
        "cnpj_titular": f"{cnpj[:2]}.***.***/****-{cnpj[-2:]}" if cnpj else None,
        "identidade": "cnpj_icp_extraido_nao_validado_cadeia" if cnpj else "ausente",
        "cadeia_icp": c.cadeia_icp,
        "revogacao": c.revogacao,
        "autorizacao_governo": c.autorizacao_governo,
        "api_testada": False,
        "fingerprint_prefixo": hashlib.sha256(c.fingerprint().encode()).hexdigest()[:8],
    }
