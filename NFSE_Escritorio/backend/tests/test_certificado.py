"""A1 PKCS#12 + delegação — somente material SINTÉTICO gerado em memória (nenhum certificado real)."""
import io
import os
import pickle
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from app.domain.models import Ambiente
from app.nfse import secure_xml
from app.nfse.certificado import (OID_CNPJ, CertificadoInvalido, SenhaA1, carregar_a1, cnpj_de_othername,
                                  resumo_sanitizado)
from app.nfse.delegacao import (SERVICO_RECEITA_NFSE, DelegacaoRecusada, ProvedorAutorizacaoAusente, ReciboWeb,
                                ResultadoAutorizacao, contexto_assinatura)
from app.nfse.dps import NS, EntradaFiscalInvalida
from app.nfse.offline import preparar
from app.nfse.signing import Assinador
from tests.test_contract import BRT, CNPJ, PARAMS, SHA256, Params, emissao

ESCRITORIO = "45723174000110"  # fictício
OUTRA = "19131243000197"       # fictício
AGORA = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
SENHA = "s3nh@-sintetica-XYZ"
ROOT = Path(__file__).resolve().parents[2]


def octet(s: str) -> bytes:
    b = s.encode()
    return bytes([0x04, len(b)]) + b


def gerar(cnpjs=(ESCRITORIO,), key=None, inicio=datetime(2026, 1, 1, tzinfo=timezone.utc),
          fim=datetime(2027, 1, 1, tzinfo=timezone.utc), senha=SENHA, sem_chave=False, extra_mesma_chave=False,
          cn="NOME QUALQUER:11222333000181"):
    k = key or rsa.generate_private_key(public_exponent=65537, key_size=2048)
    n = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    def novo():
        b = (x509.CertificateBuilder().subject_name(n).issuer_name(n).public_key(k.public_key())
             .serial_number(x509.random_serial_number()).not_valid_before(inicio).not_valid_after(fim))
        if cnpjs:
            b = b.add_extension(x509.SubjectAlternativeName(
                [x509.OtherName(x509.ObjectIdentifier(OID_CNPJ), octet(c)) for c in cnpjs]), critical=False)
        return b.sign(k, hashes.SHA256())
    c = novo()
    extras = [novo()] if extra_mesma_chave else None
    enc = serialization.BestAvailableEncryption(senha.encode())
    return pkcs12.serialize_key_and_certificates(b"a1", None if sem_chave else k, c, extras, enc), k, c


_K = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PFX, KEY, CERT = gerar(key=_K)


class Prov:
    nome = "sintetico"
    somente_teste = True

    def __init__(self, **kw):
        self.kw = kw

    def consultar(self, outorgante, outorgado, servico, ambiente):
        d = dict(outorgante_cnpj=outorgante, outorgado_cnpj=outorgado, servico=servico, ambiente=ambiente,
                 status="autorizada", consultado_em=AGORA - timedelta(seconds=10), valido_ate=None, provedor=self.nome)
        d.update(self.kw)
        return ResultadoAutorizacao(**d)


class Carregamento(unittest.TestCase):
    def test_valido_extrai_cnpj_icp_e_nao_valida_cadeia(self):
        a = carregar_a1(PFX, SenhaA1(SENHA), AGORA)
        self.assertEqual(a.cnpj_titular, ESCRITORIO)
        self.assertEqual((a.cadeia_icp, a.revogacao, a.autorizacao_governo), ("nao_verificado",) * 3)

    def test_cn_nunca_e_identidade(self):
        pfx, _, _ = gerar(cnpjs=())
        self.assertIsNone(carregar_a1(pfx, SenhaA1(SENHA), AGORA).cnpj_titular)

    def test_cnpj_todo_zero_e_indisponivel(self):
        pfx, _, _ = gerar(cnpjs=("0" * 14,))
        self.assertIsNone(carregar_a1(pfx, SenhaA1(SENHA), AGORA).cnpj_titular)

    def test_rejeicoes(self):
        casos = {
            "senha": (PFX, "errada"),
            "expirado": (gerar(fim=datetime(2026, 6, 1, tzinfo=timezone.utc))[0], SENHA),
            "futuro": (gerar(inicio=datetime(2026, 12, 1, tzinfo=timezone.utc))[0], SENHA),
            "sem_chave": (gerar(sem_chave=True)[0], SENHA),
            "ambiguo_cnpj": (gerar(cnpjs=(ESCRITORIO, OUTRA))[0], SENHA),
            "ambiguo_cert": (gerar(extra_mesma_chave=True)[0], SENHA),
            "vazio": (b"", SENHA),
            "grande": (b"0" * 70000, SENHA),
        }
        for nome, (dados, s) in casos.items():
            with self.subTest(nome), self.assertRaises(CertificadoInvalido) as cm:
                carregar_a1(dados, SenhaA1(s), AGORA)
            self.assertNotIn(SENHA, str(cm.exception))

    def test_chave_nao_rsa_e_rsa_curta(self):
        for k in (ec.generate_private_key(ec.SECP256R1()), rsa.generate_private_key(65537, 1024)):
            with self.subTest(type(k).__name__), self.assertRaises(CertificadoInvalido):
                carregar_a1(gerar(key=k)[0], SenhaA1(SENHA), AGORA)

    def test_der_estrito(self):
        self.assertEqual(cnpj_de_othername(bytes([0x13, 14]) + ESCRITORIO.encode()), ESCRITORIO)
        self.assertEqual(cnpj_de_othername(bytes([0xA0, 16]) + octet(ESCRITORIO)), ESCRITORIO)
        for ruim in (octet(ESCRITORIO) + b"\x00", bytes([0x0C, 14]) + ESCRITORIO.encode(), octet("4572317400011"),
                     octet("4572317400011A"), bytes([0x04, 0x81, 14]) + ESCRITORIO.encode(), bytes([0x04, 20]) + b"1",
                     bytes([0x04, 0x85, 1, 1, 1, 1, 1]), b"\x04", b"\x04" * 80):
            with self.subTest(ruim[:4].hex()), self.assertRaises(CertificadoInvalido):
                cnpj_de_othername(ruim)

    def test_sem_vazamento(self):
        s = SenhaA1(SENHA)
        a = carregar_a1(PFX, s, AGORA)
        for txt in (repr(s), str(s), repr(a), str(resumo_sanitizado(a))):
            self.assertNotIn(SENHA, txt)
            self.assertNotIn(ESCRITORIO, txt)
            self.assertNotIn(str(CERT.serial_number), txt)
        for obj in (s, a):
            with self.assertRaises(TypeError):
                pickle.dumps(obj)


class Delegacao(unittest.TestCase):
    def setUp(self):
        self.a1 = carregar_a1(PFX, SenhaA1(SENHA), AGORA)
        p = mock.patch.dict(os.environ, {"APP_ENV": "test"})
        p.start()
        self.addCleanup(p.stop)

    def ctx(self, prov, amb=Ambiente.PRODUCAO_RESTRITA, emit=CNPJ, **kw):
        return contexto_assinatura(emit, self.a1, amb, prov, AGORA, **kw)

    def test_recusas(self):
        casos = {
            "sem_provedor": None,
            "provedor_ausente": ProvedorAutorizacaoAusente(),
            "revogada": Prov(status="revogada"),
            "inexistente": Prov(status="inexistente"),
            "outra_empresa": Prov(outorgante_cnpj=OUTRA),
            "outro_outorgado": Prov(outorgado_cnpj=OUTRA),
            "outro_ambiente": Prov(ambiente=Ambiente.PRODUCAO),
            "outro_servico": Prov(servico="00001"),
            "expirada": Prov(valido_ate=AGORA - timedelta(seconds=1)),
            "desatualizada": Prov(consultado_em=AGORA - timedelta(hours=1)),
        }
        for nome, prov in casos.items():
            with self.subTest(nome), self.assertRaises(DelegacaoRecusada):
                self.ctx(prov)

    def test_recibo_web_nao_e_autorizacao(self):
        recibo = ReciboWeb(CNPJ, ESCRITORIO, date(2026, 11, 2))
        with self.assertRaises(DelegacaoRecusada):
            self.ctx(None, recibo_web=recibo)
        self.assertEqual(recibo.status, "informativo_nao_verificado_api")

    def test_sintetico_fora_de_teste_recusado(self):
        with mock.patch.dict(os.environ, {"APP_ENV": "production"}), self.assertRaises(DelegacaoRecusada):
            self.ctx(Prov())

    def test_certificado_sem_identidade_recusado(self):
        a1 = carregar_a1(gerar(cnpjs=())[0], SenhaA1(SENHA), AGORA)
        with self.assertRaises(DelegacaoRecusada):
            contexto_assinatura(CNPJ, a1, Ambiente.PRODUCAO_RESTRITA, Prov(), AGORA)

    def test_dps_mantem_emitente_cliente(self):
        c = self.ctx(Prov())
        self.assertTrue(c.delegado)
        self.assertEqual(c.autorizacao.servico, SERVICO_RECEITA_NFSE)
        art = preparar(emissao(), CNPJ, Params(PARAMS), date(2026, 10, 20), datetime(2026, 10, 31, 9, tzinfo=BRT),
                       Assinador(self.a1.chave, self.a1.certificado, SHA256), contexto=c)
        root = secure_xml.parse_untrusted(art.xml)
        self.assertEqual(root.find(f".//{{{NS}}}prest/{{{NS}}}CNPJ").text, CNPJ)
        self.assertNotIn(ESCRITORIO.encode(), root.find(f"{{{NS}}}infDPS").get("Id").encode())
        self.assertFalse(art.transmissivel)

    def test_preparar_recusa_sem_contexto_ou_contexto_cruzado(self):
        ass = Assinador(self.a1.chave, self.a1.certificado, SHA256)
        args = (emissao(), CNPJ, Params(PARAMS), date(2026, 10, 20), datetime(2026, 10, 31, 9, tzinfo=BRT))
        with self.assertRaises(EntradaFiscalInvalida):
            preparar(*args, ass)  # certificado de terceiro sem delegação
        outra = contexto_assinatura(OUTRA, self.a1, Ambiente.PRODUCAO_RESTRITA, Prov(), AGORA)
        with self.assertRaises(EntradaFiscalInvalida):
            preparar(*args, ass, contexto=outra)  # reuso entre empresas
        amb = contexto_assinatura(CNPJ, self.a1, Ambiente.PRODUCAO, Prov(), AGORA)
        with self.assertRaises(EntradaFiscalInvalida):
            preparar(*args, ass, contexto=amb)  # ambiente diferente
        _, k2, c2 = gerar()
        with self.assertRaises(EntradaFiscalInvalida):
            preparar(*args, Assinador(k2, c2, SHA256), contexto=self.ctx(Prov()))  # outro certificado


class CLI(unittest.TestCase):
    def run_cli(self, path, senha):
        sys.path.insert(0, str(ROOT / "scripts"))
        import inspecionar_certificado as cli
        out = io.StringIO()
        with mock.patch("getpass.getpass", return_value=senha), redirect_stdout(out):
            rc = cli.main([str(path)])
        return rc, out.getvalue()

    def test_cli_sanitizado_e_nao_pronto(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "escritorio-11222333000181.pfx"
            p.write_bytes(PFX)
            antes = sorted(os.listdir(d))
            rc, out = self.run_cli(p, SENHA)
            self.assertEqual(rc, 2)
            self.assertIn("NÃO PRONTO", out)
            self.assertIn("API: NÃO TESTADA", out)
            for segredo in (SENHA, ESCRITORIO, str(CERT.serial_number), d, "11222333000181"):
                self.assertNotIn(segredo, out)
            rc, out = self.run_cli(p, "errada")
            self.assertEqual(rc, 1)
            self.assertNotIn("errada", out)
            self.assertNotIn(d, out)
            rc, out = self.run_cli(Path(d) / "nao-existe.pfx", SENHA)
            self.assertEqual(rc, 1)
            self.assertNotIn(d, out)
            self.assertEqual(sorted(os.listdir(d)), antes)

    def test_cli_recusa_senha_por_argumento(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts/inspecionar_certificado.py"), "x.pfx", "--senha", "y"],
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("y\n", r.stdout)


if __name__ == "__main__":
    unittest.main()
