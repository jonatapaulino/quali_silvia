"""Montagem da mensagem do usuário — placeholders do §5.7 e o bloco de
correção da re-tentativa §4.4. Função pura: recebe caso+score, devolve
texto — sem transporte, sem validação de schema.
"""

import json

from ..regras import nivel_risco
from .prompts import NARRATIVA_MAX_CHARS


def montar_contexto(caso: dict, score: float) -> str:
    """Monta a mensagem do usuário com os placeholders do §5.7."""
    evidencias = "\n".join(
        f"[{e['doc_id']}] {e.get('titulo', '')} | artigos: "
        f"{', '.join(e.get('artigos', []))}\n{e.get('trecho', '')}"
        for e in caso.get("evidencias", [])
    )
    metadados = json.dumps(caso.get("metadados", {}), ensure_ascii=False)
    return (
        "[CONTEXTO]\n"
        f"score_tabular_percentual: {score * 100:.1f}\n"
        f"nivel_risco_sistema: {nivel_risco(score).value}\n"
        f"alerta_cav: {caso.get('alerta_cav', 'ausente')}\n"
        "[METADADOS]\n"
        f"{metadados}\n"
        "[EVIDÊNCIAS]\n"
        f"{evidencias or 'nenhuma evidência recuperada'}\n"
        "[NARRATIVA]\n"
        f"{caso.get('narrativa', '')[:NARRATIVA_MAX_CHARS]}\n"
        "[TAREFA]\n"
        "Preencha o schema com base apenas no contexto acima."
        + _bloco_correcao(caso)
    )


def _bloco_correcao(caso: dict) -> str:
    """§4.4 — feedback da checagem determinística na re-tentativa."""
    erros = caso.get("correcao_fundamentacao")
    if not erros:
        return ""
    lista = "\n".join(f"- {e}" for e in erros)
    return (
        "\n[CORREÇÃO OBRIGATÓRIA]\n"
        "A tentativa anterior foi rejeitada pelo verificador de fundamentação "
        "com os erros:\n" + lista + "\n"
        "Reescreva usando SOMENTE doc_id e artigo exatamente como listados em "
        "[EVIDÊNCIAS] (ex.: doc_id 'lei11340_art22', artigo 'Art. 22')."
    )
