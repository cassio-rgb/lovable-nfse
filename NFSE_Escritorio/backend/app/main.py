"""Ponto de entrada de produção/homologação (`uvicorn app.main:app`).

Persistência durável e verificação de identidade Supabase existem. Storage privado
durável e cofre de certificados ainda não estão conectados. A inicialização falha
de forma explícita enquanto essas dependências faltarem; nunca cai para memória.
"""
from __future__ import annotations

from . import config
from .auth import SupabaseIdentityVerifier
from .config import ConfigError


def create_production_app():
    settings = config.load()
    from .pg import PgCompanies, PgMemberships, PgReleases, PostgresRepository

    identity = SupabaseIdentityVerifier(settings.identity_issuer, settings.identity_audience)
    PostgresRepository(settings.database_url), PgMemberships(settings.database_url)
    PgCompanies(settings.database_url), PgReleases(settings.database_url)
    _ = identity  # identidade real conectada; demais adaptadores ainda bloqueiam o bootstrap

    raise ConfigError(
        "Infraestrutura incompleta: storage privado e cofre de certificados ainda não estão conectados. "
        f"A API não inicia (APP_ENV={settings.app_env})."
    )


app = create_production_app()
