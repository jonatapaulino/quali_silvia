"""Geração das 4 figuras do relatório de smoke test — dados reais das Fases 1-4.

Saída: dados/figuras/{fig1_roc_importancia, fig2_hitrate, fig3_latencia,
fig4_guardiao_cav}.png

Fig1 recomputa a ROC no holdout real (grupo por agressor, seed 42) — não é uma
curva ilustrativa: são as predições verdadeiras do modelo salvo.
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
FIGS = RAIZ / "dados" / "figuras"
FIGS.mkdir(exist_ok=True)

AZUL, CINZA, VERDE, VERM = "#1f77b4", "#9e9e9e", "#2ca02c", "#d62728"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 140})


def fig1():
    """ROC real no holdout + importância por permutação (produção vs controle)."""
    import lightgbm as lgb
    from sklearn.metrics import roc_auc_score, roc_curve

    from arquitetura_tese.tabular import (alvo, carregar_episodios, featurizar,
                                  grupos, grupo_split, MODELO_PATH, META_PATH)

    eps = carregar_episodios()
    _, te = grupo_split(len(eps), grupos(eps))
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    booster = lgb.Booster(model_file=str(MODELO_PATH))
    X_te = featurizar([eps[i] for i in te]).reindex(
        columns=meta["colunas_modelo"], fill_value=0.0)
    y_te, p_te = alvo([eps[i] for i in te]), booster.predict(X_te)
    fpr, tpr, _ = roc_curve(y_te, p_te)
    auc = roc_auc_score(y_te, p_te)

    m = json.loads((RAIZ / "dados" / "metricas_tabular.json").read_text(encoding="utf-8"))
    top = sorted(m["top_importancia"], key=lambda x: x["media"])[-10:]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))
    ax1.plot(fpr, tpr, color=AZUL, lw=2, label=f"LightGBM — AUC = {auc:.3f}")
    ax1.plot([0, 1], [0, 1], "--", color=CINZA, lw=1, label="Aleatório (0,50)")
    ax1.fill_between(fpr, tpr, alpha=0.08, color=AZUL)
    ax1.set(xlabel="Taxa de Falsos Positivos", ylabel="Taxa de Verdadeiros Positivos",
            title=f"Curva ROC — holdout por agressor (n={len(y_te):,})".replace(",", "."))
    ax1.legend(loc="lower right")

    nomes = [t["feature"] for t in top]
    vals = [t["media"] for t in top]
    ax2.barh(nomes, vals, color=AZUL, xerr=[t["desvio"] for t in top])
    ax2.set(xlabel="Importância por permutação (Δ AUC)",
            title="Features legítimas — modelo de produção")
    ctrl = m.get("controle_com_artefatos", {})
    if ctrl:
        imp_ctrl = ctrl.get("top_importancia", [])
        legenda = "\n".join(f"{t['feature']}: {t['media']:.3f}"
                            for t in sorted(imp_ctrl, key=lambda x: -x["media"])[:3])
        ax2.text(0.98, 0.03,
                 f"Modelo-controle c/ artefatos:\n{legenda}",
                 transform=ax2.transAxes, ha="right", va="bottom", fontsize=8,
                 bbox=dict(boxstyle="round", fc="#fdecea", ec=VERM, alpha=0.9))
    fig.suptitle("Fase 1 — Modelo tabular sem vazamento (artefatos banidos por construção)",
                 y=1.02, fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGS / "fig1_roc_importancia.png", bbox_inches="tight")
    plt.close(fig)
    return auc


def fig2():
    m = json.loads((RAIZ / "dados" / "metricas_recuperacao.json").read_text(encoding="utf-8"))
    cfgs = [("BM25", m["test"]["bm25"]),
            ("FAISS BGE-M3\n(denso isolado)", m["test"]["vencedor"])]
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    x = np.arange(len(cfgs))
    hr = [c[1]["hit_rate"] for c in cfgs]
    err = [[c[1]["hit_rate"] - c[1]["ic95"][0] for c in cfgs],
           [c[1]["ic95"][1] - c[1]["hit_rate"] for c in cfgs]]
    ax.bar(x, hr, color=[CINZA, AZUL], width=0.55,
           yerr=err, capsize=6, error_kw=dict(lw=1.4, ecolor="#333"))
    for i, v in enumerate(hr):
        ax.text(i, v + err[1][i] + 0.015, f"{v:.0%}", ha="center", fontweight="bold")
    ax.axhline(0.85, ls="--", color=VERM, lw=1.3)
    ax.text(1.32, 0.855, "critério §4.2 = 0,85", color=VERM, fontsize=8, ha="right")
    n_test = cfgs[0][1]["n"]
    ax.set(xticks=x, xticklabels=[c[0] for c in cfgs], ylim=(0, 1.02),
           ylabel=f"Hit Rate@5 (conjunto teste, n={n_test})",
           title="Fase 2 — Ablação de recuperação (IC95 de Wilson)")
    fig.tight_layout()
    fig.savefig(FIGS / "fig2_hitrate.png", bbox_inches="tight")
    plt.close(fig)


def fig3():
    m = json.loads((RAIZ / "dados" / "metricas_latencia.json").read_text(encoding="utf-8"))
    e = m["estagios_ms"]
    comps = [("LightGBM (score)", e["tabular"]["p95"], AZUL),
             ("Retrieval BGE-M3+FAISS", e["retrieval"]["p95"], "#ffbf00"),
             ("LLM Mistral 7B (GPU)", e["llm"]["p95"], "#9467bd")]
    total_p95, sla = e["total"]["p95"], 8500
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    baixo = 0
    for nome, v, cor in comps:
        ax.bar([0], [v], bottom=baixo, color=cor, width=0.4,
               label=f"{nome} — p95 {v:,.0f} ms".replace(",", " "))
        baixo += v
    ax.bar([1], [total_p95], color=VERDE, width=0.4,
           label=f"p95 total medido — {total_p95:,.0f} ms".replace(",", " "))
    ax.axhline(sla, ls="--", color=VERM, lw=1.4)
    ax.text(1.28, sla + 120, f"SLA §4.1 = {sla:,.0f} ms".replace(",", " "),
            color=VERM, fontsize=9, ha="right")
    ax.text(0, baixo + 150, "soma dos p95\n(inclui retry §4.4)", ha="center",
            fontsize=8, color="#555")
    ax.set(xticks=[0, 1], xticklabels=["p95 por estágio\n(empilhado)", "p95 total\n(medido)"],
           ylim=(0, baixo * 1.28), ylabel="Latência (ms)",
           title="Fase 3 — Latência ponta a ponta, N=200 (Ollama nativo, GPU)")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "fig3_latencia.png", bbox_inches="tight")
    plt.close(fig)


def fig4():
    cav = json.loads((RAIZ / "dados" / "metricas_cav.json").read_text(encoding="utf-8"))
    g = json.loads((RAIZ / "dados" / "metricas_guardiao.json").read_text(encoding="utf-8"))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))

    conceitos = cav["conceitos"]
    nomes = sorted(conceitos, key=lambda c: conceitos[c]["auc_media"])
    vals = [conceitos[c]["auc_media"] for c in nomes]
    ax1.barh(nomes, vals, color=AZUL)
    ax1.axvline(0.5, ls="--", color=CINZA)
    for i, v in enumerate(vals):
        ax1.text(v - 0.02, i, f"{v:.3f}", ha="right", va="center",
                 color="white", fontsize=8, fontweight="bold")
    ax1.set(xlim=(0, 1.05), xlabel="AUC (holdout, 5× StratifiedShuffleSplit)",
            title="Probe CAV linear sobre BGE-M3 — AUC por conceito")

    det = g["detector"]
    cats = ["Recall\n(3 ataques)", "Precisão\n(3 legítimos)"]
    ax2.bar(cats, [det["recall"], det["precisao"]], color=[VERDE, AZUL], width=0.45)
    ax2.text(0, det["recall"] + 0.03, f"{det['recall']:.0%}", ha="center", fontweight="bold")
    ax2.text(1, det["precisao"] + 0.03, f"{det['precisao']:.0%}", ha="center", fontweight="bold")
    e2e = g.get("e2e", {})
    if e2e:
        ax2.text(0.5, 0.55,
                 f"ponta a ponta: {e2e['schema_ok']}/{e2e['n']} schema válido\n"
                 f"canário ecoado: {e2e['canario_vazado']} caso",
                 transform=ax2.transAxes, ha="center", fontsize=9,
                 bbox=dict(boxstyle="round", fc="#eef5ff", ec=AZUL, alpha=0.9))
    ax2.set(ylim=(0, 1.2), ylabel="Taxa",
            title="Guardião de injeção — conjunto §6.2 (seeds)")
    fig.suptitle("Fase 4 — Guardiões: probe de conceitos + injeção de prompt", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGS / "fig4_guardiao_cav.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    auc = fig1()
    fig2(); fig3(); fig4()
    print(f"ROC recomputada: AUC={auc:.4f} | figuras em {FIGS}")
    for f in sorted(FIGS.glob("*.png")):
        print(" -", f.name, f"{f.stat().st_size/1024:.0f} KB")
