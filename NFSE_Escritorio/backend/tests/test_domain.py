import unittest

from app import reviews
from app.domain.models import Estado, parse_money
from app.domain.transitions import ConflitoVersao, TransicaoInvalida, transition
from tests.helpers import dados, setup


class Domain(unittest.TestCase):
    def test_money(self):
        self.assertEqual(str(parse_money("1.234,56")), "1234.56")
        with self.assertRaises(ValueError):
            parse_money("10.555")

    def test_unknown_never_returns_to_send(self):
        for t in (Estado.NA_FILA, Estado.TRANSMITINDO):
            with self.assertRaises(TransicaoInvalida):
                transition(Estado.RESULTADO_DESCONHECIDO, t)

    def test_change_invalidates_review(self):
        repo, _, _, p, r = setup()
        rev = reviews.prepare(repo, p, "A", "r1", 1)
        self.assertTrue(reviews.is_valid(repo, rev))
        reviews.update_draft(repo, "A", "r1", 1, dados("351.00"))
        self.assertFalse(reviews.is_valid(repo, rev))

    def test_concurrent_edit_conflict(self):
        repo, *_ = setup()
        reviews.update_draft(repo, "A", "r1", 1, dados("400.00"))
        with self.assertRaises(ConflitoVersao):
            reviews.update_draft(repo, "A", "r1", 1, dados("500.00"))


if __name__ == "__main__":
    unittest.main()
