"""Testes do provedor de identidade Supabase sem acesso à rede."""
from __future__ import annotations

import time
import unittest
from types import SimpleNamespace

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from app.auth import SupabaseIdentityVerifier


ISSUER = "https://projeto-exemplo.supabase.co/auth/v1"
AUDIENCE = "authenticated"


class FakeJwks:
    def __init__(self, key):
        self.key = key

    def get_signing_key_from_jwt(self, _token):
        return SimpleNamespace(key=self.key)


class SupabaseIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.public = cls.private.public_key()

    def token(self, **overrides):
        now = int(time.time())
        claims = {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": "11111111-1111-1111-1111-111111111111",
            "exp": now + 300,
            "iat": now,
            "role": "authenticated",
            "is_anonymous": False,
            "app_metadata": {"papel": "escritorio"},
            "user_metadata": {},
        }
        claims.update(overrides)
        return jwt.encode(claims, self.private, algorithm="RS256", headers={"kid": "teste"})

    def verifier(self):
        return SupabaseIdentityVerifier(ISSUER, AUDIENCE, FakeJwks(self.public))

    def test_valid_token_and_server_controlled_role(self):
        claims = self.verifier().verify(self.token())
        self.assertEqual(claims["sub"], "11111111-1111-1111-1111-111111111111")
        self.assertEqual(claims["papel"], "escritorio")

    def test_user_metadata_cannot_elevate_role(self):
        token = self.token(app_metadata={}, user_metadata={"papel": "escritorio"})
        self.assertEqual(self.verifier().verify(token)["papel"], "cliente")

    def test_wrong_audience_rejected(self):
        with self.assertRaises(jwt.InvalidAudienceError):
            self.verifier().verify(self.token(aud="outro"))

    def test_expired_token_rejected(self):
        with self.assertRaises(jwt.ExpiredSignatureError):
            self.verifier().verify(self.token(exp=int(time.time()) - 1))

    def test_anonymous_token_rejected(self):
        with self.assertRaises(ValueError):
            self.verifier().verify(self.token(is_anonymous=True))


if __name__ == "__main__":
    unittest.main()
