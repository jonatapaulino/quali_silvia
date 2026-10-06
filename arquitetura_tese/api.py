"""API do score tabular — Fase 1 (§4.5: probabilidade + log para anômalos).

Execução: uvicorn arquitetura_tese.api:app --port 8000
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .tabular import EntradaAnomala, predizer_tabular

app = FastAPI(title="ARQUITETURA TESE — score tabular", version="0.0.1")


@app.post("/score")
def score(caso: dict):
    try:
        return {"score_probabilidade": predizer_tabular(caso)}
    except EntradaAnomala as e:
        return JSONResponse(status_code=422, content=e.detalhe)


@app.get("/saude")
def saude():
    return {"status": "ok"}
