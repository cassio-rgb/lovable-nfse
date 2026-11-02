"""Regenera catálogo de consulta. Não executa fórmulas nem classifica operações.

Uso: python scripts/gerar_catalogos.py [--check]
openpyxl é necessário somente para regeneração/verificação, não para a consulta na UI.
"""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'backend/tests/fixtures/official/catalogos'
OUTPUT = ROOT / 'shared/catalogos-fiscais.json'
FILES = [
    ('servicos', 'anexo_b-nbs2-lista_servico_nacional-snnfse-v1-01-20260122.xlsx', '1.01'),
    ('correlacoes', 'anexo_viii-tabela-correlacao-v01-02-00-20261026.xlsx', '1.02.00'),
    ('indops', 'anexovii-indop_ibscbs_v1-03-00-nt009.xlsx', '1.03.00'),
    ('classes', 'classificacao_tributaria.xlsx', None),
]

def text(v):
    return '' if v is None else str(v).strip()

def expanded(ws):
    """Apenas intervalos mesclados reais; não propagar vazios fora deles."""
    cells = {}
    for m in ws.merged_cells.ranges:
        value = text(ws.cell(m.min_row, m.min_col).value)
        for r in range(m.min_row, m.max_row + 1):
            for c in range(m.min_col, m.max_col + 1):
                cells[(r, c)] = value
    return [dict(linha=r, valores=[cells.get((r,c), text(ws.cell(r,c).value))
                                 for c in range(1, ws.max_column + 1)])
            for r in range(1, ws.max_row + 1)
            if any(ws.cell(r,c).value is not None for c in range(1,ws.max_column+1))]

def generate():
    from openpyxl import load_workbook
    sources = [dict(tipo=t, arquivo=n, versao=v, sha256=hashlib.sha256((SOURCES/n).read_bytes()).hexdigest()) for t,n,v in FILES]
    cat = dict(id='catalogo-v1-'+hashlib.sha256(''.join(s['sha256'] for s in sources).encode()).hexdigest()[:16],
               capturadoEm='2026-11-02', vigencia='Não confirmada; validar por competência e ambiente antes da emissão real.', fontes=sources)
    b = load_workbook(SOURCES/FILES[0][1], data_only=True)
    cat['servicos'] = [dict(codigo=text(r[0]).zfill(6), descricao=text(r[4])) for r in list(b['LISTA.SERV.NAC.'].values)[1:] if r[0] is not None]
    cat['nbs'] = [dict(codigo=text(r[0]), descricao=text(r[1])) for r in list(b['LISTA.NBS_v2.0'].values)[1:] if re.fullmatch(r'\d\.\d{4}\.\d{2}\.\d{2}',text(r[0]))]
    cl = load_workbook(SOURCES/FILES[3][1], data_only=True).active
    cat['classes'] = [dict(codigo=text(r[10]).zfill(6), descricao=text(r[11]), cst=text(r[0]).zfill(3), descricaoCst=text(r[1]), nfse=text(r[29])=='Sim', atributos={text(h):text(v) for h,v in zip(next(cl.values),r)}) for r in list(cl.values)[1:] if r[10] is not None]
    op = load_workbook(SOURCES/FILES[2][1], data_only=True).active
    cat['indops'] = [dict(codigo=text(r[0]).zfill(6), descricao=' — '.join(text(v) for v in r[1:3]), nfse=text(r[7])=='S', local=text(r[3]), atributos={text(h):text(v) for h,v in zip(next(op.values),r)}) for r in list(op.values)[1:] if r[0] is not None]
    corr = load_workbook(SOURCES/FILES[1][1], data_only=True)
    cat['correlacoes'] = expanded(corr['tabela geral'])[1:]
    cat['notasCorrelacoes'] = expanded(corr['REGRA OP NÃO ONE_EXT'])
    assert [len(cat[k]) for k in ('servicos','nbs','classes','indops','correlacoes')] == [338,918,173,40,1609]
    for k in ('servicos','nbs','classes','indops'):
        assert len({v['codigo'] for v in cat[k]})==len(cat[k]), k
    assert sum(c['nfse'] for c in cat['classes'])==73
    assert sum(c['nfse'] for c in cat['indops'])==28
    return json.dumps(cat,ensure_ascii=False,sort_keys=True,indent=2)+'\n'

if __name__=='__main__':
    result=generate()
    if '--check' in sys.argv:
        assert OUTPUT.read_text(encoding='utf-8')==result, 'Catálogo difere das fontes'
        print('Catálogo confere integralmente com as quatro fontes.')
    else:
        OUTPUT.parent.mkdir(parents=True,exist_ok=True)
        OUTPUT.write_text(result,encoding='utf-8')
        print('Catálogo gerado:',OUTPUT)
