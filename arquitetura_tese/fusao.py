"""Compatibilidade — implementação migrada para recuperacao/fusao.py.
Código novo deve importar de arquitetura_tese.recuperacao.fusao."""

from .recuperacao.fusao import hit_rate_at_k, rrf

__all__ = ["hit_rate_at_k", "rrf"]
