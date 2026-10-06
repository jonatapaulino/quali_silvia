"""Montagem do placeholder {evidencias} do §5.7 — Fase 3.

Duas fontes (D6 denso-isolado, encoder BGE-M3 escolhido na Fase 2):
- dispositivos legais: alimentam garantia_dispositivos (citáveis, §4.4);
- narrativas similares: alimentam apoio ("caso de apoio" — nunca citáveis).
"""

from . import recuperacao

TRECHO_MAX_CHARS = 900  # mantém o prompt enxuto; dispositivo médio ~500 chars
K_DISPOSITIVOS = 5      # top-k do ramo de fundamentação
K_APOIO = 2             # casos similares — enxuto para caber no SLA


def montar_indices(encoder=None):
    """Índices densos por tipo de corpus. Cache em módulo para reuso entre
    requisições — a codificação dos 300+22 documentos ocorre uma única vez."""
    enc = encoder or recuperacao.ENCODERS["bge_m3"]()
    disp = recuperacao.IndiceDenso(
        recuperacao.montar_corpus(tipos=("dispositivo",)), enc)
    narrs = recuperacao.IndiceDenso(
        recuperacao.montar_corpus(tipos=("narrativa",)), enc)
    return enc, {"dispositivo": disp, "narrativa": narrs}


def montar_evidencias(narrativa: str, indices: dict,
                      excluir_doc: str | None = None) -> list[dict]:
    """doc_id/titulo/artigos/trecho — formato esperado por montar_contexto."""
    evidencias = []
    for tipo, k in (("dispositivo", K_DISPOSITIVOS), ("narrativa", K_APOIO)):
        idx = indices[tipo]
        por_id = {d["doc_id"]: d for d in idx.docs}
        for doc_id in idx.buscar(narrativa, k + (1 if excluir_doc else 0)):
            if doc_id == excluir_doc:
                continue
            d = por_id[doc_id]
            evidencias.append({
                "doc_id": doc_id, "titulo": d["titulo"], "artigos": d["artigos"],
                "trecho": d["texto"][:TRECHO_MAX_CHARS],
            })
            if len(evidencias) >= K_DISPOSITIVOS + K_APOIO:
                return evidencias
    return evidencias
