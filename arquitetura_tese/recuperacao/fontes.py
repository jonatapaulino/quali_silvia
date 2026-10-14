"""Fontes documentais do corpus de recuperação — acesso a dados.

Corpus = dispositivos legais (texto oficial do planalto) + narrativas
sintéticas. Cada documento carrega o metadado "artigos" (contrato do
checar_fundamentacao, §4.4).
"""

import json
from pathlib import Path

from ..config import CORPUS_LEGAL, NARRATIVAS


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
