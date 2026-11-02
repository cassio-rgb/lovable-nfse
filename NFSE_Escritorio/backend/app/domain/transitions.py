"""Máquina de estados explícita. Resultado desconhecido nunca volta para envio."""
from __future__ import annotations

from .models import Estado

ALLOWED: dict[Estado, set[Estado]] = {
    Estado.NA_FILA: {Estado.TRANSMITINDO, Estado.ERRO_PRE_ENVIO},
    Estado.TRANSMITINDO: {Estado.EMITIDA, Estado.REJEITADA, Estado.RESULTADO_DESCONHECIDO, Estado.ERRO_PRE_ENVIO},
    # Só uma consulta oficial conclusiva tira do desconhecido; nunca para NA_FILA/TRANSMITINDO.
    Estado.RESULTADO_DESCONHECIDO: {Estado.EMITIDA, Estado.REJEITADA},
    Estado.EMITIDA: set(),
    Estado.REJEITADA: set(),
    Estado.ERRO_PRE_ENVIO: {Estado.NA_FILA},  # nova tentativa controlada, sem efeito externo comprovado
}


class TransicaoInvalida(Exception):
    pass


class ConflitoVersao(Exception):
    pass


def transition(current: Estado, target: Estado) -> Estado:
    if target not in ALLOWED.get(current, set()):
        raise TransicaoInvalida(f"{current.value} -> {target.value}")
    return target


def check_version(expected: int | None, actual: int) -> None:
    if expected is None or expected != actual:
        raise ConflitoVersao("Versão do rascunho divergente")
