"""Ponto de entrada de produção/homologação (`uvicorn app.main:app`).

Persistência durável e verificação de identidade Supabase existem. Storage privado
durável e cofre de certificados ainda não estão conectados. A inicialização falha
de forma explícita enquanto essas dependências faltarem; nunca cai para memória.
"""
from __future__ import annotations

from . import config
from .auth import SupabaseIdentityVerifier
from .config import ConfigError
from .documents import SupabaseS3Storage


def create_production_app():
    settings = config.load()
    from .pg import PgCompanies, PgMemberships, PgReleases, PostgresRepository

    try:
        identity = SupabaseIdentityVerifier(settings.identity_issuer, settings.identity_audience)
    except ValueError as exc:
        raise ConfigError("Configuração de identidade inválida") from exc
    storage = SupabaseS3Storage(
        settings.storage_s3_endpoint,
        settings.storage_s3_region,
        settings.storage_s3_access_key_id,
        settings.storage_s3_secret_access_key,
        settings.storage_container,
    )
    PostgresRepository(settings.database_url), PgMemberships(settings.database_url)
    PgCompanies(settings.database_url), PgReleases(settings.database_url)
    _ = identity, storage  # identidade e storage reais conectados; cofre ainda bloqueia o bootstrap

    raise ConfigError(
        "Infraestrutura incompleta: cofre de certificados ainda não está conectado. "
        f"A API não inicia (APP_ENV={settings.app_env})."
    )


app = create_production_app()
