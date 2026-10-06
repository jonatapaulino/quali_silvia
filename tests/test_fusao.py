"""§5.6 — fusão RRF e Hit Rate@k."""

import pytest

from arquitetura_tese.fusao import hit_rate_at_k, rrf


def test_rrf_doc_em_ambos_os_rankings_vence():
    bm25 = ["doc_a", "doc_b", "doc_c"]
    faiss = ["doc_x", "doc_a", "doc_y"]
    fundido = rrf([bm25, faiss])
    assert fundido[0][0] == "doc_a"


def test_rrf_ordena_e_retorna_scores():
    fundido = rrf([["a", "b"], ["b", "c"]], k=60)
    ids = [d for d, _ in fundido]
    assert ids[0] == "b"
    assert all(fundido[i][1] >= fundido[i + 1][1] for i in range(len(fundido) - 1))


def test_hit_rate_at_5():
    resultados = {"q1": ["d1", "d2"], "q2": ["d9"], "q3": ["d3", "d4", "d5", "d6", "d7", "d8"]}
    gold = {"q1": {"d2"}, "q2": {"d9"}, "q3": {"d8"}}  # d8 na posição 6 -> fora do @5
    assert hit_rate_at_k(resultados, gold, k=5) == pytest.approx(2 / 3)


def test_hit_rate_vazio_retorna_intersecao():
    assert hit_rate_at_k({"q1": []}, {"q1": {"d1"}}, k=5) == 0.0
