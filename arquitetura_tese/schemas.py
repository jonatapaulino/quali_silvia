"""Schemas do laudo — DDA v5.3 §5.1 (schema_version "1.0", Pydantic v2).

O LLM gera apenas LaudoLLM (texto). O orquestrador monta LaudoFinal com Dados,
nível de risco e Qualificador determinísticos (D4-b, D9-b). Se o fallback for
acionado, a API devolve LaudoDegradado.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NivelRisco(str, Enum):
    BAIXO = "baixo"
    MODERADO = "moderado"
    ALTO = "alto"
    CRITICO = "critico"


class Incerteza(str, Enum):
    BAIXA = "baixa"
    MODERADA = "moderada"
    ALTA = "alta"


class Estrito(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DispositivoCitado(Estrito):
    doc_id: str = Field(min_length=1)  # deve existir nos documentos recuperados
    lei: str = Field(min_length=1)     # ex.: "Lei 11.340/2006"
    artigo: str = Field(min_length=1)  # ex.: "Art. 7º"


class CasoApoio(Estrito):
    doc_id: str = Field(min_length=1)
    resumo: str = Field(min_length=1, max_length=400)


class LaudoLLM(Estrito):
    alegacao_enunciado: str = Field(min_length=10, max_length=400)
    garantia_dispositivos: list[DispositivoCitado] = Field(min_length=1)
    garantia_raciocinio: str = Field(min_length=10, max_length=600)
    apoio: list[CasoApoio] = Field(default_factory=list, max_length=5)
    refutacao: str = Field(min_length=1, max_length=600)


class Dados(Estrito):
    score_probabilidade: float = Field(ge=0, le=100)
    metadados: dict[str, str | int | float | bool | None]


class Qualificador(Estrito):
    incerteza: Incerteza
    motivos: list[str] = Field(min_length=1)


class LaudoFinal(Estrito):
    schema_version: Literal["1.0"] = "1.0"
    trace_id: str
    degraded: Literal[False] = False
    alegacao_nivel: NivelRisco
    alegacao_enunciado: str
    dados: Dados
    garantia_dispositivos: list[DispositivoCitado] = Field(min_length=1)
    garantia_raciocinio: str
    apoio: list[CasoApoio]
    refutacao: str = Field(min_length=1)
    refutacao_flags: list[str] = Field(default_factory=list)
    qualificador: Qualificador
    revisao_humana_obrigatoria: bool


class LaudoDegradado(Estrito):
    schema_version: Literal["1.0"] = "1.0"
    trace_id: str
    degraded: Literal[True] = True
    motivo: Literal["circuit_open", "llm_indisponivel", "llm_timeout", "erro_geracao"]
    score_probabilidade: float = Field(ge=0, le=100)
    alegacao_nivel: NivelRisco
    revisao_humana_obrigatoria: Literal[True] = True


def checar_fundamentacao(laudo: LaudoLLM, recuperados: dict[str, dict]) -> list[str]:
    """Checagem determinística anti-alucinação (§4.4). Lista vazia = ok.

    Requer que cada documento indexado tenha o metadado "artigos" (list[str]).
    """
    erros = []
    for d in laudo.garantia_dispositivos:
        doc = recuperados.get(d.doc_id)
        if doc is None:
            erros.append(f"doc_id fora dos recuperados: {d.doc_id}")
        elif d.artigo not in doc.get("artigos", []):
            erros.append(f"artigo nao consta em {d.doc_id}: {d.artigo}")
    for c in laudo.apoio:
        if c.doc_id not in recuperados:
            erros.append(f"caso de apoio fora dos recuperados: {c.doc_id}")
    return erros
