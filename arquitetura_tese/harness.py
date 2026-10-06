"""Harness de latência e intervalos de confiança — DDA v5.3 §6.5."""

import time
from math import sqrt

import numpy as np


def medir(casos: list, pipeline, n_warmup: int = 5) -> dict:
    for c in casos[:n_warmup]:
        pipeline(c, cronometro={})  # aquecimento, descartado (§4.0)
    linhas = []
    for c in casos:
        t: dict = {}
        t0 = time.perf_counter()
        pipeline(c, cronometro=t)  # preenche t["guardioes"], t["retrieval"], ...
        t["total"] = time.perf_counter() - t0
        linhas.append(t)
    resumo = {}
    for etapa in linhas[0]:
        v = np.array([l[etapa] for l in linhas])
        resumo[etapa] = {q: float(np.percentile(v, q)) for q in (50, 95, 99)}
    return resumo


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    margem = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return centro - margem, centro + margem
