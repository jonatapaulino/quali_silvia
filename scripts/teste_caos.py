"""§4.7 — Cenários de caos sobre gerar_laudo.

Adaptação honesta: o DDA prevê `docker pause` em contêiner; o Ollama roda
NATIVO nesta máquina (Docker Desktop indisponível). Equivalências usadas:
  (a) serviço parado      -> base_url em porta morta
  (b) serviço travado     -> soquete local que aceita conexão e nunca responde
  (c) pane na geração     -> taskkill do processo ollama.exe durante a chamada

Em todos: espera-se LaudoDegradado + motivo correto + caminho degradado < 1 s
e abertura do circuito após 3 falhas (CircuitBreaker.falhas_max).
"""

import asyncio
import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import httpx

from arquitetura_tese.resiliencia import CircuitBreaker, gerar_laudo
from arquitetura_tese.schemas import LaudoDegradado
from arquitetura_tese.tabular import BASE_XLSX
from arquitetura_tese.dados.narrativas import iterar_episodios

OLLAMA = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Ollama" / "ollama.exe"


def caso_minimo() -> dict:
    from arquitetura_tese.tabular import FEATURES
    e = next(iterar_episodios(BASE_XLSX))
    return {**e, "trace_id": "caos_0", "narrativa": "teste",
            "metadados": {k: e[k] for k in FEATURES if k in e}}


def servidor_travado(porta: int) -> socket.socket:
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", porta))
    srv.listen(4)
    def aceitar():
        while True:
            try:
                conn, _ = srv.accept()
                threading.Thread(target=lambda c: time.sleep(30) or c.close(),
                                 args=(conn,), daemon=True).start()
            except OSError:
                return
    threading.Thread(target=aceitar, daemon=True).start()
    return srv


async def cenario_a(caso) -> dict:
    t0 = time.perf_counter()
    async with httpx.AsyncClient() as c:
        r = await gerar_laudo(caso, c, CircuitBreaker(),
                              base_url="http://127.0.0.1:59999")
    return {"motivo": getattr(r, "motivo", None), "ms": round((time.perf_counter() - t0) * 1000),
            "degradado": isinstance(r, LaudoDegradado)}


async def cenario_b(caso) -> dict:
    srv = servidor_travado(59998)
    try:
        t0 = time.perf_counter()
        async with httpx.AsyncClient() as c:
            r = await gerar_laudo(caso, c, CircuitBreaker(),
                                  base_url="http://127.0.0.1:59998")
        return {"motivo": getattr(r, "motivo", None),
                "ms": round((time.perf_counter() - t0) * 1000),
                "degradado": isinstance(r, LaudoDegradado)}
    finally:
        srv.close()


async def cenario_c(caso) -> dict:
    # garante ollama no ar
    async with httpx.AsyncClient() as c:
        try:
            await c.get("http://localhost:11434/", timeout=2)
        except httpx.HTTPError:
            subprocess.Popen([str(OLLAMA), "serve"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            await asyncio.sleep(6)
    breaker = CircuitBreaker()
    t0 = time.perf_counter()
    async with httpx.AsyncClient() as c:
        tarefa = asyncio.create_task(gerar_laudo(caso, c, breaker))
        await asyncio.sleep(1.5)  # geração em curso
        subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"],
                       capture_output=True)
        r = await tarefa
    res = {"motivo": getattr(r, "motivo", None),
           "ms": round((time.perf_counter() - t0) * 1000),
           "degradado": isinstance(r, LaudoDegradado)}
    # reinicia o serviço para os próximos cenários/uso
    subprocess.Popen([str(OLLAMA), "serve"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res


async def cenario_breaker(caso) -> dict:
    b = CircuitBreaker(falhas_max=3)
    motivos = []
    async with httpx.AsyncClient() as c:
        for _ in range(4):
            r = await gerar_laudo(caso, c, b, base_url="http://127.0.0.1:59999")
            motivos.append(getattr(r, "motivo", None))
    return {"motivos_sequencia": motivos,
            "abriu_no_4o": motivos[-1] == "circuit_open"}


async def main() -> None:
    caso = caso_minimo()
    resultado = {
        "a_servico_parado": await cenario_a(caso),
        "b_servico_travado": await cenario_b(caso),
        "breaker_3_falhas": await cenario_breaker(caso),
        "c_pane_na_geracao": await cenario_c(caso),
    }
    resultado["nota"] = ("Ollama nativo (sem contêiner): cenários adaptados de "
                         "docker pause para porta morta/soquete travado/taskkill")
    (RAIZ / "dados" / "metricas_caos.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
