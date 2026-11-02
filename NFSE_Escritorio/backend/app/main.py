"""Ponto de entrada da API fiscal em homologação/produção.

A API usa apenas dependências duráveis (PostgreSQL, Supabase Auth e Storage).
O processo da API não carrega certificado nem adaptador fiscal; transmissão externa
permanece responsabilidade exclusiva do worker e continua fail-closed.
"""
from __future__ import annotations

from . import config
from .api import ApiSettings, Deps, create_app
from .auth import SupabaseIdentityVerifier
from .config import ConfigError
from .documents import SupabaseS3Storage
from .pg import PgCompanies, PgMemberships, PgReleases, PostgresRepository


def create_production_app():
    settings = config.load()

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

    deps = Deps(
        settings=ApiSettings(
            app_env=settings.app_env,
            allowed_origins=settings.cors_origins,
            production_enabled=settings.nfse_production_enabled,
            import_max_bytes=settings.import_max_bytes,
            import_max_rows=settings.import_max_rows,
        ),
        repo=PostgresRepository(settings.database_url),
        members=PgMemberships(settings.database_url),
        companies=PgCompanies(settings.database_url),
        releases=PgReleases(settings.database_url),
        storage=storage,
        identity=identity,
    )
    return create_app(deps)


app = create_production_app()
