"""Ponto de entrada de produção/homologação (`uvicorn app.main:app`).

Persistência durável existe (`app/pg.py`: PostgresRepository, PgMemberships, PgCompanies,
PgReleases). Ainda NÃO existem: provedor de identidade real (verificador de sessão e
emissão do cookie), storage privado durável e cofre de certificados. A inicialização,
portanto, falha de forma explícita — nunca cai para dependências em memória.
"""
from __future__ import annotations

from . import config
from .config import ConfigError


def create_production_app():
    settings = config.load()  # valida variáveis obrigatórias (inclui DATABASE_URL)
    from .pg import PgCompanies, PgMemberships, PgReleases, PostgresRepository

    PostgresRepository(settings.database_url), PgMemberships(settings.database_url)
    PgCompanies(settings.database_url), PgReleases(settings.database_url)
    raise ConfigError(
        "Infraestrutura incompleta: provedor de identidade, storage privado e cofre não estão conectados. "
        f"A API não inicia (APP_ENV={settings.app_env})."
    )


app = create_production_app()
