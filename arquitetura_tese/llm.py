"""Chamada ao Ollama com saída estruturada — DDA v5.3 §5.5."""

import json

import httpx

from .prompts import NARRATIVA_MAX_CHARS, SYSTEM_PROMPT
from .regras import nivel_risco
from .schemas import LaudoLLM

MODELO = "mistral:7b"  # [VERIFICAR] tag exata e quantização (Q4 vs Q8 na RTX 5090)
# Calibrado acima do [PROPOSTA] 600 do DDA: a soma dos max_length do LaudoLLM
# (~3.600 chars ≈ >1.200 tokens em PT) truncaria o JSON e derrubaria o Pass
# Rate (§4.3). Re-medir a latência na Fase 3 e reajustar.
NUM_PREDICT = 1500


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


async def chamar_ollama(
    client: httpx.AsyncClient,
    caso: dict,
    score: float,
    base_url: str = "http://localhost:11434",
    timeout_s: float = 10.0,
) -> LaudoLLM:
    payload = {
        "model": MODELO,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": montar_contexto(caso, score)},
        ],
        "format": LaudoLLM.model_json_schema(),  # JSON Schema como restrição de saída
        "stream": False,
        "keep_alive": "30m",
        "options": {"temperature": 0, "num_predict": NUM_PREDICT, "seed": 42,
                    "num_ctx": 4096},
    }
    r = await client.post(base_url + "/api/chat", json=payload, timeout=timeout_s)
    r.raise_for_status()
    return LaudoLLM.model_validate_json(r.json()["message"]["content"])
