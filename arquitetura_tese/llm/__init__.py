"""Camada LLM — fachada pública do pacote.

Divisão interna por responsabilidade:
- prompts.py: contrato de prompt §5.7 (SYSTEM_PROMPT);
- contexto.py: montagem da mensagem do usuário (função pura);
- cliente.py: transporte Ollama + validação LaudoLLM (fronteira externa).

Imports antigos (`from arquitetura_tese.llm import X`) continuam válidos.
"""

from .cliente import MODELO, NUM_PREDICT, chamar_ollama
from .contexto import montar_contexto
from .prompts import NARRATIVA_MAX_CHARS, SYSTEM_PROMPT

__all__ = [
    "MODELO", "NUM_PREDICT", "chamar_ollama", "montar_contexto",
    "NARRATIVA_MAX_CHARS", "SYSTEM_PROMPT",
]
