"""Fase 1 — pipeline tabular (§4.5): split por grupo, contrato de features,
ECE, erro estruturado e ausência de artefatos de geração no modelo."""

import numpy as np
import pytest

from arquitetura_tese import tabular


def _eps(n=400, seed=0):
    rng = np.random.RandomState(seed)
    eps = []
    for i in range(n):
        agr = f"agr{i % 60}"  # ~60 agressores -> força multi-episódio
        risco = rng.rand()
        ep = {f: 0.0 for f in tabular.FEATURES_NUM}
        ep.update({
            "id_episodio": f"EP{i:05d}", "id_agressor_sintetico": agr,
            "id_vitima_sintetica": f"vit{i % 61}",
            "n_episodios_anteriores": float(i % 5),
            "idade_requerido": 30 + rng.rand() * 20, "idade_vitima": 25 + rng.rand() * 20,
            "ameaca_morte": float(risco > 0.6), "descumpriu_medida": float(risco > 0.7),
            "controle_coercitivo": float(risco > 0.5),
            "classe": "Inquérito Policial" if i % 2 else "Ação Penal - Procedimento Sumário",
            "situacao_processo": "Ativo", "sexo_requerido": "M", "sexo_vitima": "F",
            "nova_agressao": float(risco > 0.55),
        })
        eps.append(ep)
    return eps


def test_split_por_grupo_nao_vaza_agressor():
    eps = _eps()
    g = tabular.grupos(eps)
    tr, te = tabular.grupo_split(len(eps), g, seed=7)
    assert not set(g[tr]) & set(g[te])


def test_ece_limites():
    y = np.array([0] * 50 + [1] * 50)
    assert tabular.ece(y, y.astype(float)) < 1e-9          # calibração perfeita
    invertido = np.array([0.9] * 50 + [0.1] * 50)          # confiante e errado
    assert tabular.ece(y, invertido) > 0.5                  # mal calibrado
    assert tabular.ece(y, np.full(100, 0.5)) < 1e-9         # constante na prevalência = calibrado


def test_contrato_rejeita_anomalias():
    caso = {"features": {f: 0 for f in tabular.FEATURES}}
    feats = tabular.extrair_features(caso)
    assert set(feats) == set(tabular.FEATURES)

    with pytest.raises(tabular.EntradaAnomala):
        tabular.extrair_features({"features": {"ameaca_morte": 1}})      # faltantes

    proibido = {f: 0 for f in tabular.FEATURES}
    proibido["prob_geracao"] = 0.9
    with pytest.raises(tabular.EntradaAnomala):
        tabular.extrair_features({"features": proibido})                 # artefato

    ruim = {f: 0 for f in tabular.FEATURES}
    ruim["ameaca_morte"] = "texto"
    with pytest.raises(tabular.EntradaAnomala):
        tabular.extrair_features({"features": ruim})                     # tipo inválido


def test_modelo_nao_contem_artefatos(tmp_path):
    eps = _eps(600)
    X = tabular.featurizar(eps)
    y = tabular.alvo(eps)
    g = tabular.grupos(eps)
    tr, te = tabular.grupo_split(len(eps), g, seed=3)
    modelo = tabular.treinar(X.iloc[tr], y[tr], n_estimators=60)
    assert not any(b in f for f in X.columns for b in tabular.FEATURES_PROIBIDAS)

    caminho = tmp_path / "m.txt"
    tabular.salvar(modelo, list(X.columns), caminho=caminho)
    p = tabular.predizer_tabular(
        {"features": {f: eps[0][f] for f in tabular.FEATURES}}, caminho=caminho)
    assert 0.0 <= p <= 1.0

    metricas = tabular.avaliar(modelo, X.iloc[te], y[te])
    assert 0.5 <= metricas["auc"] <= 1.0
    assert metricas["brier"] >= 0.0 and metricas["ece"] >= 0.0
