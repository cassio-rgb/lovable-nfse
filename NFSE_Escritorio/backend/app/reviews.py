"""Snapshot revisado vinculado à versão e hash exatos do conteúdo."""
from __future__ import annotations

from dataclasses import replace

from .auth import Principal
from .catalogos import pendencias_catalogo
from .domain.models import DadosRascunho, Rascunho, Revisao, content_hash, pendencias, utcnow
from .domain.transitions import check_version


class Pendente(Exception):
    pass


class JaEnviado(Exception):
    pass


def update_draft(repo, empresa_id: str, rid: str, expected: int, dados: DadosRascunho) -> Rascunho:
    with repo.tx() as t:
        r = t.get_draft(empresa_id, rid, lock=True)
        if r.emissao_id:
            raise JaEnviado("Rascunho já enviado não pode ser alterado")
        check_version(expected, r.versao)
        if r.dados.canonical() == dados.canonical():
            return r
        return t.save_draft(replace(r, dados=dados, versao=r.versao + 1, atualizado_em=utcnow()))


def prepare(repo, p: Principal, empresa_id: str, rid: str, versao: int) -> Revisao:
    with repo.tx() as t:
        r = t.get_draft(empresa_id, rid, lock=True)
        if r.emissao_id:
            raise JaEnviado("Rascunho já enviado")
        check_version(versao, r.versao)
        if pendencias(r.dados) or pendencias_catalogo(r.dados.fiscal):
            raise Pendente("Há pendências no rascunho")
        rev = Revisao(repo.new_id("rev"), empresa_id, rid, r.versao, content_hash(empresa_id, r.dados), p.user_id)
        t.insert_review(rev)
        return rev


def is_valid_in(t, rev: Revisao) -> bool:
    r = t.get_draft(rev.empresa_id, rev.rascunho_id)
    return not pendencias_catalogo(r.dados.fiscal) and r.versao == rev.versao and content_hash(rev.empresa_id, r.dados) == rev.hash


def is_valid(repo, rev: Revisao) -> bool:
    with repo.tx() as t:
        return is_valid_in(t, rev)
