"""Treina e avalia o modelo tabular — critério de saída da Fase 1: §4.5.

Gera dados/modelo_tabular.txt (+ .meta.json) e dados/metricas_tabular.json.
O run --com-controle treina um segundo modelo INCLUINDO os artefatos de geração
para demonstrar que o teste de permutação os flagraria como vazamento.

Uso: python scripts/treinar_tabular.py [--n 20000] [--com-controle]
"""

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import numpy as np

from arquitetura_tese import tabular


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--com-controle", action="store_true",
                    help="treina modelo de controle com artefatos (demonstra o teste §4.5)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    eps = tabular.carregar_episodios()
    X = tabular.featurizar(eps)
    y = tabular.alvo(eps)
    g = tabular.grupos(eps)
    tr, te = tabular.grupo_split(len(eps), g, seed=args.seed)

    X_tr, X_te = X.iloc[tr], X.iloc[te]
    y_tr, y_te = y[tr], y[te]
    print(f"treino {len(X_tr)} | teste {len(X_te)} | grupos disjuntos: ok")

    # split interno do TREINO para early stopping (o holdout de teste não
    # participa da decisão de parada — seria seleção no teste)
    fit_idx, val_idx = tabular.grupo_split(len(tr), g[tr], test_size=0.15,
                                           seed=args.seed)
    tr_fit, tr_val = tr[fit_idx], tr[val_idx]
    modelo = tabular.treinar(
        X.iloc[tr_fit], y[tr_fit], validacao=(X.iloc[tr_val], y[tr_val]))
    best_it = getattr(modelo, "best_iteration_", None)
    print(f"early stopping: melhor iteração = {best_it} "
          f"(teto 2000; treino interno {len(tr_fit)} + validação {len(tr_val)})")
    metricas = tabular.avaliar(modelo, X_te, y_te)
    imp = tabular.importancia_permutacao(modelo, X_te, y_te)

    metricas.update({
        "n_treino": len(X_tr), "n_teste": len(X_te), "seed": args.seed,
        "prevalencia_holdout": float(y_te.mean()),
        "split": "grouped_by_id_agressor_sintetico (GroupShuffleSplit 80/20)",
        "early_stopping": {
            "best_iteration": int(best_it) if best_it else None,
            "validacao_interna": f"{len(tr_val)} episódios (grupos disjuntos do fit)",
        },
        "top_importancia": imp[:8],
        "features_proibidas_no_modelo": [
            f for f in X.columns if any(b in f for b in tabular.FEATURES_PROIBIDAS)
        ],
        "nota": "Prevalência sintética ~50/50 difere da real: o escore não é "
                "interpretável como risco absoluto até recalibração (§4.5, D8).",
    })

    if args.com_controle:
        # controle §4.5: modelo COM os artefatos — a permutação deve flagrá-los
        import pandas as pd

        Xc = X.copy()
        Xc["prob_geracao"] = [tabular._f(e.get("prob_geracao")) for e in eps]
        Xc["score_geracao"] = [tabular._f(e.get("score_geracao")) for e in eps]
        Xc["perfil_risco_agressor"] = pd.Categorical(
            [str(e.get("perfil_risco_agressor")) for e in eps]).codes
        m_ctrl = tabular.treinar(Xc.iloc[tr], y_tr)
        imp_ctrl = tabular.importancia_permutacao(m_ctrl, Xc.iloc[te], y_te)
        metricas["controle_com_artefatos"] = {
            "top_importancia": imp_ctrl[:5],
            "demonstra": "os artefatos dominam a importância quando incluídos",
        }

    tabular.salvar(modelo, list(X.columns), meta_extra={"metricas_holdout": {
        "auc": metricas["auc"], "brier": metricas["brier"], "ece": metricas["ece"]}})

    saida = RAIZ / "dados" / "metricas_tabular.json"
    saida.write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in metricas.items() if k != "top_importancia"},
                     ensure_ascii=False, indent=2))
    print("top-5 permutação:", [(d["feature"], round(d["media"], 4)) for d in imp[:5]])
    print(f"-> {saida}")


if __name__ == "__main__":
    main()
