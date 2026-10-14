"""Preprocessamento lexical compartilhado pelos índices de recuperação."""

import re
import unicodedata


def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def tokenizar(t: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", normalizar(t))
