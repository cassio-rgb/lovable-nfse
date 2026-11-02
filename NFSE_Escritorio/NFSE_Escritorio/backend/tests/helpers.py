from app.catalogos import CATALOGO
from app.auth import MembershipStore, Principal
from app.domain.models import DadosRascunho, FiscalResult, Outcome, Rascunho
from app.eligibility import Release, ReleaseRegistry
from app.repository import MemoryRepository


def dados(valor="350.00"):
    return DadosRascunho("529.982.247-25", "Maria Fictícia", "locacao", "2026-11", valor, "Taxa de administração", fiscal=dict(catalogoId=CATALOGO["id"],servico="010101",nbs="1.0101.11.00",cst="000",cClassTrib="000001",cIndOp="010101"))


class FakeAdapter:
    """Integração SIMULADA para testes locais — nunca usada como emissão oficial."""

    def __init__(self, submit=Outcome.ACCEPTED, lookup=Outcome.ACCEPTED):
        self.s, self.l, self.submits, self.lookups = submit, lookup, 0, 0

    def submit(self, e):
        self.submits += 1
        return FiscalResult(self.s, "c", e.identidade_dps)

    def lookup(self, e):
        self.lookups += 1
        return FiscalResult(self.l, "c", e.identidade_dps)


def setup():
    repo, m, rel = MemoryRepository(), MembershipStore(), ReleaseRegistry()
    p = Principal("u1", "escritorio")
    m.grant("u1", "A", {"editar", "emitir"})
    rel.register(Release("A", "locacao", "producao_restrita", 1, "evidência de teste", "esc"))
    r = repo.insert_draft(Rascunho("r1", "A", 1, dados()))
    return repo, m, rel, p, r
