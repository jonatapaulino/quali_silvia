"""Fusão RRF e métrica Hit Rate@k — DDA v5.3 §5.6.

score_RRF(d) = Σ_r 1 / (k + posição_r(d)), k=60 como valor inicial da
literatura [PROPOSTA: ajustar no dev do gold set].
"""


def rrf(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    pontos: dict[str, float] = {}
    for ranking in rankings:
        for pos, doc_id in enumerate(ranking, start=1):
            pontos[doc_id] = pontos.get(doc_id, 0.0) + 1.0 / (k + pos)
    return sorted(pontos.items(), key=lambda x: x[1], reverse=True)


def hit_rate_at_k(
    resultados: dict[str, list[str]], gold: dict[str, set[str]], k: int = 5
) -> float:
    acertos = sum(1 for q, docs in resultados.items() if gold[q] & set(docs[:k]))
    return acertos / len(gold)
