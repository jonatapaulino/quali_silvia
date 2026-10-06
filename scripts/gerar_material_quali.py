"""Material de qualificação — complementa as 4 figuras principais.

Gera:
  dados/dicionario_base.md   — dicionário de dados + amostra (5 linhas) +
                               narrativa renderizada + correlações
  dados/figuras/fig5_calibracao.png — diagrama de confiabilidade (ECE 0,021)
  dados/figuras/fig6_bandas.png    — scores no holdout por faixa D8
  dados/figuras/fig7_arquitetura.png — pipeline com latências medidas
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
FIGS = RAIZ / "dados" / "figuras"

AZUL, CINZA, VERDE, VERM = "#1f77b4", "#9e9e9e", "#2ca02c", "#d62728"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 140})

DESCRICAO = {
    "id_episodio": ("identificador único do episódio (sintético)", "id"),
    "id_agressor_sintetico": ("hash estável do requerido — liga episódios da mesma pessoa", "id"),
    "id_vitima_sintetica": ("hash estável da vítima", "id"),
    "n_episodios_anteriores": ("nº de episódios anteriores do mesmo agressor", "feature"),
    "idade_requerido": ("idade do requerido", "feature"),
    "idade_vitima": ("idade da vítima", "feature"),
    "escolaridade_requerido": ("escolaridade do requerido (~95% 'Não Informado')", "descartada"),
    "escolaridade_vitima": ("escolaridade da vítima (~95% 'Não Informado')", "descartada"),
    "sexo_requerido": ("sexo do requerido (95% M)", "feature"),
    "sexo_vitima": ("sexo da vítima (92% F)", "feature"),
    "local": ("município — constante 'Manaus' nesta base", "descartada"),
    "classe": ("classe processual (IP, MPU, Ação Penal…)", "feature"),
    "situacao_processo": ("situação atual do processo", "feature"),
    "ameaca_morte": ("agressor ameaçou de morte (0/1)", "feature"),
    "acesso_arma": ("acesso a arma de fogo (0/1)", "feature"),
    "uso_alcool_drogas": ("uso de álcool/drogas no episódio (0/1)", "feature"),
    "separacao_recente": ("separação do casal nas últimas semanas (0/1)", "feature"),
    "descumpriu_medida": ("descumpriu medida protetiva vigente (0/1)", "feature"),
    "filhos_comum": ("filhos em comum com a vítima (0/1)", "feature"),
    "desemprego_agressor": ("requerido desempregado (0/1)", "feature"),
    "controle_coercitivo": ("controle coercitivo/vigilância (0/1)", "feature"),
    "nova_agressao": ("ALVO: houve nova agressão posterior (0/1)", "alvo"),
    "prob_geracao": ("ARTEFATO da geração sintética — vazamento (banido)", "artefato"),
    "score_geracao": ("ARTEFATO da geração sintética — vazamento (banido)", "artefato"),
    "perfil_risco_agressor": ("ARTEFATO da geração sintética — rótulo gerador (banido)", "artefato"),
}


def carregar_holdout():
    import lightgbm as lgb
    from arquitetura_tese.tabular import (alvo, carregar_episodios, featurizar, grupos,
                                  grupo_split, MODELO_PATH, META_PATH)
    eps = carregar_episodios()
    _, te = grupo_split(len(eps), grupos(eps))
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    booster = lgb.Booster(model_file=str(MODELO_PATH))
    X_te = featurizar([eps[i] for i in te]).reindex(
        columns=meta["colunas_modelo"], fill_value=0.0)
    return eps, te, alvo([eps[i] for i in te]), booster.predict(X_te)


def fig5(y_te, p_te, ece):
    bins = np.linspace(0, 1, 11)
    ixb = np.digitize(p_te, bins) - 1
    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    xs, ys, ns = [], [], []
    for b in range(10):
        m = ixb == b
        if m.sum() >= 20:
            xs.append(p_te[m].mean()); ys.append(y_te[m].mean()); ns.append(m.sum())
    ax.plot([0, 1], [0, 1], "--", color=CINZA, lw=1, label="Calibração perfeita")
    ax.plot(xs, ys, "o-", color=AZUL, lw=2, label="Modelo (10 bins)")
    for x, y, n in zip(xs, ys, ns):
        ax.annotate(str(n), (x, y), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=7, color="#555")
    ax.set(xlabel="Probabilidade prevista", ylabel="Frequência observada",
           title=f"Calibração no holdout — ECE = {ece:.3f}",
           xlim=(0, 1), ylim=(0, 1))
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(FIGS / "fig5_calibracao.png", bbox_inches="tight")
    plt.close(fig)


def fig6(y_te, p_te):
    faixas = [(0, .25, "baixo", VERDE), (.25, .50, "moderado", "#ffbf00"),
              (.50, .75, "alto", "#ff7f0e"), (.75, 1.01, "crítico", VERM)]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for lo, hi, nome, cor in faixas:
        m = (p_te >= lo) & (p_te < hi)
        ax.hist(p_te[m], bins=np.linspace(lo, hi, 9), color=cor, alpha=0.85,
                label=f"{nome}: {m.sum()} casos ({m.sum()/len(p_te):.0%})")
    for c in (.25, .50, .75):
        ax.axvline(c, color="#333", ls=":", lw=1)
    ax.set(xlabel="Probabilidade prevista de nova_agressao",
           ylabel="Episódios no holdout",
           title="Distribuição dos scores por faixa de risco (D8: 0,25/0,50/0,75)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "fig6_bandas.png", bbox_inches="tight")
    plt.close(fig)


def fig7():
    lat = json.loads((RAIZ / "dados" / "metricas_latencia.json").read_text(encoding="utf-8"))["estagios_ms"]
    caixas = [
        (0.02, "Entrada\n(episódio)", "#eceff1"),
        (0.16, "Guardião\ningestão §4.6", "#ffcdd2"),
        (0.30, f"LightGBM\n~{lat['tabular']['p50']:.0f} ms", "#bbdefb"),
        (0.46, f"BGE-M3 + FAISS\n~{lat['retrieval']['p50']:.0f} ms", "#fff9c4"),
        (0.64, f"Mistral 7B Q4\nGPU — p50 {lat['llm']['p50']/1000:.1f} s", "#e1bee7"),
        (0.82, "Montagem\ndeterminística\n+ fundamentação", "#c8e6c9"),
    ]
    fig, ax = plt.subplots(figsize=(11.5, 3.4))
    for x, txt, cor in caixas:
        ax.add_patch(plt.Rectangle((x, 0.32), 0.125, 0.4, fc=cor, ec="#555"))
        ax.text(x + 0.0625, 0.52, txt, ha="center", va="center", fontsize=9)
    for x1, x2 in zip([c[0] + 0.125 for c in caixas], [c[0] for c in caixas[1:]]):
        ax.annotate("", xy=(x2, 0.52), xytext=(x1, 0.52),
                    arrowprops=dict(arrowstyle="->", color="#333"))
    ax.text(0.93, 0.86, "LaudoFinal\nou LaudoDegradado\n(circuit breaker §4.7)",
            ha="center", fontsize=8.5, color=VERDE)
    ax.text(0.02, 0.08,
            "D9-b: LLM gera só texto — score, nível, incerteza e fundamentação são determinísticos",
            fontsize=8.5, color="#555")
    ax.set(xlim=(0, 1), ylim=(0, 1), title="Pipeline ARQUITETURA TESE — caminho síncrono (SLA 8,5 s)")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(FIGS / "fig7_arquitetura.png", bbox_inches="tight")
    plt.close(fig)


def dicionario(eps):
    df = pd.DataFrame(eps)
    y = df["nova_agressao"].astype(float)
    linhas = ["# Dicionário — base_sintetica_risco.xlsx (20.200 episódios)", "",
              "| coluna | papel | descrição | r(y) |", "|---|---|---|---|"]
    for c in df.columns:
        desc, papel = DESCRICAO.get(c, ("", "?"))
        try:
            r = f"{np.corrcoef(pd.to_numeric(df[c], errors='coerce'), y)[0,1]:+.3f}"
            if "nan" in r:
                r = "—"
        except Exception:
            r = "—"
        linhas.append(f"| `{c}` | {papel} | {desc} | {r} |")
    linhas += ["", "## Amostra (5 episódios, colunas principais)", "",
               "```", df[["id_episodio", "n_episodios_anteriores", "classe",
                          "ameaca_morte", "acesso_arma", "descumpriu_medida",
                          "controle_coercitivo", "nova_agressao"]].head(5).to_string(index=False),
               "```", "",
               "## Narrativa sintética renderizada (exemplo)", "", "```",
               json.loads(open(RAIZ / "dados" / "narrativas_sinteticas.jsonl",
                               encoding="utf-8").readline())["narrativa"], "```"]
    (RAIZ / "dados" / "dicionario_base.md").write_text(
        "\n".join(linhas), encoding="utf-8")


def fig8(eps, te):
    """Curvas de treinamento — mesma partição do treino de produção:
    split externo por grupo (holdout intocado) + validação interna 15%
    usada pelo early stopping. Não altera o artefato salvo."""
    import json

    import lightgbm as lgb

    from arquitetura_tese.tabular import alvo, featurizar, grupos, grupo_split

    mets = json.loads((RAIZ / "dados" / "metricas_tabular.json")
                      .read_text(encoding="utf-8"))
    best = mets["early_stopping"]["best_iteration"]
    auc_teste = mets["auc"]

    import numpy as np

    g_all = np.asarray(grupos(eps))
    tr_idx, _te = grupo_split(len(eps), g_all)
    fit_i, val_i = grupo_split(len(tr_idx), g_all[tr_idx], test_size=0.15)
    fit_idx = [tr_idx[i] for i in fit_i]
    val_idx = [tr_idx[i] for i in val_i]
    X_fit = featurizar([eps[i] for i in fit_idx])
    X_val = featurizar([eps[i] for i in val_idx])
    X_val = X_val.reindex(columns=X_fit.columns, fill_value=0.0)
    y_fit, y_val = alvo([eps[i] for i in fit_idx]), alvo([eps[i] for i in val_idx])

    modelo = lgb.LGBMClassifier(n_estimators=2000, learning_rate=0.05,
                                num_leaves=31, subsample=0.9, colsample_bytree=0.9,
                                random_state=42, n_jobs=-1, verbose=-1)
    modelo.fit(X_fit, y_fit, eval_set=[(X_fit, y_fit), (X_val, y_val)],
               eval_metric=["binary_logloss", "auc"],
               callbacks=[lgb.early_stopping(50, verbose=False)])
    ev = modelo.evals_result_
    ll_tr = ev["training"]["binary_logloss"]
    ll_te = ev["valid_1"]["binary_logloss"]
    au_tr = ev["training"]["auc"]
    au_te = ev["valid_1"]["auc"]
    it = best or modelo.best_iteration_

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax1.plot(ll_tr, label="treino", color=AZUL)
    ax1.plot(ll_te, label="validação interna", color=VERM)
    ax1.axvline(it, ls="--", color="gray",
                label=f"early stopping (it. {it})")
    ax1.set(xlabel="iteração (árvores)", ylabel="log-loss",
            title="Convergência — log-loss")
    ax1.legend()
    ax2.plot(au_tr, label="treino", color=AZUL)
    ax2.plot(au_te, label="validação interna", color=VERM)
    ax2.axvline(it, ls="--", color="gray",
                label=f"early stopping (it. {it})")
    ax2.set(xlabel="iteração (árvores)", ylabel="AUC",
            title=f"Convergência — AUC (val. interna {au_te[it-1]:.3f} no ponto de parada)")
    ax2.legend(loc="lower right")
    gap = au_tr[it - 1] - au_te[it - 1]
    fig.suptitle(f"Treino LightGBM — early stopping it. {it}, gap "
                 f"treino/validação {gap:+.3f} AUC | holdout externo (teste): "
                 f"{auc_teste:.3f}", y=1.02, fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGS / "fig8_treinamento.png", bbox_inches="tight")
    plt.close(fig)


def fig9(eps):
    """Curva de aprendizado: AUC do holdout vs tamanho do treino
    (frações do mesmo split por grupo) + AUC do probe CAV por fold."""
    import lightgbm as lgb
    from sklearn.metrics import roc_auc_score

    from arquitetura_tese.tabular import alvo, featurizar, grupos, grupo_split

    tr_idx, te_idx = grupo_split(len(eps), grupos(eps))
    X_all = featurizar(eps)
    cols = X_all.columns
    X_te = X_all.iloc[te_idx]
    y_te = alvo([eps[i] for i in te_idx])

    fracs, aucs_tr, aucs_te = [0.1, 0.25, 0.5, 0.75, 1.0], [], []
    rng = np.random.RandomState(42)
    for f in fracs:
        sub = rng.choice(tr_idx, size=int(len(tr_idx) * f), replace=False)
        X_tr = X_all.iloc[sub].reindex(columns=cols, fill_value=0.0)
        y_tr = alvo([eps[i] for i in sub])
        m = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31,
                               subsample=0.9, colsample_bytree=0.9,
                               random_state=42, n_jobs=-1, verbose=-1)
        m.fit(X_tr, y_tr)
        aucs_tr.append(roc_auc_score(y_tr, m.predict_proba(X_tr)[:, 1]))
        aucs_te.append(roc_auc_score(y_te, m.predict_proba(X_te)[:, 1]))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ns = [int(len(tr_idx) * f) for f in fracs]
    ax1.plot(ns, aucs_te, "o-", color=AZUL, label="holdout")
    ax1.plot(ns, aucs_tr, "s--", color=CINZA, label="treino")
    for n, a in zip(ns, aucs_te):
        ax1.annotate(f"{a:.3f}", (n, a), textcoords="offset points",
                     xytext=(0, 8), ha="center", fontsize=8)
    ax1.set(xlabel="episódios de treino", ylabel="AUC",
            title="Curva de aprendizado — saturação de dados")
    ax1.legend()

    # fold-level AUC do probe CAV (reusa o pipeline do script de métricas)
    from arquitetura_tese import recuperacao
    narrs = [json.loads(l) for l in
             (RAIZ / "dados" / "narrativas_sinteticas.jsonl").open(encoding="utf-8")]
    enc = recuperacao.ENCODERS["bge_m3"]()
    X = np.asarray(enc.encode([d["narrativa"] for d in narrs],
                              normalize_embeddings=True), dtype="float32")
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedShuffleSplit
    from collections import Counter
    conceitos = [c for c, n in Counter(
        c for d in narrs for c in d["conceitos"]).items() if 15 <= n <= len(narrs) - 15]
    dados = {c: [] for c in conceitos}
    for conceito in conceitos:
        y = np.array([conceito in d["conceitos"] for d in narrs], dtype=int)
        for tr, ts in StratifiedShuffleSplit(5, test_size=0.25,
                                             random_state=np.random.RandomState(42)).split(X, y):
            p = LogisticRegression(max_iter=2000).fit(X[tr], y[tr])
            dados[conceito].append(roc_auc_score(y[ts], p.predict_proba(X[ts])[:, 1]))
    ax2.boxplot([dados[c] for c in conceitos], tick_labels=conceitos)
    ax2.axhline(0.5, ls="--", color=CINZA)
    ax2.set(ylabel="AUC (5 folds)", title="Probe CAV — estabilidade por conceito")
    ax2.tick_params(axis="x", rotation=35)

    fig.tight_layout()
    fig.savefig(FIGS / "fig9_aprendizado_cav.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    eps, te, y_te, p_te = carregar_holdout()
    m = json.loads((RAIZ / "dados" / "metricas_tabular.json").read_text(encoding="utf-8"))
    fig5(y_te, p_te, m["ece"]); fig6(y_te, p_te); fig7(); dicionario(eps)
    fig8(eps, te); fig9(eps)
    print("gerados: fig5-fig9 + dicionario_base.md")
