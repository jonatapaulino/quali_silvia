"""§6.5 — intervalo de confiança de Wilson (âncora do §4.3)."""

from arquitetura_tese.harness import wilson


def test_wilson_zero_falhas_em_200():
    lo, hi = wilson(0, 200)
    assert lo == 0.0
    assert hi < 0.025  # regra dos três: limite superior ~1,5% a 95%


def test_wilson_85_por_cento():
    lo, hi = wilson(170, 200)
    assert lo < 0.85 < hi
