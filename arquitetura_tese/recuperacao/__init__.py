"""Recuperação de informação HyPA-RAG — fachada pública do pacote.

Divisão interna por responsabilidade:
- texto.py: preprocessamento lexical (normalizar/tokenizar);
- fontes.py: montagem do corpus (acesso a dados, conjuntos/);
- indices.py: IndiceBM25, IndiceDenso, hibrido, concordancia_top;
- fusao.py: RRF e Hit Rate@k (§5.6);
- encoders.py: factories de SentenceTransformer do benchmark (D2).

Imports antigos (`from arquitetura_tese.recuperacao import X`) continuam
válidos — este __init__ re-exporta a API pública.
"""

from .encoders import (ENCODERS, encoder_bge_m3, encoder_legal_bertimbau_base,
                       encoder_legal_bertimbau_sts)
from .fontes import montar_corpus
from .fusao import hit_rate_at_k, rrf
from .indices import IndiceBM25, IndiceDenso, concordancia_top, hibrido
from .texto import normalizar, tokenizar

__all__ = [
    "ENCODERS", "encoder_bge_m3", "encoder_legal_bertimbau_base",
    "encoder_legal_bertimbau_sts", "montar_corpus", "hit_rate_at_k", "rrf",
    "IndiceBM25", "IndiceDenso", "concordancia_top", "hibrido",
    "normalizar", "tokenizar",
]
