"""Infraestrutura de resiliência — §5.4 e cenários de caos §4.7.

Somente mecanismos: circuit breaker, health probe do LLM e a resposta
degradada (LaudoDegradado). A orquestração do laudo fica em pipeline.py.
"""

import time

import httpx

from ..config import LLM_TIMEOUT_S, OLLAMA_URL, PROBE_TIMEOUT_S
from ..regras import nivel_risco
from ..schemas import LaudoDegradado

__all__ = [
    "CircuitBreaker", "llm_saudavel", "laudo_degradado",
    "OLLAMA_URL", "PROBE_TIMEOUT_S", "LLM_TIMEOUT_S",
]


class CircuitBreaker:
    def __init__(self, falhas_max: int = 3, reabrir_apos_s: float = 15.0):
        self.falhas_max = falhas_max
        self.reabrir_apos_s = reabrir_apos_s
        self.falhas = 0
        self.aberto_em: float | None = None

    def permite(self) -> bool:  # meia-abertura
        if self.aberto_em is None:
            return True
        return time.monotonic() - self.aberto_em >= self.reabrir_apos_s

    def sucesso(self) -> None:
        self.falhas = 0
        self.aberto_em = None

    def falha(self) -> None:
        self.falhas += 1
        if self.falhas >= self.falhas_max:
            self.aberto_em = time.monotonic()


async def llm_saudavel(client: httpx.AsyncClient, base_url: str = OLLAMA_URL) -> bool:
    try:
        r = await client.get(base_url + "/", timeout=PROBE_TIMEOUT_S)
        return r.status_code == 200
    except httpx.HTTPError:  # inclui timeout e conexão recusada
        return False


def laudo_degradado(caso: dict, score: float, motivo: str) -> LaudoDegradado:
    return LaudoDegradado(
        trace_id=caso["trace_id"],
        motivo=motivo,
        score_probabilidade=score * 100,
        alegacao_nivel=nivel_risco(score),
    )
