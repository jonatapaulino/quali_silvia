"""Índices de recuperação: BM25 (lexical) e denso (FAISS + encoder).

Arquitetura incremental (D6): ramos independentes fundidos por RRF (§5.6).
O grafo entra só se a ablação provar ganho sobre o melhor componente
isolado — a interface `buscador_grafo` é o ponto de injeção.
"""

import numpy as np

from .fusao import rrf
from .texto import tokenizar


class IndiceBM25:
    def __init__(self, docs: list[dict]):
        from rank_bm25 import BM25Okapi

        self.docs = docs
        self.indice = BM25Okapi([tokenizar(d["texto"]) for d in docs])

    def buscar(self, consulta: str, k: int = 10) -> list[str]:
        scores = self.indice.get_scores(tokenizar(consulta))
        top = np.argsort(scores)[::-1][:k]
        return [self.docs[i]["doc_id"] for i in top if scores[i] > 0]


class IndiceDenso:
    """FAISS IndexFlatIP sobre embeddings normalizados (= cosseno)."""

    def __init__(self, docs: list[dict], encoder):
        import faiss

        self.docs = docs
        self.encoder = encoder
        emb = encoder.encode([d["texto"] for d in docs], normalize_embeddings=True)
        self.indice = faiss.IndexFlatIP(emb.shape[1])
        self.indice.add(np.asarray(emb, dtype="float32"))

    def buscar(self, consulta: str, k: int = 10) -> list[str]:
        q = self.encoder.encode([consulta], normalize_embeddings=True)
        _, idx = self.indice.search(np.asarray(q, dtype="float32"), k)
        return [self.docs[i]["doc_id"] for i in idx[0] if i >= 0]


def hibrido(rankings: list[list[str]], k_rrf: int = 60) -> list[str]:
    return [doc_id for doc_id, _ in rrf(rankings, k=k_rrf)]


def concordancia_top(ranking_a: list[str], ranking_b: list[str], k: int = 5) -> float:
    """Jaccard entre os Top-k dos dois ramos — alimenta incerteza() do §5.2."""
    a, b = set(ranking_a[:k]), set(ranking_b[:k])
    return len(a & b) / len(a | b) if (a or b) else 0.0
