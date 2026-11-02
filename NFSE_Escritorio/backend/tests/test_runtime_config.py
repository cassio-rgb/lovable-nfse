import unittest
from types import SimpleNamespace

from app import config, worker


class RuntimeConnectionSegregation(unittest.TestCase):
    def _env(self):
        return {
            "APP_ENV": "homologacao",
            "NFSE_ENVIRONMENT": "producao_restrita",
            "NFSE_PRODUCTION_ENABLED": "false",
            "IDENTITY_ISSUER": "https://example.supabase.co/auth/v1",
            "IDENTITY_AUDIENCE": "authenticated",
            "DATABASE_URL": "postgresql://api.example",
            "WORKER_DATABASE_URL": "postgresql://worker.example",
            "STORAGE_S3_ENDPOINT": "https://example.storage.supabase.co/storage/v1/s3",
            "STORAGE_S3_REGION": "us-east-1",
            "STORAGE_S3_ACCESS_KEY_ID": "access",
            "STORAGE_S3_SECRET_ACCESS_KEY": "secret",
            "STORAGE_CONTAINER": "nfse-documentos",
            "CORS_ORIGINS": "https://app.example",
        }

    def test_config_requires_and_preserves_separate_dsns(self):
        s = config.load(self._env())
        self.assertEqual(s.database_url, "postgresql://api.example")
        self.assertEqual(s.worker_database_url, "postgresql://worker.example")
        self.assertNotEqual(s.database_url, s.worker_database_url)

    def test_worker_bootstrap_uses_only_worker_dsn(self):
        s = SimpleNamespace(worker_database_url="postgresql://worker-only.example")
        repo = worker.create_worker_repository(s)
        self.assertEqual(repo.dsn, "postgresql://worker-only.example")


if __name__ == "__main__":
    unittest.main()
