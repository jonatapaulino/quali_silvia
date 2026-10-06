


def _laudo(doc_id="cp_art147", artigo="Art. 147", raciocinio="ameaça tipificada"):
    from arquitetura_tese.schemas import LaudoLLM
    return LaudoLLM(
        alegacao_enunciado="risco de ameaça recorrente",
        garantia_dispositivos=[{"doc_id": doc_id, "lei": "CP", "artigo": artigo}],
        garantia_raciocinio=raciocinio, apoio=[],
        refutacao="dados sintéticos limitados")


def test_retentativa_fundamentacao(monkeypatch):
    """§4.4: 1ª tentativa com citação inválida -> re-tentativa com feedback."""
    import asyncio
    import arquitetura_tese.llm as llm_mod
    from arquitetura_tese.resiliencia import gerar_fundamentado

    caso = {"trace_id": "t", "evidencias": [
        {"doc_id": "cp_art147", "artigos": ["Art. 147"]}]}
    chamadas = []
    ruim, bom = _laudo(artigo="Art. 999"), _laudo()

    async def fake(client, caso, score, base_url=None):
        chamadas.append(caso.get("correcao_fundamentacao"))
        return ruim if len(chamadas) == 1 else bom

    monkeypatch.setattr(llm_mod, "chamar_ollama", fake)
    bruto, erros, tent = asyncio.run(gerar_fundamentado(None, caso, 0.7))
    assert tent == 2 and erros == [] and bruto is bom
    assert chamadas[1]  # feedback do erro injetado na 2ª chamada


def test_retentativa_persistente_flaga(monkeypatch):
    """Se a 2ª tentativa ainda viola, o erro é reportado (não escondido)."""
    import asyncio
    import arquitetura_tese.llm as llm_mod
    from arquitetura_tese.resiliencia import gerar_fundamentado

    caso = {"trace_id": "t", "evidencias": [
        {"doc_id": "cp_art147", "artigos": ["Art. 147"]}]}

    async def fake(*a, **k):
        return _laudo(doc_id="cp_art999", artigo="Art. 999")

    monkeypatch.setattr(llm_mod, "chamar_ollama", fake)
    bruto, erros, tent = asyncio.run(gerar_fundamentado(None, caso, 0.7))
    assert tent == 2 and erros  # violação persistiu e é reportada


def test_sem_violacao_nao_retenta(monkeypatch):
    import asyncio
    import arquitetura_tese.llm as llm_mod
    from arquitetura_tese.resiliencia import gerar_fundamentado

    caso = {"trace_id": "t", "evidencias": [
        {"doc_id": "cp_art147", "artigos": ["Art. 147"]}]}
    n = [0]

    async def fake(*a, **k):
        n[0] += 1
        return _laudo()

    monkeypatch.setattr(llm_mod, "chamar_ollama", fake)
    bruto, erros, tent = asyncio.run(gerar_fundamentado(None, caso, 0.7))
    assert n[0] == 1 and tent == 1 and erros == []
