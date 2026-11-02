"""Worker: claim com lease + fencing token, transmissão e reconciliação por consulta.

- Nenhuma transação/lock é mantida durante a chamada externa.
- Após registrar uma tentativa, nenhum caminho automático faz novo POST: lease expirado
  converte o job em `consultar` e a emissão em `resultado_desconhecido`.
- Cada claim incrementa `fence`; um worker que perdeu o lease não consegue gravar resultado.
"""
from __future__ import annotations

import time
from dataclasses import replace

from . import config
from .domain.models import Estado, Outcome
from .domain.transitions import transition
from .observability import event
from .ports import FiscalAdapter
from .repository import Job


def create_worker_repository(settings=None):
    """Cria o repositório durável do worker usando exclusivamente WORKER_DATABASE_URL."""
    s = settings or config.load()
    from .pg import PostgresRepository
    return PostgresRepository(s.worker_database_url)


OUTCOME_STATE = {
    Outcome.ACCEPTED: Estado.EMITIDA,
    Outcome.REJECTED: Estado.REJEITADA,
    Outcome.UNKNOWN: Estado.RESULTADO_DESCONHECIDO,
    Outcome.PRE_SEND_FAILURE: Estado.ERRO_PRE_ENVIO,
}


def claim(repo, worker_id: str, lease_seconds: int, now: float | None = None) -> Job | None:
    t0 = time.time() if now is None else now
    with repo.tx() as t:
        j = t.next_claimable(t0)
        if not j:
            return None
        tipo = j.tipo
        if j.situacao == "em_execucao":  # lease perdido
            e = t.get_emission(j.empresa_id, j.emissao_id, lock=True)
            if e.tentativas > 0:
                tipo = "consultar"
                if e.estado == Estado.TRANSMITINDO:
                    t.save_emission(replace(e, estado=transition(e.estado, Estado.RESULTADO_DESCONHECIDO)))
        nj = replace(j, tipo=tipo, situacao="em_execucao", fence=j.fence + 1, dono=worker_id, lease_ate=t0 + lease_seconds)
        t.save_job(nj)
        return nj


def _current(t, job: Job) -> Job | None:
    cur = t.get_job(job.empresa_id, job.emissao_id, lock=True)
    if not cur or cur.fence != job.fence or cur.dono != job.dono or cur.situacao != "em_execucao":
        return None
    return cur


def run_once(repo, adapter: FiscalAdapter, worker_id: str = "w1", lease_seconds: int = 120,
             now: float | None = None, crash_after_attempt: bool = False, job: Job | None = None) -> str | None:
    job = job or claim(repo, worker_id, lease_seconds, now)
    if not job:
        return None
    if job.tipo == "transmitir":
        with repo.tx() as t:
            if not _current(t, job):
                return "stale"
            e = t.get_emission(job.empresa_id, job.emissao_id, lock=True)
            e = t.save_emission(replace(e, estado=transition(e.estado, Estado.TRANSMITINDO), tentativas=e.tentativas + 1))
            t.insert_attempt(job.empresa_id, e.id, job.fence)
        if crash_after_attempt:
            return "crash"
        result = adapter.submit(e)  # fora de transação
    else:
        with repo.tx() as t:
            e = t.get_emission(job.empresa_id, job.emissao_id)
        result = adapter.lookup(e)  # fora de transação
    with repo.tx() as t:
        if not _current(t, job):
            event("resultado_descartado_fence", job.emissao_id, fence=job.fence)
            return "stale"
        e = t.get_emission(job.empresa_id, job.emissao_id, lock=True)
        target = OUTCOME_STATE[result.outcome]
        if target != e.estado:
            e = t.save_emission(replace(e, estado=transition(e.estado, target), resultado=result))
        if target == Estado.RESULTADO_DESCONHECIDO:
            t.save_job(replace(job, situacao="pendente", tipo="consultar", dono=None))
        else:
            t.save_job(replace(job, situacao="concluido", dono=None))
    return target.value
