"""Infraestrutura de recuperação HyPA-RAG — Fase 2 (DDA v5.3 §4.2, D2, D6).

Corpus = dispositivos legais (texto oficial do planalto) + narrativas
sintéticas. Cada documento carrega o metadado "artigos" (contrato do
checar_fundamentacao, §4.4).

Arquitetura incremental (D6): BM25 e FAISS como ramos independentes fundidos
por RRF (§5.6). O grafo entra só se a ablação provar ganho sobre o melhor
componente isolado — a interface `buscador_grafo` é o ponto de injeção.
"""

import json
import re
import unicodedata
from pathlib import Path

import numpy as np

from .fusao import rrf

RAIZ = Path(__file__).resolve().parents[1]
CORPUS_LEGAL = RAIZ / "conjuntos" / "corpus_legal.jsonl"
NARRATIVAS = RAIZ / "dados" / "narrativas_sinteticas.jsonl"


def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def tokenizar(t: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", normalizar(t))


def montar_corpus(corpus_legal=CORPUS_LEGAL, narrativas=NARRATIVAS,
                  tipos: tuple | None = None) -> list[dict]:
    """Documentos indexáveis: dispositivos legais + narrativas (doc_id narr_*)."""
    docs = []
    for l in Path(corpus_legal).open(encoding="utf-8"):
        d = json.loads(l)
        docs.append({
            "doc_id": d["doc_id"], "tipo": "dispositivo", "lei": d["lei"],
            "artigos": d["artigos"], "titulo": f"{d['lei']} — {d['artigo']}",
            "texto": f"{d['lei']} {d['artigo']} {d['tema']}. {d['texto']}",
        })
    if Path(narrativas).exists():
        for l in Path(narrativas).open(encoding="utf-8"):
            d = json.loads(l)
            docs.append({
                "doc_id": f"narr_{d['id_episodio']}", "tipo": "narrativa",
                "lei": "", "artigos": [x["artigo"] for x in d["dispositivos_sugeridos"]],
                "titulo": f"Episódio {d['id_episodio']} — {d.get('classe') or ''}",
                "texto": d["narrativa"],
            })
    if tipos is not None:
        docs = [d for d in docs if d["tipo"] in tipos]
    return docs


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


# ---------- Encoders (D2: benchmark no dev do gold set) ----------

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
