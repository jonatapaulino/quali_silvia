"""Auditoria da base_sintetica_risco.xlsx — insumo da Fase 1 e do teste de
vazamento do §4.5.

Verifica: shape, nulos, balanceamento do alvo, correlação ponto-bisserial de
cada feature numérica com nova_agressao (inclui os artefatos de geração
prob_geracao/score_geracao/perfil_risco_agressor — candidatos a vazamento),
distribuição de episódios por agressor (viabilidade do grafo, D6) e cardinalidade
das categóricas.

Uso: python scripts/analisar_base.py
"""

import math
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from arquitetura_tese.dados.narrativas import iterar_episodios

XLSX = RAIZ / "dados" / "base_sintetica_risco.xlsx"
TARGET = "nova_agressao"
ARTEFATOS_GERACAO = ["prob_geracao", "score_geracao", "perfil_risco_agressor"]
FEATURES_BINARIAS = [
    "ameaca_morte", "acesso_arma", "uso_alcool_drogas", "separacao_recente",
    "descumpriu_medida", "filhos_comum", "desemprego_agressor", "controle_coercitivo",
]
FEATURES_NUMERICAS = ["n_episodios_anteriores", "idade_requerido", "idade_vitima"]
CATEGORICAS = ["local", "classe", "situacao_processo", "escolaridade_requerido",
               "escolaridade_vitima", "sexo_requerido", "sexo_vitima", "perfil_risco_agressor"]


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx * dy else float("nan")


def main() -> None:
    linhas = [e for e in iterar_episodios(XLSX) if e.get("id_episodio")]
    print(f"registros: {len(linhas)}")

    nulos = Counter()
    for e in linhas:
        for k, v in e.items():
            if v is None or str(v).strip() == "":
                nulos[k] += 1
    print("nulos por coluna:", dict(nulos.most_common(10)) or "nenhum")

    rotulados = [e for e in linhas if _f(e.get(TARGET)) is not None]
    ys = [_f(e[TARGET]) for e in rotulados]
    pos = sum(ys)
    print(f"alvo {TARGET}: {int(pos)} pos / {len(ys) - int(pos)} neg "
          f"({pos / len(ys):.1%} positivo) | sem rótulo: {len(linhas) - len(rotulados)}")

    print("\n-- correlação ponto-bisserial com nova_agressao --")
    candidatas = FEATURES_BINARIAS + FEATURES_NUMERICAS + ["prob_geracao", "score_geracao"]
    for col in candidatas:
        xs = [_f(e.get(col)) for e in rotulados]
        pares = [(x, y) for x, y in zip(xs, ys) if x is not None]
        if not pares:
            continue
        xs2, ys2 = zip(*pares)
        r = pearson(list(xs2), list(ys2))
        marca = "  <-- PROVÁVEL VAZAMENTO" if abs(r) > 0.7 else ""
        print(f"  {col:28s} r={r:+.3f}{marca}")

    print("\n-- perfil_risco_agressor x nova_agressao (crosstab) --")
    tab: dict[str, list[int]] = {}
    for e, y in zip(rotulados, ys):
        tab.setdefault(str(e.get("perfil_risco_agressor")), [0, 0])
        tab[str(e.get("perfil_risco_agressor"))][0] += int(y)
        tab[str(e.get("perfil_risco_agressor"))][1] += 1
    for k, (p, n) in sorted(tab.items()):
        print(f"  {k:12s} taxa_pos={p / n:.3f}  (n={n})")

    print("\n-- episódios por agressor (viabilidade do grafo, D6) --")
    eps_por_agr = Counter(e["id_agressor_sintetico"] for e in linhas)
    dist = Counter(eps_por_agr.values())
    for k in sorted(dist):
        print(f"  {k} episódio(s): {dist[k]} agressores")
    multi = sum(1 for n in eps_por_agr.values() if n >= 2)
    print(f"  agressores com >=2 episódios (arestas do grafo): {multi}")

    print("\n-- categóricas (top 6) --")
    for col in CATEGORICAS:
        vals = Counter(str(e.get(col)) for e in linhas)
        print(f"  {col}: {vals.most_common(6)}")


if __name__ == "__main__":
    main()
