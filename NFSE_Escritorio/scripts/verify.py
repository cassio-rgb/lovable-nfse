#!/usr/bin/env python3
"""Verificação do projeto. Cada modo falha se algum check obrigatório não puder rodar.

  --mode local       testes Python (memória + API), vitest, typecheck, build, E2E (preview em :8080)
  --mode postgres    testes de integração PostgreSQL; exige TEST_DATABASE_URL (nfse_test[_sufixo], host local) e NFSE_PG_ALLOW_SCHEMA_RESET=nfse_test_reset_public
  --mode restricted  smoke OFICIAL em produção restrita; exige credenciais; nunca usa simulador
"""
import argparse
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY_LOCAL = ["tests.test_guards", "tests.test_domain", "tests.test_imports", "tests.test_isolation", "tests.test_emissions",
            "tests.test_contract", "tests.test_interop", "tests.test_preflight", "tests.test_certificado", "tests.test_escritorio",
            "tests.test_api", "tests.test_auth", "tests.test_catalogos"]
results: list[tuple[str, str]] = []


def check(name: str, cmd: list[str], cwd: Path = ROOT, env: dict | None = None) -> None:
    print(f"\n=== {name}: {' '.join(cmd)}", flush=True)
    rc = subprocess.call(cmd, cwd=cwd, env={**os.environ, **(env or {})})
    results.append((name, "PASS" if rc == 0 else f"FAIL (exit {rc})"))


def missing(name: str, why: str) -> None:
    print(f"\n=== {name}: NÃO EXECUTADO — {why}", flush=True)
    results.append((name, f"NOT RUN ({why})"))


def need_tool(name: str, tool: str) -> bool:
    if shutil.which(tool):
        return True
    missing(name, f"'{tool}' ausente")
    return False


def need_py(name: str, *mods: str) -> bool:
    for m in mods:
        try:
            __import__(m)
        except ImportError:
            missing(name, f"módulo Python '{m}' ausente")
            return False
    return True


def xmlsec1() -> str | None:
    """Verificador XMLDSIG independente (libxmlsec). PATH, XMLSEC1 ou nixpkgs#xmlsec."""
    found = os.environ.get("XMLSEC1") or shutil.which("xmlsec1")
    if not found and shutil.which("nix"):
        out = subprocess.run(["nix", "build", "nixpkgs#xmlsec", "--no-link", "--print-out-paths"],
                             capture_output=True, text=True, timeout=300).stdout.split()
        found = f"{out[0]}/bin/xmlsec1" if out else None
    return found if found and os.path.exists(found) else None


def local() -> None:
    xs = xmlsec1()
    if not xs:
        missing("python-unit+api", "xmlsec1 ausente: verificação independente de assinatura obrigatória")
    elif need_py("python-unit+api", "fastapi", "httpx", "openpyxl", "multipart", "lxml", "cryptography"):
        check("python-unit+api", [sys.executable, "-m", "unittest", *PY_LOCAL, "-v"], cwd=ROOT / "backend",
              env={"XMLSEC1": xs})
    if need_tool("vitest", "bunx"):
        check("vitest", ["bunx", "vitest", "run"])
    if need_tool("typecheck", "bunx"):
        check("typecheck", ["bunx", "tsc", "--noEmit"])
    if need_tool("build", "bun"):
        check("build", ["bun", "run", "build"])
    try:
        urllib.request.urlopen("http://localhost:8080/", timeout=10)
        if need_py("e2e", "playwright"):
            check("e2e", [sys.executable, "tests/e2e/nfse_flow.py"])
    except OSError as exc:
        missing("e2e", f"preview em http://localhost:8080 inacessível ({exc})")


def postgres() -> None:
    if not os.environ.get("TEST_DATABASE_URL"):
        missing("postgres", "TEST_DATABASE_URL não definido (use scripts/pg_ephemeral.sh start)")
        return
    if need_py("postgres", "psycopg", "fastapi"):
        check("postgres", [sys.executable, "-m", "unittest", "tests.test_pg", "-v"], cwd=ROOT / "backend")


def restricted() -> None:
    needed = ["NFSE_SMOKE_ENABLED", "NFSE_BASE_URL", "CERTIFICATE_REFERENCE", "PILOT_COMPANY_BARIRI", "PILOT_COMPANY_PEDERNEIRAS"]
    absent = [k for k in needed if not os.environ.get(k)]
    if absent:
        missing("smoke-oficial", f"faltam {', '.join(absent)}; nenhuma simulação substitui este modo")
    else:
        missing("smoke-oficial", "adaptador oficial bloqueado até o spike (docs/nfse-integration-evidence.md)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["local", "postgres", "restricted"], required=True)
    mode = ap.parse_args().mode
    {"local": local, "postgres": postgres, "restricted": restricted}[mode]()
    print("\n=== RESUMO")
    for n, r in results:
        print(f"{n:20} {r}")
    sys.exit(0 if results and all(r == "PASS" for _, r in results) else 1)
