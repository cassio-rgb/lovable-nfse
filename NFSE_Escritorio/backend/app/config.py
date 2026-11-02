"""Configuração validada. Sem segredo embutido e sem fallback para produção."""
from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    app_env: str
    nfse_environment: str
    nfse_production_enabled: bool
    nfse_base_url: str
    identity_issuer: str
    identity_audience: str
    database_url: str
    storage_s3_endpoint: str
    storage_s3_region: str
    storage_s3_access_key_id: str
    storage_s3_secret_access_key: str
    storage_container: str
    cors_origins: tuple[str, ...]
    job_lease_seconds: int = 120
    lookup_max_attempts: int = 5
    import_max_bytes: int = 5 * 1024 * 1024
    import_max_rows: int = 5000


def load(env: dict[str, str] | None = None) -> Settings:
    e = env if env is not None else dict(os.environ)
    required = ["APP_ENV", "NFSE_ENVIRONMENT", "IDENTITY_ISSUER", "IDENTITY_AUDIENCE", "DATABASE_URL",
                "STORAGE_S3_ENDPOINT", "STORAGE_S3_REGION", "STORAGE_S3_ACCESS_KEY_ID",
                "STORAGE_S3_SECRET_ACCESS_KEY", "STORAGE_CONTAINER"]
    missing = [k for k in required if not e.get(k)]
    if missing:
        raise ConfigError(f"Configuração ausente: {', '.join(missing)}")
    nfse_env = e["NFSE_ENVIRONMENT"]
    if nfse_env not in {"producao_restrita", "producao"}:
        raise ConfigError("NFSE_ENVIRONMENT inválido")
    prod_enabled = e.get("NFSE_PRODUCTION_ENABLED", "false").lower() == "true"
    if nfse_env == "producao" and not prod_enabled:
        raise ConfigError("Produção exige NFSE_PRODUCTION_ENABLED=true explícito")
    return Settings(
        app_env=e["APP_ENV"],
        nfse_environment=nfse_env,
        nfse_production_enabled=prod_enabled,
        nfse_base_url=e.get("NFSE_BASE_URL", ""),
        identity_issuer=e["IDENTITY_ISSUER"],
        identity_audience=e["IDENTITY_AUDIENCE"],
        database_url=e["DATABASE_URL"],
        storage_s3_endpoint=e["STORAGE_S3_ENDPOINT"],
        storage_s3_region=e["STORAGE_S3_REGION"],
        storage_s3_access_key_id=e["STORAGE_S3_ACCESS_KEY_ID"],
        storage_s3_secret_access_key=e["STORAGE_S3_SECRET_ACCESS_KEY"],
        storage_container=e["STORAGE_CONTAINER"],
        cors_origins=tuple(o for o in e.get("CORS_ORIGINS", "").split(",") if o),
        job_lease_seconds=int(e.get("JOB_LEASE_SECONDS", "120")),
        lookup_max_attempts=int(e.get("LOOKUP_MAX_ATTEMPTS", "5")),
    )
