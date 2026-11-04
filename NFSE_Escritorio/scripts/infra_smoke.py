#!/usr/bin/env python3
"""Smoke test REAL da infraestrutura de homologação.

Testa somente:
- PostgreSQL da API;
- PostgreSQL do worker;
- JWKS do Supabase Auth;
- Storage S3 privado (put/get/delete de objeto temporário).

NÃO lê certificado, NÃO chama a API Nacional de NFS-e e NÃO transmite documento fiscal.
Nunca imprime DSNs, senhas, access keys ou secret keys.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from urllib.request import Request, urlopen

import boto3
import psycopg
from botocore.client import Config

ROOT_REQUIRED = (
    "DATABASE_URL",
    "WORKER_DATABASE_URL",
    "IDENTITY_ISSUER",
    "STORAGE_S3_ENDPOINT",
    "STORAGE_S3_REGION",
    "STORAGE_S3_ACCESS_KEY_ID",
    "STORAGE_S3_SECRET_ACCESS_KEY",
    "STORAGE_CONTAINER",
)


class SmokeError(RuntimeError):
    pass


def _require_env() -> dict[str, str]:
    missing = [name for name in ROOT_REQUIRED if not os.environ.get(name)]
    if missing:
        raise SmokeError("Variáveis ausentes: " + ", ".join(missing))
    return {name: os.environ[name] for name in ROOT_REQUIRED}


def _db_error(label: str, exc: Exception) -> SmokeError:
    sqlstate = getattr(exc, "sqlstate", None)
    diag = getattr(exc, "diag", None)
    primary = getattr(diag, "message_primary", None) if diag else None
    detail = primary or str(exc).splitlines()[0]
    if len(detail) > 220:
        detail = detail[:217] + "..."
    suffix = f" SQLSTATE={sqlstate}" if sqlstate else ""
    return SmokeError(f"{label}: falha PostgreSQL ({type(exc).__name__}{suffix}) — {detail}")


def _check_db(label: str, dsn: str, expected_role: str) -> None:
    try:
        with psycopg.connect(dsn, connect_timeout=10) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select current_user,
                           coalesce(
                               (select rolsuper from pg_roles where rolname = current_user),
                               false
                           )
                    """
                )
                user, is_super = cur.fetchone()
                cur.execute("select pg_has_role(%s::name, 'MEMBER')", (expected_role,))
                has_expected_role = bool(cur.fetchone()[0])
    except Exception as exc:
        raise _db_error(label, exc) from exc

    if is_super:
        raise SmokeError(f"{label}: conexão recusada — usuário é superusuário")
    if not has_expected_role:
        raise SmokeError(
            f"{label}: conectado como {user}, mas não herda o papel esperado {expected_role}"
        )
    print(
        f"[OK] {label}: conectado como {user}; não-superusuário; "
        f"herança {expected_role} confirmada"
    )


def _check_jwks(issuer: str) -> None:
    if not issuer.startswith("https://"):
        raise SmokeError("Auth JWKS: IDENTITY_ISSUER deve usar HTTPS")
    url = issuer.rstrip("/") + "/.well-known/jwks.json"
    try:
        req = Request(url, headers={"Accept": "application/json", "User-Agent": "nfse-infra-smoke/1"})
        with urlopen(req, timeout=10) as response:
            if response.status != 200:
                raise SmokeError(f"Auth JWKS: HTTP {response.status}")
            data = json.loads(response.read().decode("utf-8"))
    except SmokeError:
        raise
    except Exception as exc:
        raise SmokeError(f"Auth JWKS: falha ao consultar endpoint ({type(exc).__name__})") from exc

    keys = data.get("keys") if isinstance(data, dict) else None
    if not isinstance(keys, list) or not keys:
        raise SmokeError("Auth JWKS: endpoint respondeu sem chaves")
    if not all(isinstance(k, dict) and k.get("kid") and k.get("kty") for k in keys):
        raise SmokeError("Auth JWKS: conjunto de chaves incompleto")
    print(f"[OK] Auth JWKS: endpoint válido com {len(keys)} chave(s)")


def _s3_client(env: dict[str, str]):
    endpoint = env["STORAGE_S3_ENDPOINT"]
    if not endpoint.startswith("https://"):
        raise SmokeError("Storage: endpoint deve usar HTTPS")
    return boto3.client(
        "s3",
        endpoint_url=endpoint.rstrip("/"),
        region_name=env["STORAGE_S3_REGION"],
        aws_access_key_id=env["STORAGE_S3_ACCESS_KEY_ID"],
        aws_secret_access_key=env["STORAGE_S3_SECRET_ACCESS_KEY"],
        config=Config(
            signature_version="s3v4",
            connect_timeout=10,
            read_timeout=15,
            retries={"max_attempts": 1, "mode": "standard"},
            s3={"addressing_style": "path"},
        ),
    )


def _check_storage(env: dict[str, str]) -> None:
    client = _s3_client(env)
    bucket = env["STORAGE_CONTAINER"]
    key = f"__infra_smoke__/probe/{uuid.uuid4().hex}.bin"
    payload = ("nfse-infra-smoke:" + uuid.uuid4().hex).encode("utf-8")
    sha = hashlib.sha256(payload).hexdigest()
    created = False

    try:
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=payload,
            ContentType="application/octet-stream",
            Metadata={"sha256": sha, "purpose": "infra-smoke"},
        )
        created = True
        obj = client.get_object(
            Bucket=bucket,
            Key=key,
            Range=f"bytes=0-{len(payload) - 1}",
        )
        body = obj["Body"].read(len(payload))
        meta = {str(k).lower(): str(v) for k, v in (obj.get("Metadata") or {}).items()}
        if body != payload:
            raise SmokeError("Storage: conteúdo lido difere do conteúdo gravado")
        if meta.get("sha256") != sha:
            raise SmokeError("Storage: metadata SHA-256 não confere")
        if hashlib.sha256(body).hexdigest() != sha:
            raise SmokeError("Storage: integridade SHA-256 falhou")
        print("[OK] Storage privado: gravação, leitura e SHA-256 conferidos")
    except SmokeError:
        raise
    except Exception as exc:
        raise SmokeError(f"Storage: falha S3 ({type(exc).__name__})") from exc
    finally:
        if created:
            try:
                client.delete_object(Bucket=bucket, Key=key)
                print("[OK] Storage privado: objeto temporário removido")
            except Exception as exc:
                raise SmokeError(
                    f"Storage: teste funcionou, mas limpeza do objeto temporário falhou ({type(exc).__name__})"
                ) from exc


def main() -> int:
    print("Smoke de infraestrutura — sem certificado e sem transmissão fiscal.")
    try:
        env = _require_env()
        _check_db("Banco API", env["DATABASE_URL"], "nfse_api")
        _check_db("Banco Worker", env["WORKER_DATABASE_URL"], "nfse_worker")
        _check_jwks(env["IDENTITY_ISSUER"])
        _check_storage(env)
    except SmokeError as exc:
        print(f"[FALHOU] {exc}", file=sys.stderr)
        return 1

    print("\nRESULTADO: INFRAESTRUTURA BÁSICA VALIDADA — nenhuma NFS-e foi transmitida.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
