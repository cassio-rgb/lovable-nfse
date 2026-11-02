import unittest
from dataclasses import replace

from app import emissions, reviews, worker
from app.domain.models import Ambiente, Estado, Outcome, Rascunho
from app.domain.transitions import ConflitoVersao
from app.eligibility import OperacaoNaoLiberada
from tests.helpers import FakeAdapter, dados, setup

R = Ambiente.PRODUCAO_RESTRITA


def confirmed(key="k1"):
    repo, m, rel, p, _ = setup()
    rev = reviews.prepare(repo, p, "A", "r1", 1)
    e = emissions.confirm(repo, m, rel, p, "A", "r1", rev.id, 1, R, key, True)
    return repo, m, rel, p, rev, e


class Emissions(unittest.TestCase):
    def test_double_confirm_same_operation(self):
        repo, m, rel, p, rev, e = confirmed()
        e2 = emissions.confirm(repo, m, rel, p, "A", "r1", rev.id, 1, R, "k1", True)
        e3 = emissions.confirm(repo, m, rel, p, "A", "r1", rev.id, 1, R, "outra-chave", True)
        self.assertEqual(e.id, e2.id)
        self.assertEqual(e.id, e3.id)
        self.assertEqual(len(repo.emissoes), 1)

    def test_stale_review_blocked(self):
        repo, m, rel, p, _ = setup()
        rev = reviews.prepare(repo, p, "A", "r1", 1)
        reviews.update_draft(repo, "A", "r1", 1, dados("999.00"))
        with self.assertRaises(ConflitoVersao):
            emissions.confirm(repo, m, rel, p, "A", "r1", rev.id, 2, R, "k", True)

    def test_not_released_blocked(self):
        repo, m, rel, p, _ = setup()
        d = dados(); d.operacao = "venda"
        repo.insert_draft(Rascunho("r2", "A", 1, d))
        rev = reviews.prepare(repo, p, "A", "r2", 1)
        with self.assertRaises(OperacaoNaoLiberada):
            emissions.confirm(repo, m, rel, p, "A", "r2", rev.id, 1, R, "k", True)
        self.assertEqual(len(repo.emissoes), 0)

    def test_lost_response_only_lookup(self):
        repo, *_rest, e = confirmed()
        ad = FakeAdapter(submit=Outcome.UNKNOWN, lookup=Outcome.ACCEPTED)
        self.assertEqual(worker.run_once(repo, ad, now=0), "resultado_desconhecido")
        self.assertEqual(worker.run_once(repo, ad, now=1), "emitida")
        self.assertEqual((ad.submits, ad.lookups), (1, 1))

    def test_unknown_blocks_resend(self):
        repo, m, rel, p, rev, e = confirmed()
        worker.run_once(repo, FakeAdapter(submit=Outcome.UNKNOWN), now=0)
        with self.assertRaises(emissions.Bloqueado):
            emissions.confirm(repo, m, rel, p, "A", "r1", rev.id, 1, R, "nova", True)

    def test_crash_after_attempt_never_reposts(self):
        repo, *_rest, e = confirmed()
        ad = FakeAdapter(lookup=Outcome.ACCEPTED)
        self.assertEqual(worker.run_once(repo, ad, now=0, lease_seconds=10, crash_after_attempt=True), "crash")
        self.assertIsNone(worker.run_once(repo, ad, now=5))  # lease ainda válido
        self.assertEqual(worker.run_once(repo, ad, now=20), "emitida")
        self.assertEqual(ad.submits, 0)
        self.assertEqual(ad.lookups, 1)
        self.assertEqual(repo.emissoes[e.id].estado, Estado.EMITIDA)

    def test_fencing_rejects_worker_that_lost_lease(self):
        repo, *_rest, e = confirmed()
        old = worker.claim(repo, "antigo", 10, now=0)
        # antigo registra tentativa e "trava" na chamada externa; lease expira
        self.assertEqual(worker.run_once(repo, FakeAdapter(), job=old, crash_after_attempt=True), "crash")
        novo = worker.claim(repo, "novo", 10, now=20)
        self.assertEqual((novo.tipo, novo.fence), ("consultar", old.fence + 1))
        self.assertEqual(repo.emissoes[e.id].estado, Estado.RESULTADO_DESCONHECIDO)
        # o antigo volta com uma resposta: não pode sobrescrever
        self.assertEqual(worker.run_once(repo, FakeAdapter(submit=Outcome.REJECTED), job=replace(old, tipo="consultar")), "stale")
        self.assertEqual(worker.run_once(repo, FakeAdapter(lookup=Outcome.ACCEPTED), job=novo), "emitida")

    def test_requires_human_confirmation(self):
        repo, m, rel, p, _ = setup()
        rev = reviews.prepare(repo, p, "A", "r1", 1)
        with self.assertRaises(emissions.Bloqueado):
            emissions.confirm(repo, m, rel, p, "A", "r1", rev.id, 1, R, "k", False)

    def test_production_disabled_by_default(self):
        repo, m, rel, p, _ = setup()
        rev = reviews.prepare(repo, p, "A", "r1", 1)
        with self.assertRaises(emissions.Bloqueado):
            emissions.confirm(repo, m, rel, p, "A", "r1", rev.id, 1, Ambiente.PRODUCAO, "k", True)


if __name__ == "__main__":
    unittest.main()
