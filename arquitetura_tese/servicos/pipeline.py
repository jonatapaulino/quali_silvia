"""Orquestração do laudo — fluxo síncrono medido no SLA de 8,5 s (D5, §4.0).

Composição dos ramos: score tabular → health probe/breaker → geração LLM →
verificação determinística de citações (§4.4, com UMA re-tentativa) →
montagem determinística do LaudoFinal. Imports de borda (llm/tabular) são
tardios de propósito: processos que só usam o LLM não carregam lightgbm,
e os testes podem substituir a fronteira pelo monkeypatch.
"""

import httpx

from ..config import OLLAMA_URL
from ..regras import aplicar_override, incerteza, nivel_risco
from ..schemas import (
    Dados,
    LaudoFinal,
    LaudoLLM,
    NivelRisco,
    Qualificador,
)
from .resiliencia import CircuitBreaker, laudo_degradado, llm_saudavel


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
    from ..llm import chamar_ollama
    from ..schemas import checar_fundamentacao

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
    from ..tabular import predizer_tabular

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
