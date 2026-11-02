"""Confirmação atômica: revalida vínculo, liberação, versão e revisão; reserva DPS e cria job.

Idempotência: chave escopada por empresa e vinculada à impressão digital
(empresa, rascunho, versão, ambiente, hash revisado). Concorrência: a linha do
rascunho é travada (FOR UPDATE no PostgreSQL) e as unicidades do banco são a
última barreira — em violação, a transação é refeita e devolve a operação existente.
"""
from __future__ import annotations

import hashlib
from copy import deepcopy
from dataclasses import replace

from .auth import Principal
from .domain.models import Ambiente, Emissao, Estado
from .domain.transitions import ConflitoVersao
from . import reviews


class Bloqueado(Exception):
    pass


class UniqueRace(Exception):
    """Levantada pelo repositório quando outra transação venceu a corrida de unicidade."""


def fingerprint(empresa_id: str, rid: str, versao: int, ambiente: Ambiente, review_hash: str) -> str:
    return hashlib.sha256(f"{empresa_id}|{rid}|{versao}|{ambiente.value}|{review_hash}".encode()).hexdigest()


def _confirm_once(repo, releases, empresa_id, rid, revisao_id, versao, ambiente, key) -> Emissao:
    with repo.tx() as t:
        r = t.get_draft(empresa_id, rid, lock=True)
        rev = t.get_review(empresa_id, revisao_id)
        if not rev or rev.rascunho_id != rid:
            raise ConflitoVersao("Revisão não corresponde ao rascunho")
        fp = fingerprint(empresa_id, rid, versao, ambiente, rev.hash)
        prev = t.emission_by_key(empresa_id, key)
        if prev:
            if prev.fingerprint != fp:
                raise ConflitoVersao("Chave idempotente reutilizada com outro conteúdo ou ambiente")
            return prev
        existing = t.emission_for_version(empresa_id, rid, versao, ambiente.value)
        if existing is None and r.emissao_id:
            existing = t.get_emission(empresa_id, r.emissao_id)
        if existing:
            if existing.estado == Estado.RESULTADO_DESCONHECIDO:
                raise Bloqueado("Resultado desconhecido: verificar situação; reenvio não permitido")
            return existing
        if rev.versao != versao or not reviews.is_valid_in(t, rev):
            raise ConflitoVersao("Revisão não corresponde à versão atual")
        releases.require(empresa_id, r.dados.operacao, ambiente.value)
        e = Emissao(repo.new_id("op"), empresa_id, rid, versao, ambiente, t.reserve_dps(empresa_id, ambiente.value),
                    deepcopy(r.dados), revisao_id, key, fingerprint=fp)
        t.insert_emission(e)
        t.save_draft(replace(r, emissao_id=e.id))
        t.insert_job(empresa_id, e.id, "transmitir")
        return e


def confirm(repo, members, releases, p: Principal, empresa_id: str, rid: str, revisao_id: str, versao: int,
            ambiente: Ambiente, chave_idempotente: str, confirmacao_humana: bool,
            production_enabled: bool = False) -> Emissao:
    members.require(p, empresa_id, "emitir")
    if not confirmacao_humana:
        raise Bloqueado("Confirmação humana obrigatória")
    if ambiente == Ambiente.PRODUCAO and not production_enabled:
        raise Bloqueado("Produção desabilitada")
    if not chave_idempotente or len(chave_idempotente) > 200:
        raise Bloqueado("Chave idempotente inválida")
    for _ in range(3):
        try:
            return _confirm_once(repo, releases, empresa_id, rid, revisao_id, versao, ambiente, chave_idempotente)
        except UniqueRace:
            continue  # a outra transação já persistiu: a próxima volta devolve a operação dela
    raise Bloqueado("Concorrência persistente; consulte a situação")


def schedule_lookup(repo, empresa_id: str, eid: str) -> Emissao:
    """Agenda consulta idempotente. Nunca cria emissão nem reagenda transmissão."""
    with repo.tx() as t:
        e = t.get_emission(empresa_id, eid)
        if e.estado == Estado.RESULTADO_DESCONHECIDO:
            j = t.get_job(empresa_id, eid, lock=True)
            if j and j.situacao != "em_execucao":
                t.save_job(replace(j, tipo="consultar", situacao="pendente"))
        return e
