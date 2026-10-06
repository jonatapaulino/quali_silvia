"""§4.6 — Probe linear de conceitos (D3-b): AUC por conceito em holdout.

Representação: embedding BGE-M3 da narrativa (mesma camada usada na
recuperação — o probe mede se a representação carrega os conceitos críticos
que o Qualificador/override monitoram). Holdout por episódio, estratificado.
"""

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

NARRATIVAS = RAIZ / "dados" / "narrativas_sinteticas.jsonl"
MIN_POSITIVOS = 15


def main() -> None:
    docs = [json.loads(l) for l in NARRATIVAS.open(encoding="utf-8")]
    conceitos = sorted({c for d in docs for c in d["conceitos"]})
    contagem = Counter(c for d in docs for c in d["conceitos"])
    alvos = [c for c in conceitos
             if MIN_POSITIVOS <= contagem[c] <= len(docs) - MIN_POSITIVOS]
    print(f"{len(docs)} docs; conceitos avaliáveis (>= {MIN_POSITIVOS} pos e neg): {alvos}")

    from arquitetura_tese import recuperacao
    enc = recuperacao.ENCODERS["bge_m3"]()
    X = np.asarray(enc.encode([d["narrativa"] for d in docs],
                              normalize_embeddings=True), dtype="float32")

    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedShuffleSplit

    resultados = {}
    rng = np.random.RandomState(42)
    for conceito in alvos:
        y = np.array([conceito in d["conceitos"] for d in docs], dtype=int)
        aucs = []
        for treino, teste in StratifiedShuffleSplit(
                5, test_size=0.25, random_state=rng).split(X, y):
            probe = LogisticRegression(max_iter=2000, C=1.0)
            probe.fit(X[treino], y[treino])
            aucs.append(roc_auc_score(y[teste], probe.predict_proba(X[teste])[:, 1]))
        resultados[conceito] = {
            "auc_media": round(float(np.mean(aucs)), 4),
            "auc_dp": round(float(np.std(aucs)), 4),
            "n_pos": int(y.sum()),
        }
        print(f"  {conceito}: AUC {resultados[conceito]['auc_media']} "
              f"±{resultados[conceito]['auc_dp']} (pos={y.sum()})")

    saida = {
        "metodo": "LogisticRegression(C=1) sobre BGE-M3, 5x StratifiedShuffleSplit 75/25",
        "n_docs": len(docs), "conceitos": resultados,
        "nota": "rótulos fracos do gerador sintético — valida o MECANISMO do "
                "probe (D3), não a presença real do conceito em texto judicial",
    }
    (RAIZ / "dados" / "metricas_cav.json").write_text(
        json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    print("-> dados/metricas_cav.json")


if __name__ == "__main__":
    main()
