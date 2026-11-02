"""Preflight: nunca vaza valores e nunca fica verde com config de teste/demo ou só com URLs presentes."""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "preflight.py"
SEGREDO = "s3nh4-SUPER-secreta-xyz"


def run(env, *args):
    base = {"PATH": os.environ.get("PATH", "")}
    return subprocess.run([sys.executable, str(SCRIPT), *args], env={**base, **env}, capture_output=True, text=True, timeout=30)


FULL = {
    "APP_ENV": "homologacao", "NFSE_ENVIRONMENT": "producao_restrita", "NFSE_PRODUCTION_ENABLED": "false",
    "IDENTITY_ISSUER": f"https://user:{SEGREDO}@idp.example", "IDENTITY_AUDIENCE": "nfse",
    "DATABASE_URL": f"postgresql://nfse_api:{SEGREDO}@db.example/nfse",
    "WORKER_DATABASE_URL": f"postgresql://w:{SEGREDO}@db.example/nfse",
    "STORAGE_S3_ENDPOINT": "https://storage.example.test/storage/v1/s3",
    "STORAGE_S3_REGION": "us-test-1",
    "STORAGE_S3_ACCESS_KEY_ID": "fake-access",
    "STORAGE_S3_SECRET_ACCESS_KEY": SEGREDO,
    "STORAGE_CONTAINER": "nfse-documentos",
    "CERTIFICATE_REFERENCE": f"vault://{SEGREDO}", "CORS_ORIGINS": "https://app.example",
}


class Preflight(unittest.TestCase):
    def test_no_secret_or_url_leak(self):
        for args in ((), ("--json",)):
            r = run(FULL, *args)
            self.assertNotIn(SEGREDO, r.stdout + r.stderr)
            self.assertNotIn("db.example", r.stdout + r.stderr)
            self.assertNotIn("idp.example", r.stdout + r.stderr)

    def test_all_config_present_still_blocked(self):
        r = run(FULL, "--json")
        self.assertEqual(r.returncode, 1)
        d = json.loads(r.stdout)
        self.assertFalse(d["pronto"])
        st = {i["item"]: i["status"] for i in d["itens"]}
        self.assertEqual(st["DATABASE_URL"], "presente_nao_validado")  # presença ≠ validação
        self.assertEqual(st["verificador_identidade"], "presente_nao_validado")
        self.assertEqual(st["storage_privado_duravel"], "presente_nao_validado")
        self.assertEqual(st["cofre_certificados"], "ausente")
        self.assertEqual(st["adaptador_http_oficial"], "bloqueado")
        self.assertEqual(st["perfil_cripto_aprovado"], "bloqueado")

    def test_test_or_demo_env_rejected(self):
        for v in ("test", "demo"):
            st = {i["item"]: i["status"] for i in json.loads(run({**FULL, "APP_ENV": v}, "--json").stdout)["itens"]}
            self.assertEqual(st["APP_ENV"], "invalido")

    def test_production_flag_rejected_and_empty_env_blocked(self):
        st = {i["item"]: i["status"] for i in json.loads(run({**FULL, "NFSE_PRODUCTION_ENABLED": "true"}, "--json").stdout)["itens"]}
        self.assertEqual(st["NFSE_PRODUCTION_ENABLED"], "invalido")
        self.assertEqual(run({}).returncode, 1)
        self.assertEqual(run({}, "--bad").returncode, 2)


if __name__ == "__main__":
    unittest.main()
