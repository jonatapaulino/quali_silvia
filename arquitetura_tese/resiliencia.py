"""Compatibilidade — a implementação migrou para servicos/.

servicos/resiliencia.py: mecanismos (breaker, health probe, degradado);
servicos/pipeline.py: orquestração (montar_laudo, gerar_fundamentado,
gerar_laudo). Este módulo re-exporta a API antiga — código novo deve
importar de arquitetura_tese.servicos diretamente.
"""

from .config import LLM_TIMEOUT_S, OLLAMA_URL, PROBE_TIMEOUT_S
from .servicos.pipeline import gerar_fundamentado, gerar_laudo, montar_laudo
from .servicos.resiliencia import (
    CircuitBreaker,
    laudo_degradado,
    llm_saudavel,
)

__all__ = [
    "CircuitBreaker", "llm_saudavel", "laudo_degradado",
    "montar_laudo", "gerar_fundamentado", "gerar_laudo",
    "OLLAMA_URL", "PROBE_TIMEOUT_S", "LLM_TIMEOUT_S",
]
