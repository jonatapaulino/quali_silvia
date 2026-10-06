"""Gera o corpus de narrativas sintéticas (D7-b) a partir de base_sintetica_risco.xlsx.

Uso:
    python scripts/gerar_corpus_sintetico.py --n 300 --seed 42
    python scripts/gerar_corpus_sintetico.py --n 5 --mostrar

Saída: dados/narrativas_sinteticas.jsonl (versionar e hashear — §6.6).
"""

import argparse
import json
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from arquitetura_tese.dados.narrativas import gerar_documento, iterar_episodios


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", default=str(RAIZ / "dados" / "base_sintetica_risco.xlsx"))
    ap.add_argument("--n", type=int, default=300, help="episódios a amostrar (0 = todos)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--saida", default=str(RAIZ / "dados" / "narrativas_sinteticas.jsonl"))
    ap.add_argument("--mostrar", action="store_true", help="imprime exemplos no stdout")
    args = ap.parse_args()

    episodios = [e for e in iterar_episodios(args.xlsx) if e.get("id_episodio")]
    rng_amostra = random.Random(args.seed)
    if args.n and args.n < len(episodios):
        episodios = rng_amostra.sample(episodios, args.n)

    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    n_conceitos = 0
    with saida.open("w", encoding="utf-8") as f:
        for i, ep in enumerate(episodios):
            doc = gerar_documento(ep, random.Random((args.seed, i).__hash__()))
            n_conceitos += bool(doc["conceitos"])
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            if args.mostrar and i < 3:
                print(json.dumps(doc, ensure_ascii=False, indent=1), "\n")

    print(f"{len(episodios)} narrativas -> {saida}")
    print(f"episódios com >=1 conceito rotulado (probe CAV): {n_conceitos}")


if __name__ == "__main__":
    main()
