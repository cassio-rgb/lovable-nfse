#!/usr/bin/env python3
"""Preflight de ativação (homologação) — SOMENTE LEITURA.

Uso:  python3 scripts/preflight.py [--json]

- Só biblioteca padrão. Não importa `app.main` nem qualquer módulo do serviço.
- Não acessa rede, banco, cofre nem segredos; não altera arquivos; não roda migrações.
- Lê apenas a PRESENÇA de variáveis de ambiente (nunca imprime valores) e inspeciona o
  código-fonte como texto para saber se adaptadores existem e se o adaptador fiscal está bloqueado.
- "presente_nao_validado" significa apenas que a variável existe — não que o provedor funciona.
- Exit 0 somente se tudo estiver pronto; 1 se não pronto; 2 em erro de uso.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "backend" / "app"

OK, PRESENTE, AUSENTE, INVALIDO, BLOQUEADO = "ok", "presente_nao_validado", "ausente", "invalido", "bloqueado"


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


def check_config(env: dict[str, str]) -> list[dict]:
    out: list[dict] = []

    def item(nome, status, motivo):
        out.append({"grupo": "config", "item": nome, "status": status, "motivo": motivo})

    app_env = env.get("APP_ENV", "")
    if not app_env:
        item("APP_ENV", AUSENTE, "obrigatória")
    elif app_env.lower() in {"test", "demo", "dev", "local"}:
        item("APP_ENV", INVALIDO, "valor de teste/demonstração não serve para homologação")
    else:
        item("APP_ENV", PRESENTE, "definida; não validada")

    nfse = env.get("NFSE_ENVIRONMENT", "")
    if not nfse:
        item("NFSE_ENVIRONMENT", AUSENTE, "obrigatória")
    elif nfse != "producao_restrita":
        item("NFSE_ENVIRONMENT", INVALIDO, "homologação exige producao_restrita")
    else:
        item("NFSE_ENVIRONMENT", OK, "producao_restrita")

    if env.get("NFSE_PRODUCTION_ENABLED", "false").lower() == "true":
        item("NFSE_PRODUCTION_ENABLED", INVALIDO, "produção deve permanecer desabilitada na homologação")
    else:
        item("NFSE_PRODUCTION_ENABLED", OK, "desabilitada")

    for k, why in (("IDENTITY_ISSUER", "emissor do provedor de identidade"),
                   ("IDENTITY_AUDIENCE", "audiência esperada nos tokens"),
                   ("DATABASE_URL", "papel nfse_api, nunca superusuário"),
                   ("WORKER_DATABASE_URL", "papel do worker separado do API"),
                   ("CERTIFICATE_REFERENCE", "referência no cofre, nunca o arquivo"),
                   ("CORS_ORIGINS", "origens permitidas do frontend")):
        item(k, PRESENTE if env.get(k) else AUSENTE, (why + "; presença não é validação") if env.get(k) else why)

    if env.get("APP_ENV", "").lower() not in {"", "test"} and env.get("TEST_DATABASE_URL"):
        item("TEST_DATABASE_URL", INVALIDO, "não deve existir fora de testes (testes recriam schema)")
    return out


def check_code() -> list[dict]:
    out: list[dict] = []

    def item(nome, status, motivo):
        out.append({"grupo": "adaptadores", "item": nome, "status": status, "motivo": motivo})

    main = _read(APP / "main.py")
    incompleto = "Infraestrutura incompleta" in main
    for nome, marcador in (("verificador_identidade", "IdentityVerifier"), ("storage_privado_duravel", "Storage"),
                           ("cofre_certificados", "Vault")):
        implementado = any(f"({marcador})" in _read(p) or f"({marcador}):" in _read(p)
                           for p in APP.rglob("*.py") if p.name != "ports.py")
        st = AUSENTE if (incompleto or not implementado) else PRESENTE
        item(nome, st, "não implementado/conectado; app.main recusa iniciar" if st == AUSENTE else "implementação encontrada; não validada")

    item("parametros_fiscais_duraveis", AUSENTE if "FiscalParameters" not in "".join(
        _read(p) for p in APP.rglob("*.py") if p.name != "ports.py") else PRESENTE,
         "cadastro explícito por empresa/operação não implementado")

    client = _read(APP / "nfse" / "client.py")
    item("adaptador_http_oficial", BLOQUEADO if "raise AdaptadorFiscalBloqueado()" in client else PRESENTE,
         "contrato HTTP oficial não capturado; submit/lookup falham fechados")

    sig = _read(APP / "nfse" / "signing.py")
    confirmados = sig.count('"confirmado_fonte_oficial"') - 1  # descontar a constante
    item("perfil_cripto_aprovado", OK if confirmados > 0 else BLOQUEADO,
         "nenhum perfil com fonte oficial vigente" if confirmados <= 0 else "perfil marcado como confirmado; revisar evidência")

    ev = _read(ROOT / "docs" / "nfse-integration-evidence.md")
    item("xsd_producao_serie", BLOQUEADO if "Defeito no XSD de produção" in ev else PRESENTE,
         "TSSerieDPS do XSD de produção v1.01 não aceita série real")
    item("smoke_producao_restrita", BLOQUEADO, "não executado; depende de todos os itens acima e de certificado autorizado")
    return out


def main(argv: list[str]) -> int:
    if any(a not in ("--json",) for a in argv):
        print("uso: python3 scripts/preflight.py [--json]", file=sys.stderr)
        return 2
    itens = check_config(dict(os.environ)) + check_code()
    pronto = all(i["status"] == OK for i in itens)
    if "--json" in argv:
        print(json.dumps({"pronto": pronto, "itens": itens}, ensure_ascii=False, indent=2))
    else:
        for i in itens:
            print(f"[{i['status']:<22}] {i['grupo']}/{i['item']}: {i['motivo']}")
        print(f"\nRESULTADO: {'PRONTO' if pronto else 'NÃO PRONTO (BLOQUEADO)'} — preflight não valida provedores nem transmite.")
    return 0 if pronto else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
