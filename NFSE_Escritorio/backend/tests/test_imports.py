import unittest
from decimal import Decimal

from app import imports
from app.repository import MemoryRepository

CSV = (
    "id_origem;tomador_documento;tomador_nome;operacao;competencia;valor;descricao\n"
    "A1;529.982.247-25;Maria;locacao;11/2026;100,00;Administração nov\n"
    "A2;529.982.247-25;João;locacao;11/2026;200,00;Administração nov\n"
    "A3;000;Inválido;locacao;11/2026;50,00;Administração nov\n"
    "A1;529.982.247-25;Maria;locacao;11/2026;100,00;Administração nov\n"
).encode()


class Imports(unittest.TestCase):
    def test_mixed_file_and_reimport(self):
        repo = MemoryRepository()
        rows = imports.read_rows("x.csv", CSV)
        linhas = imports.preview(repo, "A", rows)
        t = imports.totals(linhas)
        self.assertEqual(t["valida"], {"qtd": 2, "valor": Decimal("300.00")})
        self.assertEqual(t["invalida"]["qtd"], 1)
        self.assertEqual(t["repetida_no_arquivo"]["qtd"], 1)
        self.assertEqual(imports.confirm(repo, "A", linhas, {2, 3})["criados"], 2)
        again = imports.preview(repo, "A", rows)
        self.assertEqual(imports.confirm(repo, "A", again, {l.linha for l in again})["criados"], 0)
        self.assertEqual(len(repo.rascunhos), 2)
        self.assertEqual(len(repo.emissoes), 0)  # importar nunca transmite

    def test_other_company_not_affected(self):
        repo = MemoryRepository()
        rows = imports.read_rows("x.csv", CSV)
        imports.confirm(repo, "A", imports.preview(repo, "A", rows), {2, 3})
        self.assertEqual(imports.totals(imports.preview(repo, "B", rows))["valida"]["qtd"], 2)

    def test_rejects_unknown_format(self):
        with self.assertRaises(imports.ArquivoInvalido):
            imports.read_rows("x.xls", b"abc")


if __name__ == "__main__":
    unittest.main()
