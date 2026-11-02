"""Importação CSV/XLSX com prévia por linha e criação deliberada (M02).

Nada é transmitido. Commit das linhas selecionadas é atômico e idempotente por
(empresa, sistema_origem, id_origem).
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from decimal import Decimal

from .domain.models import DadosRascunho, Rascunho, parse_money, pendencias

LAYOUT = "nfse-imoveis-v1"
OBRIGATORIAS = ["id_origem", "tomador_documento", "tomador_nome", "operacao", "competencia", "valor", "descricao"]
OPS = {"locacao": "locacao", "locação": "locacao", "aluguel": "locacao", "venda": "venda",
       "arrendamento": "arrendamento", "administracao": "administracao", "administração": "administracao"}


class ArquivoInvalido(ValueError):
    pass


@dataclass
class Linha:
    linha: int
    sistema: str
    id_origem: str
    dados: DadosRascunho
    situacao: str
    erros: list[str] = field(default_factory=list)
    valor: Decimal = Decimal("0")


def read_rows(filename: str, data: bytes, max_bytes: int = 5 * 1024 * 1024) -> list[list[str]]:
    if len(data) > max_bytes:
        raise ArquivoInvalido("Arquivo maior que o limite.")
    name = filename.lower()
    if name.endswith(".csv"):
        text = data.decode("utf-8-sig")
        sample = text.split("\n", 1)[0]
        delim = ";" if sample.count(";") >= sample.count(",") else ","
        return [r for r in csv.reader(io.StringIO(text), delimiter=delim) if any(c.strip() for c in r)]
    if name.endswith(".xlsx"):
        if not data.startswith(b"PK"):
            raise ArquivoInvalido("Conteúdo não corresponde a XLSX.")
        from openpyxl import load_workbook  # leitura como dados: fórmulas não executam

        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb.worksheets[0]
        return [["" if c is None else str(c) for c in row] for row in ws.iter_rows(values_only=True)
                if any(c not in (None, "") for c in row)]
    raise ArquivoInvalido("Formato não suportado. Use .csv ou .xlsx.")


def _comp(s: str) -> str:
    s = s.strip()
    if "/" in s:
        m, y = s.split("/", 1)
        return f"{y}-{m.zfill(2)}"
    if len(s) >= 7 and s[4] == "-":
        return s[:7]
    return s


def preview(repo, empresa_id: str, rows: list[list[str]], max_rows: int = 5000) -> list[Linha]:
    if len(rows) < 2:
        raise ArquivoInvalido("Arquivo sem linhas de dados.")
    if len(rows) - 1 > max_rows:
        raise ArquivoInvalido("Limite de linhas excedido.")
    head = [h.strip().lower() for h in rows[0]]
    falt = [c for c in OBRIGATORIAS if c not in head]
    if falt:
        raise ArquivoInvalido(f"Colunas obrigatórias ausentes: {', '.join(falt)}")
    col = lambda r, n: (r[head.index(n)] if n in head and head.index(n) < len(r) else "").strip()
    seen: set[tuple[str, str]] = set()
    out: list[Linha] = []
    with repo.tx() as t:
        known = t.origins(empresa_id)
    for i, r in enumerate(rows[1:], start=2):
        erros: list[str] = []
        sistema = col(r, "sistema_origem") or "planilha"
        ido = col(r, "id_origem")
        op = OPS.get(col(r, "operacao").lower(), "")
        try:
            valor = parse_money(col(r, "valor"))
            vs = str(valor)
        except ValueError as e:
            valor, vs = Decimal("0"), ""
            erros.append(f"Valor: {e}")
        d = DadosRascunho(col(r, "tomador_documento"), col(r, "tomador_nome"), op, _comp(col(r, "competencia")), vs,
                          col(r, "descricao"), col(r, "imovel"), col(r, "tomador_email"))
        if not ido:
            erros.append("id_origem vazio")
        erros += [m for k, m in pendencias(d).items() if not (k == "valor" and vs == "")]
        key = (sistema, ido)
        if erros:
            sit = "invalida"
        elif key in seen:
            sit = "repetida_no_arquivo"
        elif (sistema, ido) in known:
            sit = "duplicada" if known[(sistema, ido)] == d.canonical() else "conflito"
        else:
            sit = "valida"
        if ido:
            seen.add(key)
        out.append(Linha(i, sistema, ido, d, sit, erros, valor))
    return out


def totals(linhas: list[Linha]) -> dict[str, dict]:
    t: dict[str, dict] = {}
    for l in linhas:
        x = t.setdefault(l.situacao, {"qtd": 0, "valor": Decimal("0.00")})
        x["qtd"] += 1
        x["valor"] += l.valor
    return t


def classify(known: dict[tuple[str, str], str], linhas: list[Linha]) -> list[Linha]:
    """Reclassifica linhas no servidor (não confia na prévia do navegador)."""
    seen: set[tuple[str, str]] = set()
    out = []
    for l in linhas:
        erros = list(pendencias(l.dados).values()) + ([] if l.id_origem else ["id_origem vazio"])
        k = (l.sistema, l.id_origem)
        if erros:
            sit = "invalida"
        elif k in seen:
            sit = "repetida_no_arquivo"
        elif k in known:
            sit = "duplicada" if known[k] == l.dados.canonical() else "conflito"
        else:
            sit = "valida"
        seen.add(k)
        out.append(Linha(l.linha, l.sistema, l.id_origem, l.dados, sit, erros, l.valor))
    return out


def confirm(repo, empresa_id: str, linhas: list[Linha], selecionadas: set[int]) -> dict:
    """Commit atômico. A unicidade (empresa, sistema, id_origem) do banco decide corridas."""
    criados, ignorados = 0, 0
    with repo.tx() as t:
        linhas = classify(t.origins(empresa_id), linhas)
        lote = repo.new_id("lote")
        tot = {k: {"qtd": v["qtd"], "valor": str(v["valor"])} for k, v in totals(linhas).items()}
        t.insert_batch(empresa_id, lote, LAYOUT, tot)
        for l in linhas:
            if l.linha not in selecionadas or l.situacao != "valida":
                ignorados += 1
                continue
            r = t.insert_draft(Rascunho(repo.new_id("rasc"), empresa_id, 1, l.dados,
                                        {"tipo": "importacao", "sistema": l.sistema, "idOrigem": l.id_origem, "loteId": lote, "linha": l.linha}))
            if t.insert_origin(empresa_id, lote, l.linha, l.sistema, l.id_origem, l.dados.canonical(), r.id):
                criados += 1
            else:
                t.delete_draft(empresa_id, r.id)
                ignorados += 1
    return {"criados": criados, "ignorados": ignorados}
