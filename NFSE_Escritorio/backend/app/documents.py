"""Storage privado com vínculo por empresa e integridade SHA-256."""
from __future__ import annotations

import hashlib
import uuid

from .auth import AcessoNegado


class MemoryStorage:
    durable = False  # somente teste/demonstração
    def __init__(self) -> None:
        self._o: dict[str, tuple[str, bytes, str]] = {}

    def put(self, empresa_id: str, kind: str, data: bytes) -> tuple[str, str]:
        ref = f"{empresa_id}/{kind}/{uuid.uuid4().hex}"
        h = hashlib.sha256(data).hexdigest()
        self._o[ref] = (empresa_id, data, h)
        return ref, h

    def get(self, empresa_id: str, ref: str) -> bytes:
        o = self._o.get(ref)
        if not o or o[0] != empresa_id:
            raise AcessoNegado()
        if hashlib.sha256(o[1]).hexdigest() != o[2]:
            raise RuntimeError("Integridade do artefato violada")
        return o[1]
