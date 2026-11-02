#!/usr/bin/env python3
"""Inspeção LOCAL e somente leitura de um certificado A1 (.pfx/.p12) no computador do próprio usuário.

Uso:  python3 scripts/inspecionar_certificado.py CAMINHO_DO_ARQUIVO.pfx
A senha é pedida de forma oculta (getpass); não é aceita por argumento nem variável de ambiente.

Não acessa rede, não grava arquivos, não envia DPS e não altera nada no aplicativo.
Mostra apenas status sanitizado. Cadeia ICP-Brasil, revogação, autorização (procuração) e API
NÃO são testadas aqui; por isso o resultado é sempre "NÃO PRONTO" para emissão.
Requer o pacote `cryptography` (dependência já usada pelo serviço fiscal).
"""
from __future__ import annotations

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0].startswith("-"):
        print("Uso: python3 scripts/inspecionar_certificado.py CAMINHO_DO_ARQUIVO.pfx")
        print("A senha é solicitada de forma oculta; não a informe na linha de comando.")
        return 64
    from app.nfse.certificado import MAX_PFX, CertificadoInvalido, SenhaA1, carregar_a1, resumo_sanitizado
    p = Path(argv[0])
    try:
        if not p.is_file() or p.stat().st_size > MAX_PFX:
            raise CertificadoInvalido("x")
        dados = p.read_bytes()
    except Exception:  # noqa: BLE001
        print("ERRO: arquivo não encontrado, ilegível ou acima do limite de tamanho.")
        return 1
    senha = SenhaA1(getpass.getpass("Senha do certificado (não será exibida): "))
    try:
        a1 = carregar_a1(dados, senha)
    except CertificadoInvalido as e:
        print(f"ERRO: {e}.")
        return 1
    except Exception:  # noqa: BLE001
        print("ERRO: falha inesperada ao ler o certificado (detalhes omitidos por segurança).")
        return 1
    finally:
        del senha
    r = resumo_sanitizado(a1)
    print("Inspeção local do certificado A1 (somente estrutura)")
    print(f"- Estrutura local (chave↔certificado, RSA, validade): {r['estrutura_local'].upper()}")
    print(f"- Algoritmo: {r['algoritmo']}  | Válido até: {r['valido_ate']}")
    print(f"- CNPJ do titular (ICP-Brasil OID 2.16.76.1.3.3): {r['cnpj_titular'] or 'AUSENTE'}")
    print("- Cadeia ICP-Brasil: NÃO VERIFICADA | Revogação: NÃO VERIFICADA")
    print("- Procuração/representação no governo: NÃO VERIFICADA")
    print("- API: NÃO TESTADA")
    if not r["cnpj_titular"]:
        print("Resultado: NÃO PRONTO — o certificado não traz CNPJ ICP-Brasil identificável.")
    else:
        print("Resultado: NÃO PRONTO — faltam cadeia/revogação, autorização oficial, cofre e contrato da API.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
