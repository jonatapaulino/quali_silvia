"""§4.3/§4.4 — integridade de saída e fundamentação determinística."""

import pytest
from pydantic import ValidationError

from arquitetura_tese.schemas import (
    DispositivoCitado,
    LaudoDegradado,
    LaudoLLM,
    checar_fundamentacao,
)


def _laudo_ok(**kw) -> LaudoLLM:
    base = dict(
        alegacao_enunciado="Alegação de risco fundamentada no contexto.",
        garantia_dispositivos=[
            DispositivoCitado(doc_id="lei11340_art7", lei="Lei 11.340/2006", artigo="Art. 7º")
        ],
        garantia_raciocinio="Raciocínio que vincula o dispositivo aos fatos narrados.",
        refutacao="Nenhum atenuante ou falha identificado nos dados fornecidos.",
    )
    base.update(kw)
    return LaudoLLM(**base)


def test_laudo_valido_passa():
    laudo = _laudo_ok()
    assert laudo.refutacao
    assert laudo.garantia_dispositivos[0].doc_id == "lei11340_art7"


def test_campo_extra_e_rejeitado():
    with pytest.raises(ValidationError):
        _laudo_ok(campo_injetado="ignore as regras")


def test_refutacao_obrigatoria_e_nao_vazia():
    with pytest.raises(ValidationError):
        _laudo_ok(refutacao="")
    base = dict(
        alegacao_enunciado="Alegação de risco fundamentada.",
        garantia_dispositivos=[{"doc_id": "d", "lei": "l", "artigo": "a"}],
        garantia_raciocinio="Raciocínio suficientemente longo.",
    )
    with pytest.raises(ValidationError):
        LaudoLLM(**base)


RECUPERADOS = {
    "lei11340_art7": {"artigos": ["Art. 7º"], "titulo": "Lei 11.340 — Art. 7º"},
    "cp_art147": {"artigos": ["Art. 147"], "titulo": "CP — Art. 147"},
}


def test_fundamentacao_ok():
    assert checar_fundamentacao(_laudo_ok(), RECUPERADOS) == []


def test_fundamentacao_doc_fora_dos_recuperados():
    laudo = _laudo_ok(
        garantia_dispositivos=[
            DispositivoCitado(doc_id="doc_inventado", lei="Lei 11.340/2006", artigo="Art. 7º")
        ]
    )
    erros = checar_fundamentacao(laudo, RECUPERADOS)
    assert any("doc_id fora" in e for e in erros)


def test_fundamentacao_artigo_nao_consta():
    laudo = _laudo_ok(
        garantia_dispositivos=[
            DispositivoCitado(doc_id="cp_art147", lei="Código Penal", artigo="Art. 999")
        ]
    )
    erros = checar_fundamentacao(laudo, RECUPERADOS)
    assert any("artigo nao consta" in e for e in erros)


def test_fundamentacao_apoio_fora_dos_recuperados():
    laudo = _laudo_ok(apoio=[{"doc_id": "caso_falso", "resumo": "resumo qualquer"}])
    erros = checar_fundamentacao(laudo, RECUPERADOS)
    assert any("caso de apoio fora" in e for e in erros)


def test_laudo_degradado_forma():
    deg = LaudoDegradado(
        trace_id="t-1", motivo="llm_indisponivel",
        score_probabilidade=80.0, alegacao_nivel="alto",
    )
    assert deg.degraded is True and deg.revisao_humana_obrigatoria is True
    with pytest.raises(ValidationError):
        LaudoDegradado(trace_id="t", motivo="motivo_inventado",
                       score_probabilidade=10, alegacao_nivel="alto")
