import copy
import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path
import unittest

from app.catalogos import CATALOGO, CLASSES, INDOPS, pendencias_catalogo
from app.domain.models import DadosRascunho, content_hash
from app import reviews
from tests.helpers import dados, setup

class CatalogTests(unittest.TestCase):
    def test_full_sources_and_counts(self):
        root=Path(__file__).resolve().parents[2]
        for s in CATALOGO['fontes']:
            self.assertEqual(s['sha256'],hashlib.sha256((root/'backend/tests/fixtures/official/catalogos'/s['arquivo']).read_bytes()).hexdigest())
        self.assertEqual([len(CATALOGO[k]) for k in ('servicos','nbs','classes','indops','correlacoes')],[338,918,173,40,1609])
        self.assertEqual((len(CLASSES),len(INDOPS)),(73,28))

    def test_membership_pair_and_environment_flags(self):
        s=dados().fiscal
        self.assertEqual(pendencias_catalogo(s),{})
        for key,value in [('nbs','9.9999.99.99'),('cst','200'),('cClassTrib','000002'),('cIndOp','010104'),('catalogoId','antigo'),('servico','10101')]:
            self.assertTrue(pendencias_catalogo({**s,key:value}))
        self.assertTrue(pendencias_catalogo(None))

    def test_each_field_changes_hash_roundtrip(self):
        d=dados()
        for k in d.fiscal:
            other=replace(d,fiscal={**d.fiscal,k:'outro'})
            self.assertNotEqual(content_hash('A',d),content_hash('A',other))
        self.assertEqual(DadosRascunho(**json.loads(json.dumps(asdict(d)))),d)
        old=asdict(d);old.pop('fiscal')
        self.assertIsNone(DadosRascunho(**old).fiscal)
        self.assertEqual(len(json.loads(DadosRascunho(**old).canonical())),7)

    def test_api_and_pg_json_roundtrip(self):
        from app.api import DadosIn, ser_dados
        from app.pg import _dados
        d=dados()
        self.assertEqual(DadosIn(**ser_dados(d)).domain(),d)
        self.assertEqual(_dados(asdict(d)),d)
        old=asdict(d);old.pop('fiscal')
        self.assertIsNone(_dados(old).fiscal)

    def test_save_incomplete_review_blocks_old_review_invalid(self):
        repo,m,rel,p,r=setup()
        rev=reviews.prepare(repo,p,'A',r.id,r.versao)
        self.assertTrue(reviews.is_valid(repo,rev))
        changed=reviews.update_draft(repo,'A',r.id,r.versao,replace(r.dados,fiscal=None))
        self.assertFalse(reviews.is_valid(repo,rev))
        with self.assertRaises(reviews.Pendente):reviews.prepare(repo,p,'A',r.id,changed.versao)
        # A previously stored legacy review with its original canonical hash also fails.
        oldrev=replace(rev,versao=changed.versao,hash=content_hash('A',changed.dados))
        self.assertFalse(reviews.is_valid(repo,oldrev))

if __name__=='__main__': unittest.main()
