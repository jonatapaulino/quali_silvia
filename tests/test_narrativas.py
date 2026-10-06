"""D7(b) — narrativas sintéticas: determinismo, ligação e conceitos CAV."""

import random

from arquitetura_tese.dados.narrativas import (
    conceitos,
    dispositivos_sugeridos,
    gerar_documento,
    gerar_narrativa,
)

EP = {
    "id_episodio": "EP000001",
    "id_agressor_sintetico": "8d26c895aaaa",
    "id_vitima_sintetica": "3e22e360bbbb",
    "n_episodios_anteriores": "3.0",
    "idade_requerido": "35", "idade_vitima": "30",
    "local": "Manaus", "classe": "Inquérito Policial",
    "ameaca_morte": "1.0", "acesso_arma": "0.0", "uso_alcool_drogas": "1.0",
    "separacao_recente": "0.0", "descumpriu_medida": "1.0", "filhos_comum": "1.0",
    "desemprego_agressor": "0.0", "controle_coercitivo": "1.0", "nova_agressao": "1.0",
}


def test_determinismo_mesma_semente():
    a = gerar_narrativa(EP, random.Random(42))
    b = gerar_narrativa(EP, random.Random(42))
    assert a == b


def test_placeholders_vinculados_aos_ids():
    texto = gerar_narrativa(EP, random.Random(1))
    assert "VÍTIMA_3E22E3" in texto
    assert "AGRESSOR_8D26C8" in texto


def test_conceitos_seguem_features():
    rotulos = conceitos(EP)
    for esperado in ("coercao", "descumprimento_medida", "ameaca_morte",
                     "abuso_substancias", "escalada"):
        assert esperado in rotulos
    ep_sem = {**EP, "controle_coercitivo": "0.0", "n_episodios_anteriores": "0.0"}
    rotulos_sem = conceitos(ep_sem)
    assert "coercao" not in rotulos_sem
    assert "escalada" not in rotulos_sem


def test_dispositivos_sugeridos_mapeiam_features():
    ids = {d["doc_id"] for d in dispositivos_sugeridos(EP)}
    assert "lei11340_art24a" in ids   # descumpriu_medida
    assert "cp_art147" in ids         # ameaca_morte
    assert "cp_art147a" in ids        # controle_coercitivo
    assert "lei11340_art12" in ids    # classe = Inquérito Policial


def test_documento_completo():
    doc = gerar_documento(EP, random.Random(0))
    assert doc["id_episodio"] == "EP000001"
    assert len(doc["narrativa"]) >= 200
    assert doc["conceitos"] and doc["dispositivos_sugeridos"]
