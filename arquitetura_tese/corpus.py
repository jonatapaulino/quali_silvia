"""Compatibilidade — implementação migrada para dados/corpus.py.
Código novo deve importar de arquitetura_tese.dados.corpus."""

from .dados.corpus import DISPOSITIVOS, corpus_para_indexacao

__all__ = ["DISPOSITIVOS", "corpus_para_indexacao"]
