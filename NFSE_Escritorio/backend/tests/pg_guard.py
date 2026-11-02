"""Guardas do banco de teste PostgreSQL — validadas ANTES de qualquer conexão/mutação.

Regras: TEST_DATABASE_URL explícito; dbname exatamente `nfse_test` ou `nfse_test_<sufixo>`;
host local (unix socket absoluto, localhost, 127.0.0.1, ::1); reset destrutivo do schema
`public` só com NFSE_PG_ALLOW_SCHEMA_RESET igual ao valor exato abaixo.
"""
import re

RESET_FLAG = "NFSE_PG_ALLOW_SCHEMA_RESET"
RESET_VALUE = "nfse_test_reset_public"
_DBNAME = re.compile(r"^nfse_test(_[a-z0-9]+)?$")
_LOCAL = {"localhost", "127.0.0.1", "::1"}


class UnsafeTestDatabase(RuntimeError):
    pass


def check(dsn: str, env: dict) -> dict:
    if not dsn:
        raise UnsafeTestDatabase("TEST_DATABASE_URL ausente")
    from psycopg.conninfo import conninfo_to_dict  # parse puro, não conecta

    info = conninfo_to_dict(dsn)
    db = info.get("dbname") or ""
    if not _DBNAME.match(db):
        raise UnsafeTestDatabase(f"dbname {db!r} recusado: use nfse_test ou nfse_test_<sufixo>")
    hosts = [h for h in (info.get("host") or "").split(",")]
    if not hosts or any(not (h.startswith("/") or h in _LOCAL) for h in hosts):
        raise UnsafeTestDatabase("host recusado: somente unix socket ou loopback")
    if env.get(RESET_FLAG) != RESET_VALUE:
        raise UnsafeTestDatabase(f"defina {RESET_FLAG}={RESET_VALUE} para autorizar o reset do schema")
    return info
