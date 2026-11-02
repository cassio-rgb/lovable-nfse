"""Sessão verificável e autorização por empresa revalidada a cada ação."""
from __future__ import annotations

from dataclasses import dataclass


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
