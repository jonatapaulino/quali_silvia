"""Gera evidências demonstrativas de classificação para a banca.

- fig10_matriz_confusao.png — matriz de confusão real no holdout
- dados/exemplos/casos.json — TP/FP/TN/FN representativos com features + score
- dados/exemplos/laudo_<id>.json + .md — laudo completo ponta a ponta (2 casos)
- decisoes/exemplos_classificacao.md — documento renderizado para a banca

Uso: python scripts/gerar_exemplos_classificacao.py
"""

import asyncio
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import lightgbm as lgb

from arquitetura_tese import evidencias as ev_mod
from arquitetura_tese import recuperacao, regras
from arquitetura_tese.dados.narrativas import iterar_episodios
from arquitetura_tese.resiliencia import gerar_fundamentado, montar_laudo
from arquitetura_tese.schemas import checar_fundamentacao
from arquitetura_tese.tabular import (BASE_XLSX, META_PATH, MODELO_PATH,
                                    alvo, carregar_episodios, featurizar,
                                    grupos, grupo_split)

FIGS = RAIZ / "dados" / "figuras"
EX = RAIZ / "dados" / "exemplos"


def matriz_confusao(y_te, p_te, limiar=0.5):
    tp = int(((p_te >= limiar) & (y_te == 1)).sum())
    fp = int(((p_te >= limiar) & (y_te == 0)).sum())
    tn = int(((p_te < limiar) & (y_te == 0)).sum())
    fn = int(((p_te < limiar) & (y_te == 1)).sum())
    return tp, fp, tn, fn


def fig10(tp, fp, tn, fn):
    mat = np.array([[tn, fp], [fn, tp]])
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    ax.imshow(mat, cmap="Blues", vmin=0, vmax=mat.max() * 1.25)
    for (i, j), v in np.ndenumerate(mat):
        ax.text(j, i, f"{v}\n({v/mat.sum():.1%})", ha="center", va="center",
                fontsize=13, fontweight="bold",
                color="white" if v > mat.max() * 0.6 else "#123")
    ax.set(xticks=[0, 1], yticks=[0, 1],
           xticklabels=["predito: sem reincidência", "predito: reincidência"],
           yticklabels=["real: sem reincidência", "real: reincidência"],
           title=f"Matriz de confusão — holdout n={mat.sum():,}".replace(",", " "),
           xlabel="predição do modelo (limiar 0,50)", ylabel="classe real")
    fig.tight_layout()
    fig.savefig(FIGS / "fig10_matriz_confusao.png", bbox_inches="tight")
    plt.close(fig)


def escolher_exemplos(eps, te_idx, y_te, p_te):
    """1 TP, 1 FP, 1 TN, 1 FN — preferindo os que têm narrativa."""
    narr_ids = {json.loads(l)["id_episodio"] for l in
                (RAIZ / "dados" / "narrativas_sinteticas.jsonl").open(encoding="utf-8")}
    te_eps = [eps[i] for i in te_idx]
    alvo_local = {e["id_episodio"]: int(t) for e, t in zip(te_eps, y_te)}
    probs = {e["id_episodio"]: float(p) for e, p in zip(te_eps, p_te)}

    def pick(real, cond, ordem):
        cands = [e for e in te_eps
                 if alvo_local[e["id_episodio"]] == real
                 and cond(probs[e["id_episodio"]])
                 and e["id_episodio"] in narr_ids]
        cands.sort(key=lambda e: abs(probs[e["id_episodio"]] - ordem))
        return cands[0] if cands else None

    return {
        "TP": pick(1, lambda p: p >= 0.5, 0.9),
        "FP": pick(0, lambda p: p >= 0.5, 0.85),
        "FN": pick(1, lambda p: p < 0.5, 0.3),
        "TN": pick(0, lambda p: p < 0.5, 0.1),
    }


def tabela_caso(ep, prob, rotulo, real):
    feats = ["n_episodios_anteriores", "ameaca_morte", "acesso_arma",
             "uso_alcool_drogas", "separacao_recente", "descumpriu_medida",
             "filhos_comum", "desemprego_agressor", "controle_coercitivo",
             "classe", "situacao_processo"]
    linhas = [f"| {f} | {ep.get(f)} |" for f in feats if f in ep]
    return (
        f"### Caso {rotulo} — episódio {ep['id_episodio']}\n\n"
        f"- score previsto: **{prob:.3f}** → classe predita "
        f"{'reincidência' if prob >= 0.5 else 'sem reincidência'} "
        f"(limiar 0,50) — real: {'reincidência' if real else 'sem reincidência'}\n"
        f"- banda D8: **{regras.nivel_risco(prob).value}**\n\n"
        "| feature | valor |\n|---|---|\n" + "\n".join(linhas) + "\n")


async def laudo_completo(ep, narr_map, indices):
    caso = {
        "trace_id": f"ex_{ep['id_episodio']}",
        "id_episodio": ep["id_episodio"],
        "narrativa": narr_map[ep["id_episodio"]],
        "metadados": {k: ep[k] for k in
                      ("n_episodios_anteriores", "idade_requerido", "idade_vitima",
                       "ameaca_morte", "acesso_arma", "uso_alcool_drogas",
                       "separacao_recente", "descumpriu_medida", "filhos_comum",
                       "desemprego_agressor", "controle_coercitivo", "classe",
                       "situacao_processo", "sexo_requerido", "sexo_vitima")
                      if k in ep},
        "features": {},
        "evidencias": [],
        "concordancia": 0.0,
    }
    from arquitetura_tese.tabular import FEATURES, predizer_tabular
    caso["features"] = {k: caso["metadados"].get(k) for k in FEATURES}
    caso["_narr_doc"] = f"narr_{ep['id_episodio']}"
    import httpx
    score = predizer_tabular(caso)
    caso["evidencias"] = ev_mod.montar_evidencias(
        caso["narrativa"], indices, excluir_doc=caso["_narr_doc"])
    async with httpx.AsyncClient() as client:
        bruto, erros, tent = await gerar_fundamentado(client, caso, score)
    laudo = montar_laudo(caso, score, bruto,
                         concordancia=caso["concordancia"])
    return score, laudo, erros, tent, caso["evidencias"]


def _fmt(v):
    return int(v) if isinstance(v, float) and v == int(v) else v


def render_laudo(ep, narr, score, laudo, erros, tent, recuperadas, rotulo):
    lin = laudo.model_dump(mode="json")
    rec = "\n".join(f"  - {d['doc_id']} — “{d['titulo']}”"
                    for d in recuperadas) or "  (nenhum)"
    ev = "\n".join(f"  - {d['doc_id']} ({d['lei']}, {d['artigo']})"
                   for d in lin["garantia_dispositivos"]) or "  (nenhum)"
    apoio = "\n".join(f"  - {a['doc_id']}"
                      for a in lin.get("apoio", [])) or "  (nenhum)"
    return f"""## Exemplo ponta a ponta — {rotulo} ({ep['id_episodio']})

**Entrada (features do episódio):** {_fmt(ep.get('n_episodios_anteriores'))} episódios
anteriores; ameaça de morte={_fmt(ep.get('ameaca_morte'))}; arma={_fmt(ep.get('acesso_arma'))};
separação recente={_fmt(ep.get('separacao_recente'))}; descumprimento de
medida={_fmt(ep.get('descumpriu_medida'))}; controle coercitivo={_fmt(ep.get('controle_coercitivo'))};
classe={ep.get('classe')}; situação={ep.get('situacao_processo')}

**Narrativa associada (sintética, D7-b):**

> {narr[:600]}{'…' if len(narr) > 600 else ''}

**Estágio 1 — LightGBM:** score = **{score:.3f}** → banda **{lin['alegacao_nivel']}**
(decisão determinística, não do LLM) · revisão humana = {lin['revisao_humana_obrigatoria']}

**Estágio 2 — Evidências recuperadas (BGE-M3/FAISS, top-5 dispositivos + 2 casos):**
{rec}

**Estágio 3 — Laudo Toulmin gerado pelo Mistral 7B** (tentativas: {tent}):
- *Alegação:* {lin['alegacao_enunciado']}
- *Raciocínio da garantia:* {lin['garantia_raciocinio']}
- *Dispositivos citados:*
{ev}
- *Casos de apoio:*
{apoio}
- *Refutação:* {lin['refutacao']}

**Estágio 4 — Verificação determinística:** {"citações íntegras" if not erros else "VIOLAÇÕES: " + "; ".join(erros)}
· flags de refutação: {lin.get('refutacao_flags') or 'nenhuma'}
· incerteza: {lin['qualificador']['incerteza']} ({'; '.join(lin['qualificador']['motivos'])})
"""


def main():
    EX.mkdir(exist_ok=True)
    eps = carregar_episodios()
    _, te = grupo_split(len(eps), grupos(eps))
    m = lgb.Booster(model_file=str(MODELO_PATH))
    X = featurizar([eps[i] for i in te])
    X = X.reindex(columns=m.feature_name(), fill_value=0.0)
    p_te = m.predict(X)
    y_te = alvo([eps[i] for i in te])

    tp, fp, tn, fn = matriz_confusao(y_te, p_te)
    fig10(tp, fp, tn, fn)
    print(f"matriz: TP={tp} FP={fp} TN={tn} FN={fn}")

    ex = escolher_exemplos(eps, te, y_te, p_te)
    narr_map = {json.loads(l)["id_episodio"]: json.loads(l)["narrativa"] for l in
                (RAIZ / "dados" / "narrativas_sinteticas.jsonl").open(encoding="utf-8")}

    te_map = {eps[i]["id_episodio"]: j for j, i in enumerate(te)}
    _, indices = ev_mod.montar_indices()

    partes = ["# Exemplos de classificação e de laudo — Arquitetura Tese\n",
              f"Matriz de confusão no holdout (n={tp+fp+tn+fn}, limiar 0,50): "
              f"TP={tp}, FP={fp}, TN={tn}, FN={fn} → acurácia "
              f"{(tp+tn)/(tp+fp+tn+fn):.1%}, recall {tp/(tp+fn):.1%}, "
              f"precisão {tp/(tp+fp):.1%} (prevalência artificial ~50%).\n"]

    for rotulo in ("TP", "FP", "FN", "TN"):
        ep = ex.get(rotulo)
        if not ep:
            continue
        p = float(p_te[te_map[ep["id_episodio"]]])
        real = int(y_te[te_map[ep["id_episodio"]]])
        partes.append(tabela_caso(ep, p, rotulo, real)
                      .replace("| 1.0 |", "| 1 |").replace("| 0.0 |", "| 0 |"))
        (EX / f"caso_{rotulo.lower()}.json").write_text(
            json.dumps({"episodio": ep, "score": p, "real": real},
                       ensure_ascii=False, indent=1), encoding="utf-8")

    # dois laudos completos: um TP (tudo certo) e um FN (modelo errou —
    # mostra honestidade: o laudo ainda sai, mas a banda/refutação refletem)
    for rotulo in ("TP", "FN"):
        ep = ex.get(rotulo)
        if not ep:
            continue
        score, laudo, erros, tent, recuperadas = asyncio.run(
            laudo_completo(ep, narr_map, indices))
        (EX / f"laudo_{rotulo.lower()}.json").write_text(
            laudo.model_dump_json(indent=1), encoding="utf-8")
        md = render_laudo(ep, narr_map[ep["id_episodio"]], score, laudo,
                          erros, tent, recuperadas, rotulo)
        (EX / f"laudo_{rotulo.lower()}.md").write_text(md, encoding="utf-8")
        partes.append(md)
        print(f"laudo {rotulo}: score={score:.3f} erros={len(erros)} tent={tent}")

    (RAIZ / "decisoes" / "exemplos_classificacao.md").write_text(
        "\n".join(partes), encoding="utf-8")
    print(f"-> {EX}/ + decisoes/exemplos_classificacao.md + fig10")


if __name__ == "__main__":
    main()
