"""Compatibilidade — implementação migrada para servicos/guardiao.py.
Código novo deve importar de arquitetura_tese.servicos.guardiao."""

from .servicos.guardiao import PADROES_INJECAO, checar_ingestao, detectar_injecao

__all__ = ["PADROES_INJECAO", "checar_ingestao", "detectar_injecao"]
