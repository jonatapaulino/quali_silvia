"""Pipeline tabular LightGBM — Fase 1 (DDA v5.3 §4.5, §7).

Treina sobre base_sintetica_risco.xlsx (target nova_agressao) com:
- exclusão dos artefatos de geração (FEATURES_PROIBIDAS — vazamento auditado:
  prob_geracao r=+0,48; score_geracao r=+0,41; perfil_risco_agressor taxa_pos
  0,70 no nível "alto");
- split por grupo id_agressor_sintetico (3.579 agressores multi-episódio —
  split aleatório vazaria pessoa entre treino/teste);
- colunas mortas removidas (local constante; escolaridade_* ~95% ausente);
- métricas §4.5: AUC, Brier, ECE (uniform bins) e importância por permutação;
- erro estruturado para entradas anômalas (EntradaAnomala → 422 na API).
"""

import json
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("arquitetura_tese.tabular")

RAIZ = Path(__file__).resolve().parents[1]
BASE_XLSX = RAIZ / "dados" / "base_sintetica_risco.xlsx"
MODELO_PATH = Path(os.environ.get("ARQUITETURA_TESE_MODELO", RAIZ / "dados" / "modelo_tabular.txt"))
META_PATH = MODELO_PATH.with_suffix(".meta.json")

TARGET = "nova_agressao"
GRUPO = "id_agressor_sintetico"

FEATURES_PROIBIDAS = frozenset({"prob_geracao", "score_geracao", "perfil_risco_agressor"})

FEATURES_NUM = [
    "n_episodios_anteriores", "idade_requerido", "idade_vitima",
    "ameaca_morte", "acesso_arma", "uso_alcool_drogas", "separacao_recente",
    "descumpriu_medida", "filhos_comum", "desemprego_agressor", "controle_coercitivo",
]
FEATURES_CAT = ["classe", "situacao_processo", "sexo_requerido", "sexo_vitima"]
FEATURES = FEATURES_NUM + FEATURES_CAT  # contrato de entrada do modelo


class EntradaAnomala(ValueError):
    """Erro estruturado para entradas fora do contrato (§4.5: log para anômalos)."""

    def __init__(self, detalhe: dict):
        super().__init__(json.dumps(detalhe, ensure_ascii=False))
        self.detalhe = detalhe


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return np.nan


def carregar_episodios(xlsx_path=BASE_XLSX) -> list[dict]:
    from .dados.narrativas import iterar_episodios

    eps = [e for e in iterar_episodios(xlsx_path) if e.get("id_episodio")]
    eps = [e for e in eps if _f(e.get(TARGET)) == _f(e.get(TARGET))]  # descarta NaN no alvo
    return eps


def featurizar(episodios: list[dict]) -> pd.DataFrame:
    """Contrato de features: numéricas coagidas + categóricas one-hot."""
    df = pd.DataFrame([{f: e.get(f) for f in FEATURES} for e in episodios])
    for f in FEATURES_NUM:
        df[f] = df[f].map(_f)
    for f in FEATURES_CAT:
        df[f] = df[f].fillna("desconhecido").astype(str)
    return pd.get_dummies(df, columns=FEATURES_CAT, dtype=float)


def grupos(episodios: list[dict]) -> np.ndarray:
    return np.array([str(e[GRUPO]) for e in episodios])


def alvo(episodios: list[dict]) -> np.ndarray:
    return np.array([float(e[TARGET]) for e in episodios])


def grupo_split(n: int, grupos_arr: np.ndarray, test_size=0.2, seed=42):
    """Holdout por agressor: nenhum id aparece nos dois lados."""
    from sklearn.model_selection import GroupShuffleSplit

    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    tr, te = next(gss.split(np.zeros(n), groups=grupos_arr))
    assert not set(grupos_arr[tr]) & set(grupos_arr[te]), "vazamento de grupo no split"
    return tr, te


def treinar(X_tr: pd.DataFrame, y_tr: np.ndarray, validacao=None, **params):
    """validacao=(X_val, y_val) ativa early stopping: n_estimators vira teto
    (2000) e o corte ocorre no melhor ponto do conjunto de validação INTERNO —
    o holdout de teste nunca participa da decisão de parada."""
    import lightgbm as lgb

    kw = {}
    if validacao is not None:
        params.setdefault("n_estimators", 2000)
        kw["eval_set"] = [validacao]
        kw["callbacks"] = [lgb.early_stopping(50, verbose=False)]
    modelo = lgb.LGBMClassifier(
        n_estimators=params.pop("n_estimators", 300),
        learning_rate=params.pop("learning_rate", 0.05),
        num_leaves=params.pop("num_leaves", 31),
        subsample=0.9, colsample_bytree=0.9,
        random_state=42, n_jobs=-1, verbose=-1, **params,
    )
    modelo.fit(X_tr, y_tr, **kw)
    return modelo


def ece(y_true: np.ndarray, p: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error com bins uniformes em [0,1]."""
    y_true, p = np.asarray(y_true, float), np.asarray(p, float)
    bordas = np.linspace(0, 1, n_bins + 1)
    idx = np.clip(np.digitize(p, bordas) - 1, 0, n_bins - 1)
    total = 0.0
    for b in range(n_bins):
        m = idx == b
        if m.any():
            total += m.mean() * abs(p[m].mean() - y_true[m].mean())
    return float(total)


def avaliar(modelo, X_te: pd.DataFrame, y_te: np.ndarray) -> dict:
    from sklearn.metrics import brier_score_loss, roc_auc_score

    p = modelo.predict_proba(X_te)[:, 1]
    return {
        "auc": float(roc_auc_score(y_te, p)),
        "brier": float(brier_score_loss(y_te, p)),
        "ece": ece(y_te, p),
    }


def importancia_permutacao(modelo, X_te, y_te, n_repeats=10, seed=42) -> list[dict]:
    """§4.5 — importância por permutação (queda de AUC). Ordenada decrescente."""
    from sklearn.inspection import permutation_importance

    imp = permutation_importance(
        modelo, X_te, y_te, scoring="roc_auc", n_repeats=n_repeats,
        random_state=seed, n_jobs=-1,
    )
    return sorted(
        ({"feature": f, "media": float(m), "desvio": float(s)}
         for f, m, s in zip(X_te.columns, imp.importances_mean, imp.importances_std)),
        key=lambda d: d["media"], reverse=True,
    )


def salvar(modelo, colunas: list[str], caminho=MODELO_PATH, meta_extra=None) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    modelo.booster_.save_model(str(caminho))
    meta = {
        "features_contrato": FEATURES,
        "colunas_modelo": colunas,
        "features_proibidas": sorted(FEATURES_PROIBIDAS),
        "grupo_split": GRUPO,
        **(meta_extra or {}),
    }
    caminho.with_suffix(".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


_cache: dict = {}


def _carregar_modelo(caminho=MODELO_PATH):
    import lightgbm as lgb

    chave = str(caminho)
    if chave not in _cache:
        booster = lgb.Booster(model_file=str(caminho))
        meta = json.loads(Path(caminho).with_suffix(".meta.json").read_text(encoding="utf-8"))
        _cache[chave] = (booster, meta)
    return _cache[chave]


def extrair_features(caso: dict) -> dict:
    src = caso.get("features") or caso.get("metadados") or {}
    faltantes = [f for f in FEATURES if f not in src]
    if faltantes:
        raise EntradaAnomala({"erro": "features_ausentes", "campos": faltantes})
    proibidas = [f for f in FEATURES_PROIBIDAS if f in src]
    if proibidas:
        raise EntradaAnomala({"erro": "artefato_de_geracao_nao_permitido", "campos": proibidas})
    out = {}
    for f in FEATURES_NUM:
        v = _f(src[f])
        if v != v:  # NaN
            raise EntradaAnomala({"erro": "feature_numerica_invalida", "campo": f, "valor": src[f]})
        out[f] = v
    for f in FEATURES_CAT:
        out[f] = str(src[f])
    return out


def predizer_tabular(caso: dict, caminho=None) -> float:
    """Probabilidade em 0-1. Entradas anômalas → EntradaAnomala (log estruturado)."""
    caminho = caminho or MODELO_PATH
    try:
        feats = extrair_features(caso)
    except EntradaAnomala as e:
        log.warning(json.dumps({"evento": "entrada_anomala", **e.detalhe}, ensure_ascii=False))
        raise
    booster, meta = _carregar_modelo(caminho)
    df = featurizar([feats])
    df = df.reindex(columns=meta["colunas_modelo"], fill_value=0.0)
    p = float(booster.predict(df)[0])
    return min(max(p, 0.0), 1.0)
