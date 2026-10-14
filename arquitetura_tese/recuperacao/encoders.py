"""Encoders densos — candidatos do benchmark D2/Fase 2 (§4.2).

Cada factory retorna um SentenceTransformer pronto para .encode(). Os
imports pesados ficam dentro das funções para não carregar torch em
processos que só usam BM25 ou o LLM.
"""


def _device() -> str:
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def encoder_legal_bertimbau_base():
    """(a) Legal-BERTimbau base + mean pooling — baseline sem treino STS."""
    from sentence_transformers import SentenceTransformer, models

    word = models.Transformer("rufimelo/Legal-BERTimbau-base", max_seq_length=512)
    pooling = models.Pooling(word.get_embedding_dimension(), pooling_mode="mean")
    return SentenceTransformer(modules=[word, pooling], device=_device())


def encoder_legal_bertimbau_sts():
    """(b) Variante STS do Legal-BERTimbau (treinada para similaridade)."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("rufimelo/Legal-BERTimbau-sts-base", device=_device())


def encoder_bge_m3():
    """(c) Embedding multilíngue denso de referência."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("BAAI/bge-m3", device=_device())


ENCODERS = {
    "legal_bertimbau_base": encoder_legal_bertimbau_base,
    "legal_bertimbau_sts": encoder_legal_bertimbau_sts,
    "bge_m3": encoder_bge_m3,
}
