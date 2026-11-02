"""Contrato de persistência e implementação em memória (SOMENTE testes/demonstração).

Serviços usam `with repo.tx() as t:` e apenas os métodos de `Tx`. A implementação
PostgreSQL durável está em `app/pg.py` (`PostgresRepository`).
"""
from __future__ import annotations

import threading
import uuid
from contextvars import ContextVar
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Iterator, Protocol

from .auth import AcessoNegado
from .domain.models import Emissao, Rascunho, Revisao, utcnow


#: usuário autenticado da requisição corrente; usado pelo PostgreSQL para RLS (app.user_id).
current_user_id: ContextVar[str | None] = ContextVar("current_user_id", default=None)


@dataclass(frozen=True)
class Job:
    empresa_id: str
    emissao_id: str
    tipo: str  # transmitir | consultar
    situacao: str  # pendente | em_execucao | concluido
    fence: int
    dono: str | None
    lease_ate: float


def new_id() -> str:
    return str(uuid.uuid4())


class Tx(Protocol):
    # rascunhos
    def insert_draft(self, r: Rascunho) -> Rascunho: ...
    def get_draft(self, empresa_id: str, rid: str, lock: bool = False) -> Rascunho: ...
    def list_drafts(self, empresa_id: str) -> list[Rascunho]: ...
    def save_draft(self, r: Rascunho) -> Rascunho: ...
    def delete_draft(self, empresa_id: str, rid: str) -> None: ...
    # revisões
    def insert_review(self, rev: Revisao) -> None: ...
    def get_review(self, empresa_id: str, rev_id: str) -> Revisao | None: ...
    def latest_review(self, empresa_id: str, rid: str) -> Revisao | None: ...
    # importação
    def origins(self, empresa_id: str) -> dict[tuple[str, str], str]: ...
    def insert_batch(self, empresa_id: str, batch_id: str, layout: str, totals: dict) -> None: ...
    def insert_origin(self, empresa_id: str, batch_id: str, linha: int, sistema: str, id_origem: str,
                      conteudo: str, draft_id: str) -> bool: ...
    # emissões
    def emission_by_key(self, empresa_id: str, key: str) -> Emissao | None: ...
    def emission_for_version(self, empresa_id: str, rid: str, versao: int, ambiente: str) -> Emissao | None: ...
    def insert_emission(self, e: Emissao) -> None: ...
    def get_emission(self, empresa_id: str, eid: str, lock: bool = False) -> Emissao: ...
    def list_emissions(self, empresa_id: str, rid: str | None = None, versao: int | None = None) -> list[Emissao]: ...
    def save_emission(self, e: Emissao) -> Emissao: ...
    def reserve_dps(self, empresa_id: str, ambiente: str) -> str: ...
    # jobs
    def insert_job(self, empresa_id: str, eid: str, tipo: str) -> None: ...
    def get_job(self, empresa_id: str, eid: str, lock: bool = False) -> Job | None: ...
    def save_job(self, j: Job) -> None: ...
    def next_claimable(self, now: float) -> Job | None: ...  # deve travar a linha (SKIP LOCKED no PG)
    def insert_attempt(self, empresa_id: str, eid: str, fence: int) -> None: ...


def dps_identity(empresa_id: str, ambiente: str, n: int) -> str:
    """Identidade interna reservada e persistida. O número (15 dígitos) é o nDPS da DPS oficial;
    o Id oficial (município+CNPJ+série+número) é derivado em `app/nfse/dps.py` sem alterar esta identidade."""
    return f"DPS-{ambiente}-{empresa_id[:8]}-{n:015d}"


def numero_reservado(identidade: str, empresa_id: str, ambiente: str) -> int:
    """Número reservado, exigindo que a identidade pertença exatamente a esta empresa e ambiente."""
    prefixo = f"DPS-{ambiente}-{empresa_id[:8]}-"
    tail = identidade[len(prefixo):] if identidade.startswith(prefixo) else ""
    if not (len(tail) == 15 and tail.isdigit()) or int(tail) < 1 or dps_identity(empresa_id, ambiente, int(tail)) != identidade:
        raise ValueError("Identidade DPS reservada inválida ou de outra empresa/ambiente")
    return int(tail)


class MemoryRepository:
    """Volátil: some ao reiniciar. A API recusa usá-lo fora de APP_ENV=test."""

    durable = False

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.rascunhos: dict[str, Rascunho] = {}
        self.revisoes: dict[str, Revisao] = {}
        self.emissoes: dict[str, Emissao] = {}
        self.origens_: dict[tuple[str, str, str], tuple[str, str]] = {}
        self.lotes: dict[str, dict] = {}
        self.dps_seq: dict[tuple[str, str], int] = {}
        self.jobs: dict[str, Job] = {}
        self.attempts: list[tuple[str, str, int]] = []

    @staticmethod
    def new_id(_prefix: str = "") -> str:
        return new_id()

    @contextmanager
    def tx(self) -> Iterator["MemoryRepository"]:
        with self._lock:
            snap = deepcopy((self.rascunhos, self.revisoes, self.emissoes, self.origens_, self.lotes,
                             self.dps_seq, self.jobs, self.attempts))
            try:
                yield self
            except BaseException:
                (self.rascunhos, self.revisoes, self.emissoes, self.origens_, self.lotes,
                 self.dps_seq, self.jobs, self.attempts) = snap
                raise

    # rascunhos
    def insert_draft(self, r):
        self.rascunhos[r.id] = r
        return r

    def get_draft(self, empresa_id, rid, lock=False):
        r = self.rascunhos.get(rid)
        if not r or r.empresa_id != empresa_id:
            raise AcessoNegado()
        return r

    def list_drafts(self, empresa_id):
        return sorted([r for r in self.rascunhos.values() if r.empresa_id == empresa_id and not r.emissao_id],
                      key=lambda r: r.atualizado_em, reverse=True)

    def save_draft(self, r):
        self.rascunhos[r.id] = r
        return r

    def delete_draft(self, empresa_id, rid):
        self.get_draft(empresa_id, rid)
        del self.rascunhos[rid]
        self.origens_ = {k: v for k, v in self.origens_.items() if v[1] != rid}  # = ON DELETE CASCADE
        self.revisoes = {k: v for k, v in self.revisoes.items() if v.rascunho_id != rid}

    # revisões
    def insert_review(self, rev):
        self.revisoes[rev.id] = rev

    def get_review(self, empresa_id, rev_id):
        v = self.revisoes.get(rev_id)
        return v if v and v.empresa_id == empresa_id else None

    def latest_review(self, empresa_id, rid):
        vs = [v for v in self.revisoes.values() if v.empresa_id == empresa_id and v.rascunho_id == rid]
        return vs[-1] if vs else None

    # importação
    def origins(self, empresa_id):
        return {(s, i): v[0] for (e, s, i), v in self.origens_.items() if e == empresa_id}

    def insert_batch(self, empresa_id, batch_id, layout, totals):
        self.lotes[batch_id] = {"empresa": empresa_id, "layout": layout, "totais": totals}

    def insert_origin(self, empresa_id, batch_id, linha, sistema, id_origem, conteudo, draft_id):
        k = (empresa_id, sistema, id_origem)
        if k in self.origens_:
            return False
        self.origens_[k] = (conteudo, draft_id)
        return True

    # emissões
    def emission_by_key(self, empresa_id, key):
        return next((e for e in self.emissoes.values() if e.empresa_id == empresa_id and e.chave_idempotente == key), None)

    def emission_for_version(self, empresa_id, rid, versao, ambiente):
        return next((e for e in self.emissoes.values() if e.empresa_id == empresa_id and e.rascunho_id == rid
                     and e.versao == versao and e.ambiente.value == ambiente), None)

    def insert_emission(self, e):
        if self.emission_by_key(e.empresa_id, e.chave_idempotente) or \
                self.emission_for_version(e.empresa_id, e.rascunho_id, e.versao, e.ambiente.value):
            raise RuntimeError("violação de unicidade")
        self.emissoes[e.id] = e

    def get_emission(self, empresa_id, eid, lock=False):
        e = self.emissoes.get(eid)
        if not e or e.empresa_id != empresa_id:
            raise AcessoNegado()
        return e

    def list_emissions(self, empresa_id, rid=None, versao=None):
        es = [e for e in self.emissoes.values() if e.empresa_id == empresa_id
              and (rid is None or e.rascunho_id == rid) and (versao is None or e.versao == versao)]
        return sorted(es, key=lambda e: e.criado_em, reverse=True)

    def save_emission(self, e):
        e = replace(e, atualizado_em=utcnow())
        self.emissoes[e.id] = e
        return e

    def reserve_dps(self, empresa_id, ambiente):
        k = (empresa_id, ambiente)
        self.dps_seq[k] = self.dps_seq.get(k, 0) + 1
        return dps_identity(empresa_id, ambiente, self.dps_seq[k])

    # jobs
    def insert_job(self, empresa_id, eid, tipo):
        self.jobs[eid] = Job(empresa_id, eid, tipo, "pendente", 0, None, 0.0)

    def get_job(self, empresa_id, eid, lock=False):
        j = self.jobs.get(eid)
        return j if j and j.empresa_id == empresa_id else None

    def save_job(self, j):
        self.jobs[j.emissao_id] = j

    def next_claimable(self, now):
        for j in self.jobs.values():
            if j.situacao == "pendente" or (j.situacao == "em_execucao" and j.lease_ate < now):
                return j
        return None

    def insert_attempt(self, empresa_id, eid, fence):
        self.attempts.append((empresa_id, eid, fence))
