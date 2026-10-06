"""Evidências do §5.7 — montagem do contexto a partir dos índices densos."""

import numpy as np

from arquitetura_tese import evidencias, recuperacao


class EncoderFake:
    def encode(self, textos, normalize_embeddings=True, **kw):
        rng = np.random.RandomState(sum(len(t) for t in textos))
        v = rng.rand(len(textos), 8).astype("float32")
        return v / np.linalg.norm(v, axis=1, keepdims=True)


DOCS_DISP = [
    {"doc_id": "cp_art147", "tipo": "dispositivo", "lei": "CP",
     "artigos": ["Art. 147"], "titulo": "CP Art. 147", "texto": "ameaça"},
]
DOCS_NARR = [
    {"doc_id": "narr_EP1", "tipo": "narrativa", "lei": "",
     "artigos": ["Art. 147"], "titulo": "EP1", "texto": "caso similar um"},
    {"doc_id": "narr_EP2", "tipo": "narrativa", "lei": "",
     "artigos": [], "titulo": "EP2", "texto": "caso similar dois"},
]


def _indices():
    enc = EncoderFake()
    return {
        "dispositivo": recuperacao.IndiceDenso(DOCS_DISP, enc),
        "narrativa": recuperacao.IndiceDenso(DOCS_NARR, enc),
    }


def test_evidencias_tem_campos_do_prompt():
    ev = evidencias.montar_evidencias("consulta", _indices())
    assert ev
    for e in ev:
        assert {"doc_id", "titulo", "artigos", "trecho"} <= e.keys()


def test_evidencias_separa_dispositivos_e_apoio():
    ev = evidencias.montar_evidencias("consulta", _indices())
    n_disp = sum(not e["doc_id"].startswith("narr_") for e in ev)
    n_apoio = sum(e["doc_id"].startswith("narr_") for e in ev)
    assert n_disp <= evidencias.K_DISPOSITIVOS
    assert n_apoio <= evidencias.K_APOIO


def test_evidencias_exclui_proprio_documento():
    ev = evidencias.montar_evidencias(
        "consulta", _indices(), excluir_doc="narr_EP1")
    assert all(e["doc_id"] != "narr_EP1" for e in ev)


def test_trecho_truncado():
    doc_longo = {**DOCS_DISP[0], "texto": "x" * 5000}
    idx = {"dispositivo": recuperacao.IndiceDenso([doc_longo], EncoderFake()),
           "narrativa": recuperacao.IndiceDenso(DOCS_NARR, EncoderFake())}
    ev = evidencias.montar_evidencias("consulta", idx)
    assert len(ev[0]["trecho"]) <= evidencias.TRECHO_MAX_CHARS
