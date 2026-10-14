"""Transporte Ollama + validação de saída estruturada — DDA v5.3 §5.5.

Camada de fronteira: sabe falar HTTP com o Ollama e validar a resposta
contra o schema LaudoLLM. Não sabe montar contexto (ver contexto.py) nem
aplicar políticas de retry/degradação (ver servicos/).
"""

import httpx

from ..config import LLM_TIMEOUT_S, OLLAMA_URL
from ..schemas import LaudoLLM
from .contexto import montar_contexto
from .prompts import SYSTEM_PROMPT

MODELO = "mistral:7b"  # [VERIFICAR] tag exata e quantização (Q4 vs Q8 na RTX 5090)
# Calibrado acima do [PROPOSTA] 600 do DDA: a soma dos max_length do LaudoLLM
# (~3.600 chars ≈ >1.200 tokens em PT) truncaria o JSON e derrubaria o Pass
# Rate (§4.3). Re-medir a latência na Fase 3 e reajustar.
NUM_PREDICT = 1500


async def chamar_ollama(
    client: httpx.AsyncClient,
    caso: dict,
    score: float,
    base_url: str = OLLAMA_URL,
    timeout_s: float = LLM_TIMEOUT_S,
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
