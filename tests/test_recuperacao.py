"""§4.2 — corpus, índices BM25/denso, concordância e avaliação."""

import json

import numpy as np
import pytest

from arquitetura_tese import recuperacao
from arquitetura_tese.fusao import hit_rate_at_k

DOCS = [
    {"doc_id": "cp_art147", "tipo": "dispositivo", "lei": "Código Penal",
     "artigos": ["Art. 147"], "titulo": "CP — Art. 147",
     "texto": "Código Penal Art. 147 ameaça. Ameaçar alguém, por palavra, escrito ou gesto."},
    {"doc_id": "lei11340_art24a", "tipo": "dispositivo", "lei": "Lei 11.340/2006",
     "artigos": ["Art. 24-A"], "titulo": "LMP — Art. 24-A",
     "texto": "Lei 11.340 Art. 24-A descumprimento de medida protetiva de urgência."},
    {"doc_id": "narr_EP1", "tipo": "narrativa", "lei": "",
     "artigos": ["Art. 147"], "titulo": "Episódio EP1",
     "texto": "BOLETIM — a vítima relata ameaça de morte feita pelo companheiro."},
]


def test_bm25_recupera_dispositivo_por_tema():
    idx = recuperacao.IndiceBM25(DOCS)
    top = idx.buscar("crime de ameaçar alguém por palavra ou gesto", k=3)
    assert "cp_art147" in top


def test_bm25_ranking_respeita_k():
    idx = recuperacao.IndiceBM25(DOCS)
    assert len(idx.buscar("violência doméstica", k=2)) <= 2


class EncoderFake:
    """Embeddings determinísticos para testar o índice denso sem torch."""

    def encode(self, textos, normalize_embeddings=True, **kw):
        rng = np.random.RandomState(len(textos))
        v = rng.rand(len(textos), 8).astype("float32")
        return v / np.linalg.norm(v, axis=1, keepdims=True)


def test_indice_denso_forma_do_resultado():
    idx = recuperacao.IndiceDenso(DOCS, EncoderFake())
    top = idx.buscar("consulta qualquer", k=3)
    assert len(top) <= 3
    assert all(d in {d["doc_id"] for d in DOCS} for d in top)


def test_concordancia_jaccard():
    assert recuperacao.concordancia_top(["a", "b"], ["a", "b"], k=2) == 1.0
    assert recuperacao.concordancia_top(["a"], ["b"], k=1) == 0.0
    assert recuperacao.concordancia_top(["a", "b"], ["b", "c"], k=2) == pytest.approx(1 / 3)


def test_hibrido_funde_dois_rankings():
    fundido = recuperacao.hibrido([["a", "b"], ["b", "c"]])
    assert fundido[0] == "b"


def test_corpus_docs_tem_metadado_artigos(tmp_path):
    legal = tmp_path / "legal.jsonl"
    legal.write_text(json.dumps(
        {"doc_id": "cp_art147", "lei": "Código Penal", "artigo": "Art. 147",
         "tema": "ameaça", "artigos": ["Art. 147"], "texto": "Ameaçar alguém."}
    ) + "\n", encoding="utf-8")
    narrs = tmp_path / "narr.jsonl"
    narrs.write_text(json.dumps(
        {"id_episodio": "EP1", "id_agressor_sintetico": "a", "id_vitima_sintetica": "v",
         "classe": "Inquérito Policial", "narrativa": "texto", "conceitos": [],
         "dispositivos_sugeridos": [{"doc_id": "cp_art147", "lei": "CP", "artigo": "Art. 147"}]}
    ) + "\n", encoding="utf-8")
    docs = recuperacao.montar_corpus(legal, narrs)
    assert all("artigos" in d for d in docs)   # contrato §4.4
    assert {d["doc_id"] for d in docs} == {"cp_art147", "narr_EP1"}
