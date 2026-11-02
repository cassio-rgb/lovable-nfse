"""Liberação explícita por empresa/operação/ambiente. Nenhuma liberação inicial (M04)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Release:
    empresa_id: str
    operacao: str
    ambiente: str
    versao: int
    evidencia: str
    autor: str


class OperacaoNaoLiberada(Exception):
    def __init__(self) -> None:
        super().__init__(
            "Operação não liberada para esta empresa e ambiente. O Escritório deve registrar a liberação com evidência fiscal validada."
        )


class ReleaseRegistry:
    durable = False  # somente teste/demonstração
    def __init__(self) -> None:
        self._r: dict[tuple[str, str, str], Release] = {}

    def register(self, r: Release) -> None:
        if not r.evidencia.strip():
            raise ValueError("Liberação exige evidência")
        self._r[(r.empresa_id, r.operacao, r.ambiente)] = r

    def require(self, empresa_id: str, operacao: str, ambiente: str) -> Release:
        r = self._r.get((empresa_id, operacao, ambiente))
        if not r:
            raise OperacaoNaoLiberada()
        return r

    def for_company(self, empresa_id: str) -> list[Release]:
        return [r for (e, _, _), r in self._r.items() if e == empresa_id]
