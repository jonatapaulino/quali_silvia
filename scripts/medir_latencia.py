"""Medição de latência §4.1 — pipeline completo ponta a ponta.

Estágios medidos por requisição (ms):
  t_tabular   — predizer_tabular (LightGBM)
  t_retrieval — montar_evidencias (encode BGE-M3 da consulta + FAISS)
  t_llm       — chamar_ollama (Mistral 7B, saída restrita ao schema)
  t_montagem  — montar_laudo + checar_fundamentacao (determinísticos)
  t_total     — soma (≈ SLA síncrono de 8,5 s, D5)

Também registra: taxa de sucesso de schema em 1ª tentativa (§4.3) e taxa de
citação fundamentada (§4.4) — prévias das métricas dedicadas.

Uso: python scripts/medir_latencia.py [--n 200] [--saida dados/metricas_latencia.json]
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import httpx

from arquitetura_tese import evidencias, recuperacao
from arquitetura_tese.dados.narrativas import iterar_episodios
from arquitetura_tese.resiliencia import gerar_fundamentado, montar_laudo
from arquitetura_tese.tabular import FEATURES, predizer_tabular

NARRATIVAS = RAIZ / "dados" / "narrativas_sinteticas.jsonl"


def percentis(xs: list[float]) -> dict:
    xs = sorted(xs)
    q = lambda p: xs[min(len(xs) - 1, int(len(xs) * p))]
    return {"p50": round(q(0.50), 1), "p95": round(q(0.95), 1),
            "p99": round(q(0.99), 1), "max": round(xs[-1], 1), "n": len(xs)}


def carregar_casos(n: int) -> list[dict]:
    narr_por_ep = {json.loads(l)["id_episodio"]: json.loads(l)["narrativa"]
                   for l in NARRATIVAS.open(encoding="utf-8")}
    from arquitetura_tese.tabular import BASE_XLSX
    eps = {e["id_episodio"]: e for e in iterar_episodios(BASE_XLSX)
           if e["id_episodio"] in narr_por_ep}
    casos = []
    for i, ep_id in enumerate(sorted(eps)[:n]):
        e = eps[ep_id]
        casos.append({
            **e, "trace_id": f"lat_{i:04d}",
            "metadados": {k: e[k] for k in FEATURES if k in e},
            "narrativa": narr_por_ep[ep_id],
            "_narr_doc": f"narr_{ep_id}",
        })
    return casos


async def medir(n: int) -> dict:
    casos = carregar_casos(n)
    print(f"{len(casos)} casos; montando índices densos (encoder em cache) ...")
    t0 = time.perf_counter()
    _, indices = evidencias.montar_indices()
    t_indices = time.perf_counter() - t0
    print(f"índices prontos em {t_indices:.1f}s — iniciando medições")

    tempos = {k: [] for k in ("tabular", "retrieval", "llm", "montagem", "total")}
    falhas_schema = falhas_fund = n_retentativas = 0
    async with httpx.AsyncClient() as client:
        for i, caso in enumerate(casos):
            t0 = time.perf_counter()
            score = predizer_tabular(caso)
            t1 = time.perf_counter()
            caso["evidencias"] = evidencias.montar_evidencias(
                caso["narrativa"], indices, excluir_doc=caso["_narr_doc"])
            t2 = time.perf_counter()
            try:
                bruto, erros, tent = await gerar_fundamentado(client, caso, score)
            except Exception as e:  # noqa: BLE001 — falha de schema/rede conta §4.3
                falhas_schema += 1
                if i % 20 == 0:
                    print(f"  [{i}] falha: {type(e).__name__}")
                continue
            t3 = time.perf_counter()
            montar_laudo(caso, score, bruto)
            falhas_fund += bool(erros)
            n_retentativas += tent - 1
            t4 = time.perf_counter()
            tempos["tabular"].append((t1 - t0) * 1000)
            tempos["retrieval"].append((t2 - t1) * 1000)
            tempos["llm"].append((t3 - t2) * 1000)
            tempos["montagem"].append((t4 - t3) * 1000)
            tempos["total"].append((t4 - t0) * 1000)
            if i % 20 == 0:
                print(f"  [{i}] total={tempos['total'][-1]:.0f}ms")

    n_ok = len(tempos["total"])
    return {
        "n_requisicoes": n, "n_sucesso": n_ok,
        "schema_pass_1a": round(n_ok / n, 4) if n else 0,
        "fundamentacao_ok": round(1 - falhas_fund / max(n_ok, 1), 4),
        "retentativas_fundamentacao": n_retentativas,
        "t_indice_uma_vez_s": round(t_indices, 1),
        "estagios_ms": {k: percentis(v) for k, v in tempos.items() if v},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--saida", default=str(RAIZ / "dados" / "metricas_latencia.json"))
    args = ap.parse_args()
    resultado = asyncio.run(medir(args.n))
    Path(args.saida).write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
