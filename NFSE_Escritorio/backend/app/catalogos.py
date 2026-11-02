"""Consulta versionada. Não calcula imposto, não habilita emissão."""
from pathlib import Path
import json

_ROOT = Path(__file__).resolve()
_CATALOG_PATH = _ROOT.parents[2]/'shared/catalogos-fiscais.json'
if not _CATALOG_PATH.is_file():  # imagem Docker: backend é copiado para /srv
    _CATALOG_PATH = _ROOT.parents[1]/'shared/catalogos-fiscais.json'
CATALOGO = json.loads(_CATALOG_PATH.read_text(encoding='utf-8'))
SERVICOS = {v['codigo']:v for v in CATALOGO['servicos']}
NBS = {v['codigo']:v for v in CATALOGO['nbs'] if v['descricao']}
CLASSES = {v['codigo']:v for v in CATALOGO['classes'] if v['nfse']}
INDOPS = {v['codigo']:v for v in CATALOGO['indops'] if v['nfse']}
CSTS = {v['cst'] for v in CLASSES.values()}
FIELDS = ('catalogoId','servico','nbs','cst','cClassTrib','cIndOp')

def pendencias_catalogo(s):
    if not isinstance(s,dict):
        return {'catalogo':'Selecione os códigos fiscais antes de revisar.'}
    p={}
    if s.get('catalogoId')!=CATALOGO['id']:
        p['catalogo']='Seleção vinculada a outra versão das tabelas. Confira e selecione novamente.'
    for key,table,label in (('servico',SERVICOS,'serviço nacional'),('nbs',NBS,'NBS'),('cst',CSTS,'CST IBS/CBS'),('cClassTrib',CLASSES,'cClassTrib para NFS-e'),('cIndOp',INDOPS,'indicador de operação para NFS-e')):
        if not isinstance(s.get(key),str) or s[key] not in table:
            p[key]='Selecione um código válido de '+label+'.'
    cls=CLASSES.get(s.get('cClassTrib')) if isinstance(s.get('cClassTrib'),str) else None
    if cls and cls['cst']!=s.get('cst'):
        p['cClassTrib']='O cClassTrib não corresponde ao CST selecionado.'
    return p

def canonical_catalogo(s):
    return [s.get(k,'') for k in FIELDS] if isinstance(s,dict) else None
