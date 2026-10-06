# Arquitetura Tese — Smoke Test Neurossimbólico

Protótipo reproduzível de um sistema de apoio à **qualificação de risco de
violência recorrente contra a mulher**, construído para validar a arquitetura
proposta no DDA v5.3 (Documento de Definição de Arquitetura).

Combina três ramos com responsabilidades separadas:

1. **Risco (tabular)** — LightGBM sobre features estruturadas do episódio
   (histórico, ameaça de morte, arma, descumprimento de medida protetiva,
   controle coercitivo etc.), com split por grupo de agressor e early stopping.
2. **Evidência (retrieval)** — BM25 + FAISS/BGE-M3 sobre corpus legal oficial
   (Lei 11.340/2006, CP, LCP) e casos sintéticos similares.
3. **Redação (LLM)** — Mistral-7B local (Ollama) gera **somente** os campos
   textuais de um laudo estruturado Toulmin; nível de risco, incerteza e
   revisão humana são determinísticos — o LLM nunca decide.

Guardiões determinísticos envolvem tudo: verificação de citações contra as
evidências recuperadas (com re-tentativa corretiva), detector de injeção de
prompt, probe de conceitos (CAV), circuit breaker e saída degradada quando o
LLM falha.

## Resultados do smoke test (Seção 4 do DDA)

| Critério | Medido | Veredito |
|---|---|---|
| §4.1 Latência p95 (N=200, SLA 8,5 s) | 8,37 s | atendido no p95 (p99 13,1 s) |
| §4.2 Hit Rate@5 ≥ 0,85 | 0,815 (gold n=200) | **não atendido** |
| §4.3 Schema válido na 1ª tentativa | 200/200 (100%) | atendido |
| §4.4 Fundamentação (citações nos recuperados) | 97% após retry | atendido com flag |
| §4.5 AUC / Brier / ECE | 0,751 / 0,201 / 0,012 | atendido |
| §4.5 Anti-vazamento | controle flagra `score_geracao` (0,229) | atendido |
| §4.6 Probe CAV / injeção / override | AUC 0,78–1,00 · recall 1,0 | atendido |
| §4.7 Resiliência (caos + breaker) | degradado < 1,6 s | atendido |

Relatório completo: [`decisoes/relatorio_smoke.md`](decisoes/relatorio_smoke.md) ·
Documento de metodologia (PDF, 14 pág.):
[`decisoes/metodologia_smoke_test.pdf`](decisoes/metodologia_smoke_test.pdf) ·
Exemplos reais de classificação e laudos executados:
[`decisoes/exemplos_classificacao.md`](decisoes/exemplos_classificacao.md)

## Dados

- `dados/base_sintetica_risco.xlsx` — 20.200 episódios sintéticos, alvo
  `nova_agressao` (~50/50), ids estáveis de agressor/vítima.
- `dados/narrativas_sinteticas.jsonl` — 1.500 narrativas (BO, depoimento,
  pedido de MPU, histórico forense) geradas da própria base e vinculadas por id.
- `conjuntos/corpus_legal.jsonl` — 22 dispositivos com texto oficial do Planalto.
- `conjuntos/gold_set.jsonl` — 400 consultas (200 dev / 200 test) com rótulos
  fracos por regra feature→dispositivo.

**Nenhum dado real de tribunal é usado** — o protótipo valida o pipeline;
validade externa depende de dados reais e rótulos validados por especialista.

## Reproduzir

```bash
pip install -r requirements.txt
pip install faiss-cpu rank_bm25 sentence-transformers matplotlib  # Fase 2+
pytest tests/ -x -q            # 65 verificações

python scripts/analisar_base.py            # auditoria da base
python scripts/treinar_tabular.py          # LightGBM + early stopping (§4.5)
python scripts/baixar_corpus.py            # corpus legal (Planalto)
python scripts/gerar_corpus_sintetico.py --n 1500   # narrativas D7-b
python scripts/gerar_gold_set.py           # gold set de recuperação
python scripts/avaliar_recuperacao.py      # ablação de encoders (§4.2)
# LLM local: ollama pull mistral:7b && ollama serve
python scripts/medir_latencia.py --n 200   # §4.1/§4.3/§4.4
python scripts/testar_injecao.py           # §4.6 injeção
python scripts/treinar_probe_cav.py        # §4.6 probe de conceitos
python scripts/teste_caos.py               # §4.7 resiliência
python scripts/gerar_graficos.py           # figuras 1–4
python scripts/gerar_material_quali.py     # figuras 5–9 + dicionário
python scripts/gerar_exemplos_classificacao.py  # matriz + laudos exemplo
python scripts/gerar_pdf_metodologia.py    # PDF de metodologia
```

## Layout

```
arquitetura_tese/   pacote (tabular, recuperacao, evidencias, llm, prompts,
                    schemas, regras, fusao, guardiao, resiliencia, api)
scripts/            pipeline de treino, avaliação, caos e figuras
tests/              65 testes pytest (override, injeção, schema, retry)
conjuntos/          corpus legal + gold set + seeds §6.2/§6.3
dados/              base sintética, modelo treinado, métricas, figuras,
                    exemplos de laudo, hash_registry
decisoes/           ata de decisões D1–D9, relatório do smoke test,
                    PDF de metodologia, exemplos de classificação
```

## Limitações principais (declaradas, §6.6)

Base 100% sintética (prevalência e rótulos artificiais); latência medida
sequencial com modelo quente; §4.2 abaixo do limiar motiva fine-tuning do
encoder com rótulos reais; caos §4.7 adaptado ao Ollama nativo (falta
`docker pause` real); gold pendente de validação do especialista (kappa).
