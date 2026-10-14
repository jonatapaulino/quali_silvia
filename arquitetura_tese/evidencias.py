"""Compatibilidade — implementação migrada para servicos/evidencias.py.
Código novo deve importar de arquitetura_tese.servicos.evidencias."""

from .servicos.evidencias import (
    K_APOIO,
    K_DISPOSITIVOS,
    TRECHO_MAX_CHARS,
    montar_evidencias,
    montar_indices,
)

__all__ = [
    "K_APOIO", "K_DISPOSITIVOS", "TRECHO_MAX_CHARS",
    "montar_evidencias", "montar_indices",
]
