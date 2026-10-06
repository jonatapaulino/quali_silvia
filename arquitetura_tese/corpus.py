"""Corpus legal a indexar — seed para a Fase 2 (DDA v5.3 §4.2, §6.1).

doc_id estável por dispositivo. O campo "texto" deve ser preenchido com o
inteiro teor oficial (planalto.gov.br) na ingestão — [VERIFICAR] a lista final
com o especialista jurídico durante a anotação do gold set.
Todo documento indexado DEVE carregar o metadado "artigos": list[str] —
contrato exigido por checar_fundamentacao (§4.4).
"""

DISPOSITIVOS: list[dict] = [
    # Lei 11.340/2006 (Maria da Penha) — núcleo do domínio
    {"doc_id": "lei11340_art5", "lei": "Lei 11.340/2006", "artigo": "Art. 5º", "tema": "definição de violência doméstica e familiar contra a mulher", "texto": ""},
    {"doc_id": "lei11340_art7", "lei": "Lei 11.340/2006", "artigo": "Art. 7º", "tema": "formas de violência (física, psicológica, sexual, patrimonial, moral)", "texto": ""},
    {"doc_id": "lei11340_art12", "lei": "Lei 11.340/2006", "artigo": "Art. 12", "tema": "procedimento em inquérito policial", "texto": ""},
    {"doc_id": "lei11340_art18", "lei": "Lei 11.340/2006", "artigo": "Art. 18", "tema": "competência e medidas protetivas — cabimento", "texto": ""},
    {"doc_id": "lei11340_art19", "lei": "Lei 11.340/2006", "artigo": "Art. 19", "tema": "medidas protetivas de urgência ao ofensor", "texto": ""},
    {"doc_id": "lei11340_art22", "lei": "Lei 11.340/2006", "artigo": "Art. 22", "tema": "medidas protetivas de urgência à ofendida", "texto": ""},
    {"doc_id": "lei11340_art24a", "lei": "Lei 11.340/2006", "artigo": "Art. 24-A", "tema": "descumprimento de medida protetiva — crime", "texto": ""},
    {"doc_id": "lei11340_art38a", "lei": "Lei 11.340/2006", "artigo": "Art. 38-A", "tema": "Banco Nacional de Medidas Protetivas (BNMPU)", "texto": ""},
    # Código Penal — tipos incidentes no domínio
    {"doc_id": "cp_art121_2a", "lei": "Código Penal", "artigo": "Art. 121, § 2º-A", "tema": "feminicídio", "texto": ""},
    {"doc_id": "cp_art129_9", "lei": "Código Penal", "artigo": "Art. 129, § 9º", "tema": "lesão corporal doméstica contra a mulher", "texto": ""},
    {"doc_id": "cp_art138", "lei": "Código Penal", "artigo": "Art. 138", "tema": "calúnia", "texto": ""},
    {"doc_id": "cp_art139", "lei": "Código Penal", "artigo": "Art. 139", "tema": "difamação", "texto": ""},
    {"doc_id": "cp_art140", "lei": "Código Penal", "artigo": "Art. 140", "tema": "injúria", "texto": ""},
    {"doc_id": "cp_art147", "lei": "Código Penal", "artigo": "Art. 147", "tema": "ameaça", "texto": ""},
    {"doc_id": "cp_art147a", "lei": "Código Penal", "artigo": "Art. 147-A", "tema": "perseguição (stalking)", "texto": ""},
    {"doc_id": "cp_art148", "lei": "Código Penal", "artigo": "Art. 148", "tema": "sequestro e cárcere privado", "texto": ""},
    {"doc_id": "cp_art150", "lei": "Código Penal", "artigo": "Art. 150", "tema": "violação de domicílio", "texto": ""},
    {"doc_id": "cp_art163", "lei": "Código Penal", "artigo": "Art. 163", "tema": "dano", "texto": ""},
    {"doc_id": "cp_art213", "lei": "Código Penal", "artigo": "Art. 213", "tema": "estupro", "texto": ""},
    {"doc_id": "cp_art215a", "lei": "Código Penal", "artigo": "Art. 215-A", "tema": "importunação sexual", "texto": ""},
    {"doc_id": "cp_art216a", "lei": "Código Penal", "artigo": "Art. 216-A", "tema": "assédio sexual", "texto": ""},
    # Lei de Contravenções Penais
    {"doc_id": "lcp_art21", "lei": "Decreto-Lei 3.688/1941", "artigo": "Art. 21", "tema": "vias de fato", "texto": ""},
]


def corpus_para_indexacao() -> list[dict]:
    """Documentos no formato esperado pelo índice: metadado 'artigos' obrigatório."""
    docs = []
    for d in DISPOSITIVOS:
        docs.append({
            "doc_id": d["doc_id"],
            "titulo": f"{d['lei']} — {d['artigo']} ({d['tema']})",
            "artigos": [d["artigo"]],
            "lei": d["lei"],
            "texto": d["texto"],
        })
    return docs
