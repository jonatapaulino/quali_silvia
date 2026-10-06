"""Baixa o texto oficial dos dispositivos do corpus (planalto.gov.br).

Extrai os artigos listados em arquitetura_tese/corpus.py das páginas compiladas e
grava conjuntos/corpus_legal.jsonl — insumo da indexação (§4.2).

Uso: python scripts/baixar_corpus.py
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from arquitetura_tese.corpus import DISPOSITIVOS

FONTES = {
    "Lei 11.340/2006": "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm",
    "Código Penal": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm",
    "Decreto-Lei 3.688/1941": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del3688.htm",
}


def baixar(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16", errors="replace")
    for enc in ("utf-8", "latin-1", "windows-1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def limpar_html(html: str) -> str:
    txt = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    txt = re.sub(r"(?s)<[^>]+>", " ", txt)
    txt = txt.replace("&nbsp;", " ").replace("&ordm;", "º").replace("&ordf;", "ª")
    txt = txt.replace("&sect;", "§").replace("&ccedil;", "ç").replace("&atilde;", "ã")
    txt = txt.replace("&quot;", '"').replace("&amp;", "&")
    return re.sub(r"[ \t]+", " ", txt)


def numero_artigo(rotulo: str) -> str:
    """'Art. 129, § 9º' -> '129'; 'Art. 24-A' -> '24-A'; 'Art. 121, § 2º-A' -> '121'."""
    m = re.search(r"(\d+(-[A-Z])?)", rotulo)
    return m.group(1) if m else ""


def extrair_artigo(texto_plano: str, rotulo: str) -> str:
    """Extrai caput + parágrafos/incisos até o próximo 'Art.'."""
    n = numero_artigo(rotulo)
    m = re.search(rf"Art\.\s*{re.escape(n)}[^\d]", texto_plano)
    if not m:
        return ""
    inicio = m.start()
    fim = re.search(r"\n\s*Art\.\s*\d", texto_plano[inicio + 10:])
    trecho = texto_plano[inicio: inicio + 10 + (fim.start() if fim else 3000)]
    if "§" in rotulo:  # para dispositivos com §, o trecho do artigo inteiro basta
        pass
    trecho = re.sub(r"\s+", " ", trecho).strip()
    return trecho[:3000]


def main() -> None:
    paginas = {}
    for lei, url in FONTES.items():
        try:
            paginas[lei] = limpar_html(baixar(url))
            print(f"{lei}: {len(paginas[lei])} chars baixados")
        except Exception as e:
            paginas[lei] = ""
            print(f"{lei}: FALHA no download ({e})")

    saida = RAIZ / "conjuntos" / "corpus_legal.jsonl"
    faltando = []
    with saida.open("w", encoding="utf-8") as f:
        for d in DISPOSITIVOS:
            texto = extrair_artigo(paginas.get(d["lei"], ""), d["artigo"])
            if not texto:
                faltando.append(d["doc_id"])
            f.write(json.dumps({
                "doc_id": d["doc_id"], "lei": d["lei"], "artigo": d["artigo"],
                "tema": d["tema"], "artigos": [d["artigo"]], "texto": texto,
            }, ensure_ascii=False) + "\n")
    print(f"-> {saida}")
    if faltando:
        print(f"ARTIGOS SEM TEXTO ({len(faltando)}): {faltando}")


if __name__ == "__main__":
    main()
