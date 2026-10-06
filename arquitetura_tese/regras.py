"""Nível de risco, Qualificador e override CAV — DDA v5.3 §5.2 e §5.3.

Determinísticos (D4-b): incerteza responde "quão confiável é a predição";
nível de risco responde "quão alto é o risco predito". As funções recebem a
probabilidade em 0-1 (o schema guarda 0-100).
"""

from .schemas import Incerteza, NivelRisco

# Limiares D8 [PROPOSTA] — recalibrar com dados reais antes de escala.
LIMIARES: tuple[tuple[float, NivelRisco], ...] = (
    (0.75, NivelRisco.CRITICO),
    (0.50, NivelRisco.ALTO),
    (0.25, NivelRisco.MODERADO),
)


def nivel_risco(p: float) -> NivelRisco:
    for limiar, nivel in LIMIARES:
        if p >= limiar:
            return nivel
    return NivelRisco.BAIXO


def incerteza(p: float, concordancia: float, flags_qualidade: list[str]) -> Incerteza:
    """concordancia = Jaccard entre os Top-5 de BM25 e FAISS (0-1)."""
    margem = abs(p - 0.5)
    if flags_qualidade or margem < 0.15 or concordancia < 0.2:
        return Incerteza.ALTA
    if margem >= 0.35 and concordancia >= 0.5:
        return Incerteza.BAIXA
    return Incerteza.MODERADA


FLAG_DIVERGENCIA = "Divergência Latente Detectada - Revisão Humana Obrigatória"

# Override estendido a MODERADO (§5.3, decisão registrada): erro assimétrico
# torna falso negativo mais grave — CAV crítico + risco baixo/moderado pede
# revisão humana (§8).
NIVEIS_DIVERGENTES = (NivelRisco.BAIXO, NivelRisco.MODERADO)


def aplicar_override(nivel: NivelRisco, cav_critico: bool, laudo: dict) -> dict:
    if cav_critico and nivel in NIVEIS_DIVERGENTES:
        laudo["refutacao_flags"].append(FLAG_DIVERGENCIA)
        laudo["revisao_humana_obrigatoria"] = True
    return laudo
