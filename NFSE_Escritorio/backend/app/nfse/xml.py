"""Compatibilidade: a geração/validação/assinatura vivem em `dps.py`, `secure_xml.py` e `signing.py`."""
from __future__ import annotations

from .dps import build_dps, validar_xml  # noqa: F401
from .signing import Assinador, verificar  # noqa: F401
