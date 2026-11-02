import unittest

from app import emissions
from app.auth import AcessoNegado, Principal
from app.domain.models import Ambiente
from tests.helpers import setup


class Isolation(unittest.TestCase):
    def test_other_company_denied_generically(self):
        repo, *_ = setup()
        with self.assertRaises(AcessoNegado) as c:
            repo.get_draft("B", "r1")
        self.assertEqual(str(c.exception), "Conteúdo indisponível")

    def test_revoked_cannot_emit(self):
        repo, m, rel, p, _ = setup()
        m.revoke("u1", "A")
        with self.assertRaises(AcessoNegado):
            emissions.confirm(repo, m, rel, p, "A", "r1", "x", 1, Ambiente.PRODUCAO_RESTRITA, "k", True)

    def test_cliente_without_membership(self):
        repo, m, rel, _, _ = setup()
        with self.assertRaises(AcessoNegado):
            emissions.confirm(repo, m, rel, Principal("u2", "cliente"), "A", "r1", "x", 1, Ambiente.PRODUCAO_RESTRITA, "k", True)


if __name__ == "__main__":
    unittest.main()
