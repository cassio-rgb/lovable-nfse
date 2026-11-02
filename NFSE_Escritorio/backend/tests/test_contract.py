"""Testes OFFLINE da integração fiscal: XSD oficiais, construção, assinatura, URLs, XML hostil.

Nenhum teste acessa rede ou transmite DPS. Certificados/chaves são sintéticos, gerados em memória.
"""
import base64
import copy
import hashlib
import json
import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from lxml import etree

from app.domain.models import Ambiente, DadosRascunho, Emissao, Estado, pendencias
from app.nfse import secure_xml
from app.nfse.client import (AdaptadorFiscalBloqueado, ConfigTransporte, DESTINOS, Destino, NationalNfseClient,
                             UrlRecusada, contexto_tls_base, validar_url)
from app.nfse.dps import (NS, EntradaDPS, EntradaFiscalInvalida, ParametrosFiscais, Prestador, Servico, Tomador,
                          Tributacao, build_dps, id_dps, validar_xml)
from app.nfse.offline import preparar
from app.nfse.signing import DS, PERFIS_CRIPTO, Assinador, AssinaturaInvalida, verificar
from app.repository import dps_identity

CNPJ = "11222333000181"
BRT = timezone(timedelta(hours=-3))


def cert(cn="Sintetico Teste"):
    k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    n = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    c = (x509.CertificateBuilder().subject_name(n).issuer_name(n).public_key(k.public_key())
         .serial_number(x509.random_serial_number()).not_valid_before(datetime(2026, 1, 1, tzinfo=timezone.utc))
         .not_valid_after(datetime(2027, 1, 1, tzinfo=timezone.utc)).sign(k, hashes.SHA256()))
    return k, c


K1, C1 = cert()
K2, C2 = cert("Outro")
SHA256 = PERFIS_CRIPTO["xmldsig-rsa-sha256-c14n10"]


def entrada(amb=Ambiente.PRODUCAO_RESTRITA, **kw):
    base = dict(
        ambiente=amb, dh_emi=datetime(2026, 10, 31, 10, 0, 0, tzinfo=BRT), ver_aplic="nfse-imoveis-0.1",
        serie="1", n_dps=42, d_compet=date(2026, 10, 15), tp_emit="1", c_loc_emi="3505203",
        prestador=Prestador(CNPJ, op_simp_nac="1", reg_esp_trib="0"),
        tomador=Tomador("52998224725", "Maria Fictícia"),
        servico=Servico("3505203", "100101", "Serviço fictício de teste"),
        valor=Decimal("350.00"), tributacao=Tributacao("1", "1", ind_tot_trib="0"),
        fin_nfse="0" if amb == Ambiente.PRODUCAO_RESTRITA else None)
    base.update(kw)
    return EntradaDPS(**base)


class Esquemas(unittest.TestCase):
    def test_manifest_hashes_and_both_profiles_load(self):
        m = secure_xml.manifest()
        self.assertEqual(m["producao_v1_01_20260209"]["archive_sha256"],
                         "e7935cbd9470527c6cc32984c1b2263e614183bf0139ce2733eaaed2de9a8072")
        self.assertEqual(m["producao_restrita_20261020"]["archive_sha256"],
                         "25fdcecc651a67a216496ab10d7566631e6ed10f721e37d62c7845dadb0ea267")
        for k, v in m.items():
            for f, h in v["files"].items():
                self.assertEqual(hashlib.sha256((secure_xml.SCHEMAS_DIR / k / f).read_bytes()).hexdigest(), h)
            self.assertIsNotNone(secure_xml.load_schema(k))

    def test_tampered_schema_refused(self):
        r = secure_xml._AllowlistResolver(secure_xml.SCHEMAS_DIR / "producao_restrita_20261020", {"x.xsd": "0" * 64})
        with self.assertRaises(secure_xml.EsquemaInvalido):
            r.resolve("http://evil.example/x.xsd", None, None)
        with self.assertRaises(secure_xml.EsquemaInvalido):
            r.resolve("tiposSimples_v1.01.xsd", None, None)  # fora da allowlist informada


class Construcao(unittest.TestCase):
    def test_restrita_valid_with_finNFSe(self):
        x = build_dps(entrada())
        self.assertEqual(validar_xml(Ambiente.PRODUCAO_RESTRITA, x), [])
        self.assertIn(b"<finNFSe>0</finNFSe>", x)
        self.assertIn(b"<dCompet>2026-10-15</dCompet>", x)

    def test_producao_schema_serie_defect_blocks_build(self):
        """XSD de produção v1.01 (2026-02-09) define TSSerieDPS com '^0{0,4}\\d{1,5}$'. Em XSD, ^ e $ são
        literais, então nenhuma série real valida. Não alteramos o esquema oficial: o perfil fica bloqueado."""
        with self.assertRaises(EntradaFiscalInvalida) as cm:
            build_dps(entrada(Ambiente.PRODUCAO))
        self.assertIn("serie", str(cm.exception))
        # Tudo o mais na estrutura de produção é válido: só a série falha, e finNFSe não existe.
        x = build_dps(entrada()).replace(b"<finNFSe>0</finNFSe>", b"").replace(b"<tpAmb>2</tpAmb>", b"<tpAmb>1</tpAmb>")
        erros = validar_xml(Ambiente.PRODUCAO, x)
        self.assertEqual(len(erros), 1)
        self.assertIn("serie", erros[0])

    def test_profiles_differ_on_finNFSe(self):
        sem_fin = build_dps(entrada()).replace(b"<finNFSe>0</finNFSe>", b"")
        self.assertTrue(any("finNFSe" in m or "cLocEmi" in m for m in validar_xml(Ambiente.PRODUCAO_RESTRITA, sem_fin)))  # sem finNFSe → inválido na restrita
        with self.assertRaises(EntradaFiscalInvalida):
            build_dps(entrada(Ambiente.PRODUCAO, fin_nfse="0"))
        with self.assertRaises(EntradaFiscalInvalida):
            build_dps(entrada(fin_nfse=None))

    def test_deterministic_and_element_order(self):
        a, b = build_dps(entrada()), build_dps(entrada())
        self.assertEqual(a, b)
        inf = etree.fromstring(a).find(f"{{{NS}}}infDPS")
        self.assertEqual([etree.QName(c).localname for c in inf],
                         ["tpAmb", "dhEmi", "verAplic", "serie", "nDPS", "dCompet", "tpEmit", "finNFSe", "cLocEmi",
                          "prest", "toma", "serv", "valores"])
        self.assertIn(b'Id="DPS350520321122233300018100001000000000000042"', a)

    def test_official_id_layout(self):
        i = id_dps("3505203", CNPJ, "1", 42)
        self.assertEqual(len(i), 45)
        self.assertEqual((i[3:10], i[10], i[11:25], i[25:30], i[30:]), ("3505203", "2", CNPJ, "00001", "0" * 13 + "42"))

    def test_required_explicit_fields(self):
        cases = [dict(d_compet=datetime(2026, 10, 1)), dict(c_loc_emi="350520"),
                 dict(prestador=Prestador(CNPJ, op_simp_nac="", reg_esp_trib="0")),
                 dict(servico=Servico("3505203", "", "x")), dict(tributacao=Tributacao("", "1", ind_tot_trib="0")),
                 dict(tributacao=Tributacao("1", "1")), dict(valor=Decimal("10.001")), dict(n_dps=0),
                 dict(dh_emi=datetime(2026, 10, 31, 10, 0))]
        for c in cases:
            with self.subTest(c=list(c)), self.assertRaises(EntradaFiscalInvalida):
                build_dps(entrada(**c))

    def test_alphanumeric_cnpj_rejected_not_stripped(self):
        with self.assertRaises(EntradaFiscalInvalida) as cm:
            build_dps(entrada(prestador=Prestador("1A222333000181", "1", "0")))
        self.assertIn("alfanumérico", str(cm.exception))
        d = DadosRascunho("A11.222.333/0001-81", "X", "locacao", "2026-10", "1.00", "descrição")
        self.assertIn("alfanumérico", pendencias(d)["documento"])

    def test_tampered_id_detected(self):
        x = build_dps(entrada()).replace(b"<nDPS>42</nDPS>", b"<nDPS>43</nDPS>")
        self.assertEqual(validar_xml(Ambiente.PRODUCAO_RESTRITA, x), ["Id da DPS não corresponde a cLocEmi/CNPJ/série/número"])


FIXTURE_XLSX = Path(__file__).parent / "fixtures/official/anexo_i-sefin_adn-dps_nfse-snnfse_prodrest-v1-01-20261020.xlsx"


class RegraOficialId(unittest.TestCase):
    """Valida o Id contra o texto da regra oficial E0004 (não contra o próprio helper)."""

    def test_rule_e0004_from_official_annex(self):
        import openpyxl
        data = FIXTURE_XLSX.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), "72b05981c8882cdd807f3acf901b669465360f9cf1b9d9e235ac4363dacfb2d8")
        ws = openpyxl.load_workbook(FIXTURE_XLSX, read_only=True)["RN DPS_NFS-e 1.01"]
        row = next(r for i, r in enumerate(ws.iter_rows(values_only=True), 1) if i == 151)
        self.assertEqual((row[1], row[2]), ("NFSe/infNFSe/DPS/infDPS/", "id"))
        self.assertIn("E0004", row)
        tipos = dict((n, doc) for n, doc in __import__("re").findall(
            r"Tipo de inscrição Federal = (\d) / Inscrição Federal = (CPF|CNPJ)", row[3]))
        self.assertEqual(tipos, {"1": "CPF", "2": "CNPJ"})
        i = id_dps("3505203", CNPJ, "1", 42)
        self.assertEqual(tipos[i[10]], "CNPJ")
        self.assertEqual(i[11:25], CNPJ)


class XmlHostil(unittest.TestCase):
    def test_utf16_utf32_dtd_rejected(self):
        p = '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE a [<!ENTITY x "hello">]><a>&x;</a>'
        for enc in ("utf-16", "utf-16-le", "utf-16-be", "utf-32", "utf-32-le", "utf-32-be"):
            for txt in (p, p.replace("UTF-16", enc.upper()), '<a>sem dtd</a>'):
                with self.subTest(enc=enc, txt=txt[:20]), self.assertRaises(secure_xml.XmlInseguro):
                    secure_xml.parse_untrusted(txt.encode(enc))

    def test_non_utf8_declaration_rejected(self):
        for b in (b'<?xml version="1.0" encoding="ISO-8859-1"?><a>\xe9</a>', b"<a>\xff</a>",
                  "<?xml version='1.0' encoding='UTF-7'?><a/>".encode()):
            with self.assertRaises(secure_xml.XmlInseguro):
                secure_xml.parse_untrusted(b)

    def test_post_parse_dtd_guard(self):
        """Mesmo sem a varredura textual, docinfo/entidades barram DTD (defesa em profundidade)."""
        from unittest import mock
        doc = '<!DOCTYPE a [<!ENTITY x "hello">]><a>&x;</a>'.encode()
        self.assertTrue(etree.fromstring(doc, secure_xml._parser()).getroottree().docinfo.doctype)  # parser sozinho aceita
        u16 = '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE a [<!ENTITY x "hello">]><a>&x;</a>'.encode("utf-16")
        for d in (doc, u16):
            with mock.patch.object(secure_xml, "_prescan", lambda d: None), self.assertRaises(secure_xml.XmlInseguro) as cm:
                secure_xml.parse_untrusted(d)
            self.assertIn("DTD", str(cm.exception))
        with mock.patch.object(secure_xml, "_prescan", lambda d: None), self.assertRaises(secure_xml.XmlInseguro):
            secure_xml.parse_untrusted('<!DOCTYPE a SYSTEM "http://evil.example/x.dtd"><a/>'.encode())  # rede recusada

    def test_valid_utf8_with_bom_and_decl(self):
        self.assertEqual(secure_xml.parse_untrusted(b'\xef\xbb\xbf<?xml version="1.0" encoding="UTF-8"?><a>\xc3\xa9</a>').text, "é")

    def test_oversized(self):
        with self.assertRaises(secure_xml.XmlInseguro):
            secure_xml.parse_untrusted(b"<a>" + b"x" * (secure_xml.MAX_XML_BYTES + 1) + b"</a>")

    def test_xxe_and_billion_laughs(self):
        for p in (b'<?xml version="1.0"?><!DOCTYPE a [<!ENTITY x SYSTEM "file:///etc/passwd">]><a>&x;</a>',
                  b'<!DOCTYPE a [<!ENTITY l "lol"><!ENTITY l2 "&l;&l;&l;">]><a>&l2;</a>',
                  b'<!doctype a SYSTEM "http://evil.example/x.dtd"><a/>'):
            with self.assertRaises(secure_xml.XmlInseguro):
                secure_xml.parse_untrusted(p)

    def test_malformed(self):
        with self.assertRaises(secure_xml.XmlInseguro):
            secure_xml.parse_untrusted(b"<a><b></a>")


class Assinatura(unittest.TestCase):
    def setUp(self):
        self.signed = Assinador(K1, C1, SHA256).assinar(build_dps(entrada()))

    def test_sign_and_verify_with_xsd(self):
        self.assertEqual(verificar(self.signed, C1, SHA256, Ambiente.PRODUCAO_RESTRITA),
                         "DPS350520321122233300018100001000000000000042")
        root = etree.fromstring(self.signed)
        self.assertEqual(root[1].tag, f"{{{DS}}}Signature")
        self.assertEqual(root[1].find(f".//{{{DS}}}Reference").get("URI"), "#" + root[0].get("Id"))

    def test_sha1_legacy_profile_signs_but_never_allows_live(self):
        p = PERFIS_CRIPTO["xmldsig-rsa-sha1-c14n10-legado"]
        s = Assinador(K1, C1, p).assinar(build_dps(entrada()))
        verificar(s, C1, p, Ambiente.PRODUCAO_RESTRITA)
        with self.assertRaises(AssinaturaInvalida):
            verificar(s, C1, SHA256, Ambiente.PRODUCAO_RESTRITA)  # perfil divergente
        self.assertFalse(any(x.permite_transmissao for x in PERFIS_CRIPTO.values()))

    def test_tamper_value(self):
        with self.assertRaises(AssinaturaInvalida):
            verificar(self.signed.replace(b"<vServ>350.00</vServ>", b"<vServ>1.00</vServ>"), C1, SHA256, Ambiente.PRODUCAO_RESTRITA)

    def test_wrong_cert(self):
        with self.assertRaises(AssinaturaInvalida):
            verificar(self.signed, C2, SHA256, Ambiente.PRODUCAO_RESTRITA)
        with self.assertRaises(ValueError):
            Assinador(K2, C1, SHA256)

    def test_signature_value_tamper(self):
        root = etree.fromstring(self.signed)
        sv = root.find(f".//{{{DS}}}SignatureValue")
        raw = bytearray(base64.b64decode(sv.text)); raw[0] ^= 1
        sv.text = base64.b64encode(bytes(raw)).decode()
        with self.assertRaises(AssinaturaInvalida):
            verificar(etree.tostring(root), C1, SHA256, Ambiente.PRODUCAO_RESTRITA)

    def test_wrapping_and_duplicate_id(self):
        root = etree.fromstring(self.signed)
        evil = copy.deepcopy(root[0])
        evil.find(f".//{{{NS}}}vServ").text = "1.00"
        w1 = copy.deepcopy(root); w1.insert(0, evil)  # infDPS falso antes do assinado
        w2 = copy.deepcopy(root); w2[1].append(copy.deepcopy(root[0]))  # infDPS original escondido em Signature
        w3 = copy.deepcopy(root); w3[0].find(f"{{{NS}}}prest").set("Id", w3[0].get("Id"))
        w4 = copy.deepcopy(root); w4[1].find(f".//{{{DS}}}Reference").set("URI", "")
        for w in (w1, w2, w3, w4):
            with self.assertRaises(AssinaturaInvalida):
                verificar(etree.tostring(w), C1, SHA256, Ambiente.PRODUCAO_RESTRITA)

    def test_signed_but_wrong_environment_or_incoherent_id(self):
        a = Assinador(K1, C1, SHA256)
        tp = a.assinar(build_dps(entrada()).replace(b"<tpAmb>2</tpAmb>", b"<tpAmb>1</tpAmb>"))
        with self.assertRaises(AssinaturaInvalida) as cm:
            verificar(tp, C1, SHA256, Ambiente.PRODUCAO_RESTRITA)
        self.assertIn("tpAmb", str(cm.exception))
        ida = a.assinar(build_dps(entrada()).replace(b"<nDPS>42</nDPS>", b"<nDPS>43</nDPS>"))
        with self.assertRaises(AssinaturaInvalida) as cm:
            verificar(ida, C1, SHA256, Ambiente.PRODUCAO_RESTRITA)
        self.assertIn("Id da DPS", str(cm.exception))
        tipo1 = build_dps(entrada())
        tipo1 = tipo1.replace(b'Id="DPS35052032', b'Id="DPS35052031')
        with self.assertRaises(AssinaturaInvalida):
            verificar(a.assinar(tipo1), C1, SHA256, Ambiente.PRODUCAO_RESTRITA)

    def test_double_sign_refused(self):
        with self.assertRaises(AssinaturaInvalida):
            Assinador(K1, C1, SHA256).assinar(self.signed)

    def test_repr_hides_secrets(self):
        r = repr(Assinador(K1, C1, SHA256))
        self.assertNotIn("PRIVATE", r)
        self.assertNotIn(base64.b64encode(C1.public_bytes(__import__("cryptography.hazmat.primitives.serialization", fromlist=["Encoding"]).Encoding.DER)).decode()[:40], r)


class Transporte(unittest.TestCase):
    D = DESTINOS[Ambiente.PRODUCAO_RESTRITA]
    OK = "https://sefin.producaorestrita.nfse.gov.br/API/SefinNacional/nfse"

    def test_exact_allowlist(self):
        self.assertEqual(validar_url("POST", self.OK, self.D), self.OK)
        idd = "DPS" + "1" * 42
        validar_url("HEAD", f"https://sefin.producaorestrita.nfse.gov.br/API/SefinNacional/dps/{idd}", self.D)

    def test_url_attacks(self):
        h = "sefin.producaorestrita.nfse.gov.br"
        bad = [
            f"http://{h}/API/SefinNacional/nfse",
            f"https://{h}.evil.example/API/SefinNacional/nfse",
            f"https://{h}@evil.example/API/SefinNacional/nfse",
            f"https://evil.example/{h}/API/SefinNacional/nfse",
            f"https://{h}:8443/API/SefinNacional/nfse",
            f"https://{h}/API/SefinNacional/nfse/../admin",
            f"https://{h}/API/SefinNacional/nfse?x=1",
            f"https://{h}/API/SefinNacional/nfse#f",
            f"https://{h}/API/SefinNacional/nfsex",
            f"https://{h}/API/SefinNacional/%6efse",
            f"https://{h}\\@evil.example/API/SefinNacional/nfse",
            f"https://sefin.nfse.gov.br/SefinNacional/nfse",  # host de produção no destino restrito
            f"HTTPS://{h.upper()}/API/SefinNacional/nfse",
        ]
        for u in bad:
            with self.subTest(u=u), self.assertRaises(UrlRecusada):
                validar_url("POST", u, self.D)
        with self.assertRaises(UrlRecusada):
            validar_url("GET", self.OK, self.D)  # método fora da allowlist

    def test_transport_config_guards(self):
        for kw in (dict(verificar_tls=False), dict(seguir_redirecionamento=True), dict(tentativas_post=2),
                   dict(read_timeout=0)):
            with self.assertRaises(ValueError):
                ConfigTransporte(**kw)
        ctx = contexto_tls_base()
        import ssl
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(ctx.check_hostname)

    def test_prepared_requests_and_live_blocked(self):
        c = NationalNfseClient(Ambiente.PRODUCAO_RESTRITA)
        r = c.preparar_envio(b"<DPS/>")
        self.assertEqual((r.method, r.url, r.allow_redirects, r.contrato_corpo_verificado), ("POST", self.OK, False, False))
        self.assertNotIn("DPS", repr(r))
        with self.assertRaises(UrlRecusada):
            c.preparar_consulta_dps("DPS123/../x")
        with self.assertRaises(AdaptadorFiscalBloqueado) as cm:
            c.submit(None)  # type: ignore[arg-type]
        self.assertIn("contrato HTTP", str(cm.exception))
        with self.assertRaises(AdaptadorFiscalBloqueado):
            c.lookup(None)  # type: ignore[arg-type]
        with self.assertRaises(UrlRecusada):
            NationalNfseClient(Ambiente.PRODUCAO, destino=Destino("evil.example", "/x"))
        with self.assertRaises(UrlRecusada):
            NationalNfseClient(Ambiente.PRODUCAO, destino=DESTINOS[Ambiente.PRODUCAO_RESTRITA])


class Params:
    def __init__(self, p):
        self.p = p

    def parametros(self, empresa_id, operacao, ambiente):
        return self.p


PARAMS = ParametrosFiscais(c_loc_emi="3505203", serie="1", tp_emit="1", prestador=Prestador(CNPJ, "1", "0"),
                           c_loc_prestacao="3505203", c_trib_nac="100101", tributacao=Tributacao("1", "1", ind_tot_trib="0"),
                           ver_aplic="nfse-imoveis-0.1", fin_nfse="0")


def emissao(amb=Ambiente.PRODUCAO_RESTRITA, **kw):
    snap = DadosRascunho("529.982.247-25", "Maria Fictícia", "locacao", "2026-10", "350.00", "Administração fictícia")
    e = Emissao("op1", "emp1", "r1", 1, amb, kw.pop("identidade_dps", None) or dps_identity("emp1", amb.value, 7), snap, "rev1", "k", estado=Estado.NA_FILA)
    for k, v in kw.items():
        setattr(e, k, v)
    return e


class Offline(unittest.TestCase):
    def test_prepare_signed_artifact_from_immutable_snapshot(self):
        e = emissao()
        before = json.dumps(e.snapshot.__dict__)
        a = preparar(e, CNPJ, Params(PARAMS), date(2026, 10, 20), datetime(2026, 10, 31, 9, tzinfo=BRT), Assinador(K1, C1, SHA256))
        self.assertTrue(a.id_dps.endswith("000000000000007"))
        self.assertFalse(a.transmissivel)
        self.assertEqual(a.perfil_cripto_status, "nao_confirmado")
        self.assertEqual(e.estado, Estado.NA_FILA)  # não muda estado / não "emite"
        self.assertEqual(json.dumps(e.snapshot.__dict__), before)
        verificar(a.xml, C1, SHA256, Ambiente.PRODUCAO_RESTRITA)
        self.assertNotIn("Maria", repr(a))

    def test_inconsistencies_rejected(self):
        dh = datetime(2026, 10, 31, 9, tzinfo=BRT)
        with self.assertRaises(EntradaFiscalInvalida):
            preparar(emissao(), CNPJ, Params(PARAMS), None, dh)  # mês não implica dia
        with self.assertRaises(EntradaFiscalInvalida):
            preparar(emissao(), CNPJ, Params(PARAMS), date(2026, 11, 1), dh)  # fora da competência
        with self.assertRaises(EntradaFiscalInvalida):
            preparar(emissao(), "45723174000110", Params(PARAMS), date(2026, 10, 1), dh)  # CNPJ de outra empresa
        with self.assertRaises(EntradaFiscalInvalida):
            preparar(emissao(), CNPJ, Params(None), date(2026, 10, 1), dh)  # parâmetros não cadastrados
        with self.assertRaises(EntradaFiscalInvalida):
            preparar(emissao(Ambiente.PRODUCAO), CNPJ, Params(PARAMS), date(2026, 10, 1), dh)  # finNFSe na produção
        with self.assertRaises(EntradaFiscalInvalida):
            preparar(emissao(estado=Estado.EMITIDA), CNPJ, Params(PARAMS), date(2026, 10, 1), dh)
        with self.assertRaises(ValueError):
            preparar(emissao(identidade_dps="DPS-x-emp1-abc"), CNPJ, Params(PARAMS), date(2026, 10, 1), dh)
        for outra in (dps_identity("emp2", "producao_restrita", 7), dps_identity("emp1", "producao", 7),
                      dps_identity("emp1", "producao_restrita", 7) + "0", "X" + dps_identity("emp1", "producao_restrita", 7)):
            with self.subTest(outra=outra), self.assertRaises(ValueError):
                preparar(emissao(identidade_dps=outra), CNPJ, Params(PARAMS), date(2026, 10, 1), dh)


if __name__ == "__main__":
    unittest.main()
