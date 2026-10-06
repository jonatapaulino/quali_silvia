"""Avaliação §4.2 — benchmark de encoders no dev, ablação, Hit Rate@5 no test.

Fluxo (respeita o congelamento dev/test do §6.1):
  1. BM25 isolado no dev e no test (baseline, nunca ajustado em test);
  2. para cada encoder (a)(b)(c): FAISS + híbrido avaliados no DEV;
  3. encoder vencedor = maior Hit Rate@5 no dev → avaliação final no TEST;
  4. ablação §4.2: BM25 | FAISS | BM25+FAISS no test; o braço "com grafo" fica
     fora enquanto não houver índice de grafo — registrado conforme a cláusula.

Uso: python scripts/avaliar_recuperacao.py [--encoders legal_bertimbau_sts,bge_m3]
"""

import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from arquitetura_tese import recuperacao
from arquitetura_tese.fusao import hit_rate_at_k
from arquitetura_tese.harness import wilson

GOLD = RAIZ / "conjuntos" / "gold_set.jsonl"
K = 5
K_RRF = 60  # [PROPOSTA] ajustável no dev


def carregar_gold(split: str) -> dict[str, set[str]]:
    gold = {}
    for l in GOLD.open(encoding="utf-8"):
        d = json.loads(l)
        if d["split"] == split:
            gold[d["query_id"]] = {r["doc_id"] for r in d["relevantes"]}
    return gold


def consultas(split: str) -> dict[str, str]:
    return {d["query_id"]: d["query_text"]
            for d in map(json.loads, GOLD.open(encoding="utf-8"))
            if d["split"] == split}


def medir(buscador, split: str) -> dict:
    gold = carregar_gold(split)
    resultados = {}
    for d in map(json.loads, GOLD.open(encoding="utf-8")):
        if d["split"] != split or d["query_id"] not in gold:
            continue
        # auto-match: a narrativa-fonte da consulta não pode ser resposta (ela
        # recuperaria a si mesma). Mascarada por convenção doc_id narr_<ep>.
        origem = d.get("origem", "").split("/")[-1]
        alvo_mascarado = f"narr_{origem}"
        top = [x for x in buscador(d["query_text"], K + 1) if x != alvo_mascarado][:K]
        resultados[d["query_id"]] = top
    hr = hit_rate_at_k(resultados, gold, k=K)
    lo, hi = wilson(int(round(hr * len(gold))), len(gold))
    return {"hit_rate": round(hr, 4), "ic95": [round(lo, 4), round(hi, 4)], "n": len(gold)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--encoders", default="legal_bertimbau_base,legal_bertimbau_sts,bge_m3")
    args = ap.parse_args()

    # O gold mede recuperação de DISPOSITIVOS (todos os relevantes o são):
    # o ramo de fundamentação (§4.4) busca no subcorpus legal; as narrativas
    # formam índice à parte, consumido como "caso de apoio" na geração.
    docs = recuperacao.montar_corpus(tipos=("dispositivo",))
    print(f"corpus: {len(docs)} docs "
          f"({sum(d['tipo'] == 'dispositivo' for d in docs)} dispositivos, "
          f"{sum(d['tipo'] == 'narrativa' for d in docs)} narrativas)")

    bm25 = recuperacao.IndiceBM25(docs)
    resultado = {"k": K, "k_rrf": K_RRF, "n_docs": len(docs), "dev": {}, "test": {}}

    resultado["dev"]["bm25"] = medir(bm25.buscar, "dev")
    resultado["test"]["bm25"] = medir(bm25.buscar, "test")
    print(f"baseline BM25: dev {resultado['dev']['bm25']['hit_rate']:.2%} | "
          f"test {resultado['test']['bm25']['hit_rate']:.2%}")

    for nome in args.encoders.split(","):
        print(f"carregando encoder {nome} ...")
        t0 = time.perf_counter()
        enc = recuperacao.ENCODERS[nome]()
        denso = recuperacao.IndiceDenso(docs, enc)
        resultado["dev"][f"faiss_{nome}"] = medir(denso.buscar, "dev")
        hibrido_busca = lambda q, k: recuperacao.hibrido(
            [bm25.buscar(q, k), denso.buscar(q, k)], k_rrf=K_RRF)[:k]
        resultado["dev"][f"hibrido_{nome}"] = medir(hibrido_busca, "dev")
        resultado["dev"][f"faiss_{nome}"]["meta"] = {
            "dim": int(denso.indice.d), "device": str(enc.device),
            "s_carga_indice": round(time.perf_counter() - t0, 2)}
        print(f"  dev: faiss {resultado['dev'][f'faiss_{nome}']['hit_rate']:.2%} | "
              f"híbrido {resultado['dev'][f'hibrido_{nome}']['hit_rate']:.2%}")

    # config vencedora no DEV (denso OU híbrido) -> avaliação única no TEST.
    # A ablação decide se a fusão RRF ajuda ou só adiciona latência (§4.2/D6).
    nomes_enc = [n for n in args.encoders.split(",") if n in recuperacao.ENCODERS]
    candidatos = [f"{m}_{n}" for n in nomes_enc for m in ("faiss", "hibrido")]
    melhor = max(candidatos, key=lambda n: resultado["dev"][n]["hit_rate"],
                 default=None)
    if melhor:
        modo, nome_enc = melhor.split("_", 1)
        denso = recuperacao.IndiceDenso(docs, recuperacao.ENCODERS[nome_enc]())
        busca = (denso.buscar if modo == "faiss" else
                 (lambda q, k: recuperacao.hibrido(
                     [bm25.buscar(q, k), denso.buscar(q, k)], k_rrf=K_RRF)[:k]))
        resultado["test"]["vencedor"] = medir(busca, "test")
        resultado["config_escolhida"] = melhor
        resultado["encoder_escolhido"] = nome_enc

    resultado["grafo"] = "fora do smoke: Neo4j exige índice próprio; entra só se "
    "o híbrido sem grafo não superar o melhor componente isolado (§4.2/D6)"

    saida = RAIZ / "dados" / "metricas_recuperacao.json"
    saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
