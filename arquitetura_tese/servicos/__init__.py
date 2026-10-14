"""Camada de aplicação — serviços que compõem os ramos de infraestrutura.

- guardiao.py: defesas determinísticas de prompt e ingestão (§4.6, §6.3);
- evidencias.py: composição retrieval→placeholder {evidencias} do §5.7;
- resiliencia.py: circuit breaker, health probe e resposta degradada (§5.4);
- pipeline.py: orquestração do laudo (score → LLM → verificação → LaudoFinal).
"""
