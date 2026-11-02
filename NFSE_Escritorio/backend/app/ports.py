"""Contratos de infraestrutura (cofre, storage, identidade, integração fiscal)."""
from __future__ import annotations

from typing import Protocol

from .domain.models import FiscalResult, Emissao


class Vault(Protocol):
    def certificate_for(self, empresa_id: str, ambiente: str) -> bytes: ...


class Storage(Protocol):
    def put(self, empresa_id: str, kind: str, data: bytes) -> tuple[str, str]: ...  # (ref, sha256)
    def get(self, empresa_id: str, ref: str) -> bytes: ...


class IdentityVerifier(Protocol):
    def verify(self, token: str) -> dict: ...  # claims verificadas (iss, aud, exp, assinatura)


class FiscalAdapter(Protocol):
    def submit(self, emissao: Emissao) -> FiscalResult: ...
    def lookup(self, emissao: Emissao) -> FiscalResult: ...


class FiscalParameters(Protocol):
    """Parâmetros fiscais explícitos por empresa/operação/ambiente (regime, códigos, município, série).
    Sem implementação durável ainda: cadastro depende de responsável fiscal; nunca inferir."""
    def parametros(self, empresa_id: str, operacao: str, ambiente) -> "object | None": ...
