"""Testes offline do Storage S3 privado; nenhuma rede ou credencial real."""
from __future__ import annotations

import io
import unittest

from app.auth import AcessoNegado
from app.documents import SupabaseS3Storage


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], dict] = {}
        self.get_calls = 0

    def put_object(self, **kwargs):
        self.objects[(kwargs["Bucket"], kwargs["Key"])] = {
            "Body": bytes(kwargs["Body"]),
            "Metadata": dict(kwargs.get("Metadata") or {}),
        }
        return {"ETag": "fake"}

    def get_object(self, **kwargs):
        self.get_calls += 1
        obj = self.objects[(kwargs["Bucket"], kwargs["Key"])]
        return {
            "Body": io.BytesIO(obj["Body"]),
            "Metadata": dict(obj["Metadata"]),
        }


def storage(fake: FakeS3 | None = None) -> SupabaseS3Storage:
    return SupabaseS3Storage(
        "https://storage.example.test/storage/v1/s3",
        "us-test-1",
        "fake-access",
        "fake-secret",
        "nfse-documentos",
        client=fake or FakeS3(),
    )


class StoragePrivado(unittest.TestCase):
    def test_round_trip_and_integrity_metadata(self):
        fake = FakeS3()
        s = storage(fake)
        self.assertTrue(s.durable)
        ref, sha = s.put("empresa-a", "nfse", b"<NFSe/>")
        self.assertTrue(ref.startswith("empresa-a/nfse/"))
        saved = fake.objects[("nfse-documentos", ref)]
        self.assertEqual(saved["Metadata"]["sha256"], sha)
        self.assertEqual(saved["Metadata"]["company-id"], "empresa-a")
        self.assertEqual(s.get("empresa-a", ref), b"<NFSe/>")

    def test_cross_company_reference_denied_before_remote_call(self):
        fake = FakeS3()
        s = storage(fake)
        ref, _ = s.put("empresa-a", "nfse", b"x")
        with self.assertRaises(AcessoNegado):
            s.get("empresa-b", ref)
        self.assertEqual(fake.get_calls, 0)

    def test_tamper_is_detected(self):
        fake = FakeS3()
        s = storage(fake)
        ref, _ = s.put("empresa-a", "nfse", b"original")
        fake.objects[("nfse-documentos", ref)]["Body"] = b"alterado"
        with self.assertRaisesRegex(RuntimeError, "Integridade"):
            s.get("empresa-a", ref)

    def test_rejects_unsafe_path_segments(self):
        s = storage()
        for empresa, kind in (("../a", "nfse"), ("empresa-a", "../nfse"), ("empresa/a", "nfse")):
            with self.assertRaises(ValueError):
                s.put(empresa, kind, b"x")

    def test_requires_https_and_complete_configuration(self):
        with self.assertRaises(ValueError):
            SupabaseS3Storage("http://example.test", "us-test-1", "a", "s", "b", client=FakeS3())
        with self.assertRaises(ValueError):
            SupabaseS3Storage("https://example.test", "", "a", "s", "b", client=FakeS3())


if __name__ == "__main__":
    unittest.main()
