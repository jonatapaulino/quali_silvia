"""§5.2 nível/incerteza e §6.4 matriz do override (mocks — determinístico)."""

import pytest

from arquitetura_tese.regras import (
    FLAG_DIVERGENCIA,
    aplicar_override,
    incerteza,
    nivel_risco,
)
from arquitetura_tese.schemas import Incerteza, NivelRisco


@pytest.mark.parametrize("p,esperado", [
    (0.00, NivelRisco.BAIXO), (0.24, NivelRisco.BAIXO),
    (0.25, NivelRisco.MODERADO), (0.49, NivelRisco.MODERADO),
    (0.50, NivelRisco.ALTO), (0.74, NivelRisco.ALTO),
    (0.75, NivelRisco.CRITICO), (1.00, NivelRisco.CRITICO),
])
def test_nivel_risco_limiares(p, esperado):
    assert nivel_risco(p) is esperado


@pytest.mark.parametrize("p,concordancia,flags,esperado", [
    (0.10, 0.9, [], Incerteza.BAIXA),                    # margem alta + concordância alta
    (0.45, 0.9, [], Incerteza.ALTA),                     # margem < 0.15
    (0.90, 0.1, [], Incerteza.ALTA),                     # concordância < 0.2
    (0.90, 0.9, ["falta_campo"], Incerteza.ALTA),        # qualquer flag de qualidade
    (0.30, 0.4, [], Incerteza.MODERADA),                 # caso intermediário
])
def test_incerteza(p, concordancia, flags, esperado):
    assert incerteza(p, concordancia, flags) is esperado


MATRIZ_6_4 = [
    (NivelRisco.BAIXO,    True,  True),
    (NivelRisco.MODERADO, True,  True),   # regra estendida (§5.3)
    (NivelRisco.ALTO,     True,  False),
    (NivelRisco.CRITICO,  True,  False),
    (NivelRisco.BAIXO,    False, False),
    (NivelRisco.MODERADO, False, False),
    (NivelRisco.ALTO,     False, False),
    (NivelRisco.CRITICO,  False, False),
]


@pytest.mark.parametrize("nivel,cav_critico,flag_esperada", MATRIZ_6_4)
def test_matriz_override(nivel, cav_critico, flag_esperada):
    laudo = {"refutacao_flags": [], "revisao_humana_obrigatoria": False}
    aplicar_override(nivel, cav_critico, laudo)
    assert (FLAG_DIVERGENCIA in laudo["refutacao_flags"]) is flag_esperada
    if flag_esperada:
        assert laudo["revisao_humana_obrigatoria"] is True
    else:
        assert laudo["revisao_humana_obrigatoria"] is False
