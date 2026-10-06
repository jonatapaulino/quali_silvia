"""§4.5 — API retorna probabilidade ou erro estruturado 422 para anômalos."""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from arquitetura_tese import tabular
from arquitetura_tese.api import app


@pytest.fixture
def modelo_tmp(tmp_path, monkeypatch):
    rng = np.random.RandomState(1)
    eps = []
    for i in range(300):
        eps.append({
            "id_episodio": f"EP{i:04d}", "id_agressor_sintetico": f"a{i % 40}",
            "id_vitima_sintetica": f"v{i % 41}",
            **{f: float(rng.rand() > 0.7) for f in tabular.FEATURES_NUM},
            "n_episodios_anteriores": float(i % 4), "idade_requerido": 40.0,
            "idade_vitima": 35.0,
            "classe": "Inquérito Policial", "situacao_processo": "Ativo",
            "sexo_requerido": "M", "sexo_vitima": "F",
            "nova_agressao": float(rng.rand() > 0.5),
        })
    X, y = tabular.featurizar(eps), tabular.alvo(eps)
    modelo = tabular.treinar(X, y, n_estimators=30)
    caminho = tmp_path / "m.txt"
    tabular.salvar(modelo, list(X.columns), caminho=caminho)
    monkeypatch.setattr(tabular, "MODELO_PATH", caminho)
    return {f: eps[0][f] for f in tabular.FEATURES}


def test_score_ok(modelo_tmp):
    client = TestClient(app)
    r = client.post("/score", json={"features": modelo_tmp})
    assert r.status_code == 200
    assert 0.0 <= r.json()["score_probabilidade"] <= 1.0


def test_score_anomalia_retorna_422_estruturado(modelo_tmp):
    client = TestClient(app)
    r = client.post("/score", json={"features": {"prob_geracao": 0.5}})
    assert r.status_code == 422
    assert "erro" in r.json()
