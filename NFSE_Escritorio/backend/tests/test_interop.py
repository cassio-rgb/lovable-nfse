"""Verificação INDEPENDENTE da assinatura com xmlsec1 (libxmlsec, C), não com o verificador próprio.

Exige o binário `xmlsec1` (PATH ou variável XMLSEC1). `scripts/verify.py --mode local` resolve via
nix e falha se não conseguir. signxml 5.2.0 não é usado: com o libxml2 2.14.6 empacotado no lxml
6.0.2/6.1.3, a C14N de subárvore deste ambiente é defeituosa (ver docs/nfse-integration-evidence.md).
"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization

from app.domain.models import Ambiente
from tests.test_contract import C1, C2, K1, SHA256, PERFIS_CRIPTO, Assinador, build_dps, entrada

XMLSEC1 = os.environ.get("XMLSEC1") or shutil.which("xmlsec1")


@unittest.skipUnless(XMLSEC1, "xmlsec1 ausente (verify.py --mode local exige)")
class Xmlsec1(unittest.TestCase):
    def run_xmlsec(self, xml: bytes, cert=C1) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "c.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
            (Path(d) / "s.xml").write_bytes(xml)
            return subprocess.run([XMLSEC1, "--verify", "--id-attr:Id", "http://www.sped.fazenda.gov.br/nfse:infDPS",
                                   "--trusted-pem", f"{d}/c.pem", "--enabled-reference-uris", "same-doc", f"{d}/s.xml"],
                                  capture_output=True, text=True, timeout=60)

    def test_sha256_and_sha1_profiles_verify(self):
        for p in (SHA256, PERFIS_CRIPTO["xmldsig-rsa-sha1-c14n10-legado"]):
            r = self.run_xmlsec(Assinador(K1, C1, p).assinar(build_dps(entrada())))
            self.assertEqual(r.returncode, 0, r.stderr[-400:])
            self.assertTrue({"OK", "Verification status: OK"}.intersection((r.stdout + r.stderr).splitlines()), r.stdout + r.stderr)

    def test_tamper_and_wrong_trust_fail(self):
        s = Assinador(K1, C1, SHA256).assinar(build_dps(entrada()))
        self.assertNotEqual(self.run_xmlsec(s.replace(b"<vServ>350.00</vServ>", b"<vServ>1.00</vServ>")).returncode, 0)
        self.assertNotEqual(self.run_xmlsec(s, cert=C2).returncode, 0)


if __name__ == "__main__":
    unittest.main()
