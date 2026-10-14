"""Compatibilidade — implementação migrada para llm/prompts.py.
Código novo deve importar de arquitetura_tese.llm.prompts."""

from .llm.prompts import NARRATIVA_MAX_CHARS, SYSTEM_PROMPT

__all__ = ["NARRATIVA_MAX_CHARS", "SYSTEM_PROMPT"]
