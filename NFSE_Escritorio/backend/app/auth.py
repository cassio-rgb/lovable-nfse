"""Sessão verificável e autorização por empresa revalidada a cada ação."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote, urlsplit, urlunsplit

import jwt
from jwt import PyJWKClient


class AcessoNegado(Exception):
    """Mensagem genérica: não revela se o recurso existe (M05)."""

    def __init__(self) -> None:
        super().__init__("Conteúdo indisponível")


@dataclass(frozen=True)
class Principal:
    user_id: str
    papel: str  # cliente | escritorio


class MembershipStore:
    durable = False  # somente teste/demonstração
    """Vínculos atuais. Papel global não concede todas as empresas."""

    def __init__(self) -> None:
        self._m: dict[tuple[str, str], set[str]] = {}

    def grant(self, user_id: str, empresa_id: str, perms: set[str]) -> None:
        self._m[(user_id, empresa_id)] = set(perms)

    def revoke(self, user_id: str, empresa_id: str) -> None:
        self._m.pop((user_id, empresa_id), None)

    def empresas(self, user_id: str) -> list[str]:
        return [e for (u, e) in self._m if u == user_id]

    def require(self, p: Principal, empresa_id: str, perm: str) -> None:
        if perm not in self._m.get((p.user_id, empresa_id), set()):
            raise AcessoNegado()


class SupabaseIdentityVerifier:
    """Valida access tokens do Supabase Auth via JWKS público.

    Somente app_metadata controlado pelo servidor pode elevar o papel para
    escritorio. user_metadata nunca participa de autorização.
    """

    def __init__(self, issuer: str, audience: str, jwks_client: PyJWKClient | None = None) -> None:
        issuer = issuer.rstrip("/")
        if not issuer.startswith("https://") or not audience:
            raise ValueError("Configuração de identidade inválida")
        self.issuer = issuer
        self.audience = audience
        self.jwks_url = f"{issuer}/.well-known/jwks.json"
        self._jwks = jwks_client or PyJWKClient(self.jwks_url)

    def verify(self, token: str) -> dict:
        if not token or token.count(".") != 2:
            raise ValueError("Token inválido")
        signing_key = self._jwks.get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256", "ES256"],
            audience=self.audience,
            issuer=self.issuer,
            options={"require": ["exp", "iss", "sub", "aud"]},
        )
        if claims.get("role") != "authenticated" or claims.get("is_anonymous") is True:
            raise ValueError("Sessão não autenticada")

        app_metadata = claims.get("app_metadata")
        papel = app_metadata.get("papel") if isinstance(app_metadata, dict) else None
        if papel not in {"cliente", "escritorio"}:
            papel = "cliente"
        return {**claims, "papel": papel}

    def login_url(self, retorno: str) -> str:
        """Leva para a tela de login do próprio frontend, que usa Supabase Auth."""
        p = urlsplit(retorno)
        origin = urlunsplit((p.scheme, p.netloc, "", "", ""))
        return f"{origin}/login?retorno={quote(retorno, safe='')}"


def principal_from_claims(claims: dict) -> Principal:
    """claims devem vir de IdentityVerifier.verify (assinatura/iss/aud/exp verificados)."""
    sub = claims.get("sub")
    if not sub:
        raise AcessoNegado()
    return Principal(user_id=str(sub), papel=str(claims.get("papel", "cliente")))


@dataclass(frozen=True)
class Company:
    id: str
    razao_social: str
    cnpj: str
    municipio: str


class CompanyDirectory:
    durable = False  # somente teste/demonstração

    def __init__(self) -> None:
        self._c: dict[str, Company] = {}

    def add(self, c: Company) -> None:
        self._c[c.id] = c

    def get(self, cid: str) -> Company | None:
        return self._c.get(cid)
