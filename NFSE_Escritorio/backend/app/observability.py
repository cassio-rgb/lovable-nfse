"""Logs estruturados UTC com correlação; campos sensíveis são redigidos."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

SENSITIVE = {"certificado", "senha", "password", "token", "authorization", "dados", "snapshot", "tomador_documento"}
log = logging.getLogger("nfse")


def redact(fields: dict) -> dict:
    return {k: ("[redigido]" if k.lower() in SENSITIVE else v) for k, v in fields.items()}


def event(categoria: str, correlation_id: str, **fields) -> str:
    rec = {"ts": datetime.now(timezone.utc).isoformat(), "categoria": categoria, "correlation_id": correlation_id, **redact(fields)}
    line = json.dumps(rec, ensure_ascii=False, default=str)
    log.info(line)
    return line
