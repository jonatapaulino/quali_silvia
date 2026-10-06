"""Registra sha256 dos conjuntos versionados — trilha do relatório §6.6.

Uso: python scripts/registrar_hashes.py
Gera dados/hash_registry.json com hash de cada arquivo em conjuntos/ e dados/.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    arquivos = {}
    for pasta in (RAIZ / "conjuntos", RAIZ / "dados"):
        if not pasta.exists():
            continue
        for arq in sorted(pasta.rglob("*.jsonl")):
            if arq.name == "hash_registry.json":
                continue
            arquivos[str(arq.relative_to(RAIZ))] = sha256(arq)
    registro = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "arquivos": arquivos,
    }
    saida = RAIZ / "dados" / "hash_registry.json"
    saida.parent.mkdir(exist_ok=True)
    saida.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
    for k, v in arquivos.items():
        print(f"{v[:12]}  {k}")
    print(f"-> {saida}")


if __name__ == "__main__":
    sys.exit(main())
