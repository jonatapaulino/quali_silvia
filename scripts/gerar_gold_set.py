"""Deriva o gold set (§6.1) das narrativas sintéticas já geradas.

Cada narrativa vira uma consulta; os dispositivos_sugeridos viram os
relevantes (rótulo fraco — o especialista valida/corrige e ≥20% entra em
dupla anotação com kappa). Split 50/50 dev/test, estratificado pela presença
de dispositivos penais vs. Lei Maria da Penha.

Uso: python scripts/gerar_gold_set.py --n 100 --seed 42
"""

import argparse
import json
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from arquitetura_tese.dados import narrativas

ENTRADA = RAIZ / "dados" / "narrativas_sinteticas.jsonl"
SAIDA = RAIZ / "conjuntos" / "gold_set.jsonl"


def tem_penal(doc: dict) -> bool:
    return any("Penal" in d["lei"] or "CP" in d["lei"] for d in doc["dispositivos_sugeridos"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    docs = [json.loads(l) for l in ENTRADA.open(encoding="utf-8")]
    # rótulos não-discriminativos: os dispositivos BASE entram em toda narrativa
    # (art. 5º/7º são "relevantes" para tudo -> não medem nada). Gold = só
    # dispositivos implicados por feature ou classe. Consulta sem restante -> fora.
    base_ids = {d["doc_id"] for d in narrativas.DISPOSITIVOS_BASE}
    for d in docs:
        d["dispositivos_sugeridos"] = [
            x for x in d["dispositivos_sugeridos"] if x["doc_id"] not in base_ids]
    docs = [d for d in docs if d["dispositivos_sugeridos"]]
    rng = random.Random(args.seed)
    rng.shuffle(docs)

    penal = [d for d in docs if tem_penal(d)]
    so_lmp = [d for d in docs if not tem_penal(d)]
    metade = args.n // 2
    amostra = penal[: metade] + so_lmp[: args.n - metade]
    rng.shuffle(amostra)

    n_dev = len(amostra) // 2
    with SAIDA.open("w", encoding="utf-8") as f:
        for i, d in enumerate(amostra):
            f.write(json.dumps({
                "query_id": f"gs_{'dev' if i < n_dev else 'test'}_{i:04d}",
                "query_text": d["narrativa"],
                "relevantes": d["dispositivos_sugeridos"],
                "split": "dev" if i < n_dev else "test",
                "origem": f"sintetico_v1/{d['id_episodio']}",
            }, ensure_ascii=False) + "\n")

    print(f"{len(amostra)} consultas -> {SAIDA} "
          f"({n_dev} dev / {len(amostra) - n_dev} test; "
          f"{sum(tem_penal(d) for d in amostra)} com dispositivo penal)")
    print("PENDENTE: validação do especialista (>=20% dupla anotação, kappa) e hash.")


if __name__ == "__main__":
    main()
