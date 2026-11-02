"""Assinatura XMLDSIG envelopada da DPS (referência exata a infDPS/@Id) e verificação local.

O *perfil criptográfico* (algoritmos, canonicalização, transforms) é explícito e versionado.
A capacidade de assinar é independente do status de aprovação: nenhum perfil embutido está
confirmado por fonte oficial vigente (os XSD atuais não fixam algoritmo; o manual 2022 com
RSA-SHA1 não é evidência atual). Perfis não confirmados nunca liberam transmissão real.

Nunca registra chave, certificado completo nem XML integral em logs.
"""
from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from lxml import etree

from . import secure_xml
from .dps import NS, PERFIS, coerencia
from ..domain.models import Ambiente

DS = "http://www.w3.org/2000/09/xmldsig#"
C14N_10 = "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
ENVELOPED = "http://www.w3.org/2000/09/xmldsig#enveloped-signature"
STATUS_CONFIRMADO = "confirmado_fonte_oficial"


@dataclass(frozen=True)
class PerfilCripto:
    id: str
    versao: int
    signature_method: str
    digest_method: str
    hash_alg: type
    status: str  # "nao_confirmado" | "legado_nao_vigente" | STATUS_CONFIRMADO
    fonte: str
    canonicalization: str = C14N_10
    transforms: tuple[str, ...] = (ENVELOPED, C14N_10)

    @property
    def permite_transmissao(self) -> bool:
        return self.status == STATUS_CONFIRMADO


PERFIS_CRIPTO = {
    p.id: p for p in (
        PerfilCripto("xmldsig-rsa-sha256-c14n10", 1, "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
                     "http://www.w3.org/2001/04/xmlenc#sha256", hashes.SHA256, "nao_confirmado",
                     "Candidato; OpenAPI/manual vigentes não confirmaram algoritmo (consulta 2026-10-31: 403)."),
        PerfilCripto("xmldsig-rsa-sha1-c14n10-legado", 1, "http://www.w3.org/2000/09/xmldsig#rsa-sha1",
                     "http://www.w3.org/2000/09/xmldsig#sha1", hashes.SHA1, "legado_nao_vigente",
                     "Manual arquivado 2022; insuficiente como evidência atual."),
    )
}


def perfil_cripto(pid: str) -> PerfilCripto:
    if pid not in PERFIS_CRIPTO:
        raise ValueError(f"Perfil criptográfico desconhecido: {pid}")
    return PERFIS_CRIPTO[pid]


class AssinaturaInvalida(ValueError):
    pass


def _c14n(el) -> bytes:
    """C14N 1.0 inclusiva de subárvore. Canonicaliza uma cópia destacada (que preserva os namespaces
    em escopo): o libxml2 deste ambiente emite `xmlns=""` espúrio ao canonicalizar in-place um
    elemento cujo default namespace redefine o do ancestral (Signature dentro de DPS)."""
    import copy
    return etree.tostring(copy.deepcopy(el), method="c14n", exclusive=False, with_comments=False)


def _digest(p: PerfilCripto, data: bytes) -> str:
    h = hashlib.new(p.hash_alg.name, data)
    return base64.b64encode(h.digest()).decode()


class Assinador:
    def __init__(self, chave: rsa.RSAPrivateKey, certificado: x509.Certificate, perfil: PerfilCripto) -> None:
        if not isinstance(chave, rsa.RSAPrivateKey):
            raise ValueError("Somente RSA é suportado")
        pub = certificado.public_key()
        if pub.public_numbers() != chave.public_key().public_numbers():
            raise ValueError("Chave privada não corresponde ao certificado")
        self._k, self.certificado, self.perfil = chave, certificado, perfil

    def __repr__(self) -> str:  # nunca expõe material sensível
        return f"Assinador(perfil={self.perfil.id}, cert_sha256={self.cert_fingerprint()[:16]}…)"

    def cert_fingerprint(self) -> str:
        return self.certificado.fingerprint(hashes.SHA256()).hex()

    def assinar(self, xml: bytes) -> bytes:
        root = secure_xml.parse_untrusted(xml)
        _estrutura(root, assinada=False)
        inf = root[0]
        p = self.perfil
        sig = etree.SubElement(root, f"{{{DS}}}Signature", nsmap={None: DS})
        si = etree.SubElement(sig, f"{{{DS}}}SignedInfo")
        etree.SubElement(si, f"{{{DS}}}CanonicalizationMethod").set("Algorithm", p.canonicalization)
        etree.SubElement(si, f"{{{DS}}}SignatureMethod").set("Algorithm", p.signature_method)
        ref = etree.SubElement(si, f"{{{DS}}}Reference")
        ref.set("URI", "#" + inf.get("Id"))
        tr = etree.SubElement(ref, f"{{{DS}}}Transforms")
        for t in p.transforms:
            etree.SubElement(tr, f"{{{DS}}}Transform").set("Algorithm", t)
        etree.SubElement(ref, f"{{{DS}}}DigestMethod").set("Algorithm", p.digest_method)
        etree.SubElement(ref, f"{{{DS}}}DigestValue").text = _digest(p, _c14n(inf))
        sv = etree.SubElement(sig, f"{{{DS}}}SignatureValue")
        sv.text = base64.b64encode(self._k.sign(_c14n(si), padding.PKCS1v15(), p.hash_alg())).decode()
        x5 = etree.SubElement(etree.SubElement(sig, f"{{{DS}}}KeyInfo"), f"{{{DS}}}X509Data")
        etree.SubElement(x5, f"{{{DS}}}X509Certificate").text = base64.b64encode(
            self.certificado.public_bytes(serialization.Encoding.DER)).decode()
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


def _estrutura(root, assinada: bool) -> None:
    if root.tag != f"{{{NS}}}DPS":
        raise AssinaturaInvalida("Raiz deve ser DPS")
    kids = [c for c in root if isinstance(c.tag, str)]
    esperado = [f"{{{NS}}}infDPS"] + ([f"{{{DS}}}Signature"] if assinada else [])
    if [c.tag for c in kids] != esperado:
        raise AssinaturaInvalida("Estrutura inesperada (infDPS/Signature)")
    ids = [(el, v) for el in root.iter() if isinstance(el.tag, str)
           for k, v in el.attrib.items() if k.lower() == "id"]
    if len(ids) != 1 or ids[0][0] is not kids[0]:
        raise AssinaturaInvalida("Atributo Id duplicado ou fora de infDPS")


def _one(parent, path):
    found = parent.findall(path, {"ds": DS})
    if len(found) != 1:
        raise AssinaturaInvalida(f"Esperado exatamente um {path}")
    return found[0]


def verificar(xml: bytes, certificado_esperado: x509.Certificate, perfil: PerfilCripto,
              ambiente: Ambiente) -> str:
    """Verifica assinatura, perfil, certificado e XSD. Devolve o Id da DPS assinada."""
    root = secure_xml.parse_untrusted(xml)
    _estrutura(root, assinada=True)
    inf, sig = root[0], root[1]
    si = _one(sig, "ds:SignedInfo")
    if _one(si, "ds:CanonicalizationMethod").get("Algorithm") != perfil.canonicalization:
        raise AssinaturaInvalida("Canonicalização fora do perfil")
    if _one(si, "ds:SignatureMethod").get("Algorithm") != perfil.signature_method:
        raise AssinaturaInvalida("Algoritmo de assinatura fora do perfil")
    ref = _one(si, "ds:Reference")
    if ref.get("URI") != "#" + (inf.get("Id") or "\0"):
        raise AssinaturaInvalida("Referência não aponta para infDPS")
    if tuple(t.get("Algorithm") for t in ref.findall("ds:Transforms/ds:Transform", {"ds": DS})) != perfil.transforms:
        raise AssinaturaInvalida("Transforms fora do perfil")
    if _one(ref, "ds:DigestMethod").get("Algorithm") != perfil.digest_method:
        raise AssinaturaInvalida("Digest fora do perfil")
    if (_one(ref, "ds:DigestValue").text or "").strip() != _digest(perfil, _c14n(inf)):
        raise AssinaturaInvalida("Digest não confere (conteúdo alterado)")
    der = base64.b64decode(_one(sig, "ds:KeyInfo/ds:X509Data/ds:X509Certificate").text or "")
    if der != certificado_esperado.public_bytes(serialization.Encoding.DER):
        raise AssinaturaInvalida("Certificado diferente do esperado")
    try:
        certificado_esperado.public_key().verify(
            base64.b64decode(_one(sig, "ds:SignatureValue").text or ""), _c14n(si), padding.PKCS1v15(), perfil.hash_alg())
    except InvalidSignature as exc:
        raise AssinaturaInvalida("Assinatura inválida") from exc
    if ambiente is not None:
        erros = secure_xml.validate(PERFIS[ambiente].nome, root) or coerencia(root, ambiente)
        if erros:
            raise AssinaturaInvalida("XSD: " + erros[0])
    return inf.get("Id")
