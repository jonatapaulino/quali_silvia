"""Configuração central — única fonte do layout de diretórios, variáveis
de ambiente e endpoints. Nenhum módulo deve recomputar caminhos por conta
própria: importe daqui para que a troca da fonte de dados ou do endpoint
aconteça em um só lugar (ver decisoes/handoff_dados_reais.md).
"""

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "dados"
CONJUNTOS = RAIZ / "conjuntos"

BASE_XLSX = DADOS / "base_sintetica_risco.xlsx"
NARRATIVAS = DADOS / "narrativas_sinteticas.jsonl"
CORPUS_LEGAL = CONJUNTOS / "corpus_legal.jsonl"

MODELO_PATH = Path(os.environ.get("ARQUITETURA_TESE_MODELO", DADOS / "modelo_tabular.txt"))
META_PATH = MODELO_PATH.with_suffix(".meta.json")

OLLAMA_URL = "http://localhost:11434"
PROBE_TIMEOUT_S = 0.3
LLM_TIMEOUT_S = 10.0  # [PROPOSTA] §4.7 cenário (c)
