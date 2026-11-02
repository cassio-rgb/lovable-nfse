import importlib
import os
import sys
import unittest
from unittest.mock import patch

from fastapi import FastAPI

ENV = {
    "APP_ENV": "homologacao",
    "NFSE_ENVIRONMENT": "producao_restrita",
    "NFSE_PRODUCTION_ENABLED": "false",
    "IDENTITY_ISSUER": "https://example.supabase.co/auth/v1",
    "IDENTITY_AUDIENCE": "authenticated",
    "DATABASE_URL": "postgresql://api.example/nfse",
    "WORKER_DATABASE_URL": "postgresql://worker.example/nfse",
    "STORAGE_S3_ENDPOINT": "https://example.storage.supabase.co/storage/v1/s3",
    "STORAGE_S3_REGION": "us-east-1",
    "STORAGE_S3_ACCESS_KEY_ID": "access",
    "STORAGE_S3_SECRET_ACCESS_KEY": "secret",
    "STORAGE_CONTAINER": "nfse-documentos",
    "CORS_ORIGINS": "https://app.example",
}


class MainBootstrap(unittest.TestCase):
    def test_api_bootstrap_without_certificate_or_fiscal_adapter(self):
        with patch.dict(os.environ, ENV, clear=True):
            sys.modules.pop("app.main", None)
            mod = importlib.import_module("app.main")
            self.assertIsInstance(mod.app, FastAPI)
            paths = {route.path for route in mod.app.routes}
            self.assertIn("/v1/sessao", paths)
            self.assertIn("/v1/auth/session", paths)

    def test_fiscal_adapter_remains_blocked(self):
        from app.nfse.client import AdaptadorFiscalBloqueado, NationalNfseClient
        from app.domain.models import Ambiente
        client = NationalNfseClient(Ambiente.PRODUCAO_RESTRITA)
        with self.assertRaises(AdaptadorFiscalBloqueado):
            client.submit(None)


if __name__ == "__main__":
    unittest.main()
