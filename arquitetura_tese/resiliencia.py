"""Health check inline + circuit breaker + orquestração do laudo — §5.4.

Cobre os cenários de caos do §4.7: contêiner parado (a), travado (b) e pane
durante a geração (c). Em todos, resposta degradada via LaudoDegradado.
"""

import time

import httpx

from .regras import aplicar_override, incerteza, nivel_risco
from .schemas import (
    Dados,
    LaudoDegradado,
    LaudoFinal,
    LaudoLLM,
    NivelRisco,
    Qualificador,
)

OLLAMA_URL = "http://localhost:11434"
PROBE_TIMEOUT_S = 0.3
LLM_TIMEOUT_S = 10.0  # [PROPOSTA] §4.7 cenário (c)


class CircuitBreaker:
    def __init__(self, falhas_max: int = 3, reabrir_apos_s: float = 15.0):
        self.falhas_max = falhas_max
        self.reabrir_apos_s = reabrir_apos_s
        self.falhas = 0
        self.aberto_em: float | None = None

    def permite(self) -> bool:  # meia-abertura
        if self.aberto_em is None:
            return True
        return time.monotonic() - self.aberto_em >= self.reabrir_apos_s

    def sucesso(self) -> None:
        self.falhas = 0
        self.aberto_em = None

    def falha(self) -> None:
        self.falhas += 1
        if self.falhas >= self.falhas_max:
            self.aberto_em = time.monotonic()


async def llm_saudavel(client: httpx.AsyncClient, base_url: str = OLLAMA_URL) -> bool:
    try:
        r = await client.get(base_url + "/", timeout=PROBE_TIMEOUT_S)
        return r.status_code == 200
    except httpx.HTTPError:  # inclui timeout e conexão recusada
        return False


def laudo_degradado(caso: dict, score: float, motivo: str) -> LaudoDegradado:
    return LaudoDegradado(
        trace_id=caso["trace_id"],
        motivo=motivo,
        score_probabilidade=score * 100,
        alegacao_nivel=nivel_risco(score),
    )


def montar_laudo(
    caso: dict,
    score: float,
    bruto: LaudoLLM,
    concordancia: float = 0.0,
    flags_qualidade: list[str] | None = None,
) -> LaudoFinal:
    """Monta LaudoFinal: eixo Dados copiado da entrada, nível e Qualificador
    determinísticos, override CAV aplicado antes da validação (§5.3)."""
    flags = flags_qualidade or []
    nivel = nivel_risco(score)
    d = {
        "trace_id": caso["trace_id"],
        "alegacao_nivel": nivel.value,
        "alegacao_enunciado": bruto.alegacao_enunciado,
        "dados": Dados(
            score_probabilidade=score * 100,
            metadados=caso.get("metadados", {}),
        ).model_dump(),
        "garantia_dispositivos": [g.model_dump() for g in bruto.garantia_dispositivos],
        "garantia_raciocinio": bruto.garantia_raciocinio,
        "apoio": [a.model_dump() for a in bruto.apoio],
        "refutacao": bruto.refutacao,
        "refutacao_flags": [],
        "qualificador": Qualificador(
            incerteza=incerteza(score, concordancia, flags),
            motivos=flags or ["cálculo padrão §5.2"],
        ).model_dump(),
        # §8: revisão humana obrigatória em Alto/Crítico; override pode forçar.
        "revisao_humana_obrigatoria": nivel in (NivelRisco.ALTO, NivelRisco.CRITICO),
    }
    aplicar_override(nivel, bool(caso.get("cav_critico", False)), d)
    return LaudoFinal(**d)


async def gerar_fundamentado(client: httpx.AsyncClient, caso: dict,
                             score: float, base_url: str = OLLAMA_URL):
    """§4.4 — gera + valida citações + UMA re-tentativa com feedback do erro.

    Retorna (LaudoLLM, erros_restantes, tentativas)."""
    from .llm import chamar_ollama
    from .schemas import checar_fundamentacao

    recuperados = {e["doc_id"]: e for e in caso.get("evidencias", [])}
    bruto = await chamar_ollama(client, caso, score, base_url)
    erros = checar_fundamentacao(bruto, recuperados)
    if not erros:
        return bruto, [], 1
    caso2 = {**caso, "correcao_fundamentacao": erros}
    bruto2 = await chamar_ollama(client, caso2, score, base_url)
    erros2 = checar_fundamentacao(bruto2, recuperados)
    return (bruto2, erros2, 2) if len(erros2) <= len(erros) else (bruto, erros, 1)


async def gerar_laudo(caso: dict, client: httpx.AsyncClient,
                      breaker: CircuitBreaker,
                      base_url: str = OLLAMA_URL):
    """Fluxo síncrono medido no SLA de 8,5 s (D5, §4.0)."""
    from .llm import chamar_ollama
    from .schemas import checar_fundamentacao
    from .tabular import predizer_tabular

    score = predizer_tabular(caso)  # LightGBM, local e rápido

    if not breaker.permite():
        return laudo_degradado(caso, score, "circuit_open")

    if not await llm_saudavel(client, base_url):
        breaker.falha()
        return laudo_degradado(caso, score, "llm_indisponivel")

    try:
        bruto, erros, _ = await gerar_fundamentado(client, caso, score, base_url)
        breaker.sucesso()
    except (httpx.HTTPError, ValueError):  # ValidationError herda de ValueError
        breaker.falha()
        return laudo_degradado(caso, score, "llm_timeout")

    flags = list(caso.get("flags_qualidade") or [])
    if erros:
        flags.append("fundamentacao_pendente:revisao_humana")
    return montar_laudo(
        caso, score, bruto,
        concordancia=caso.get("concordancia", 0.0),
        flags_qualidade=flags,
    )
