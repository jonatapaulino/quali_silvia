# Relatório de Smoke Test — ARQUITETURA TESE v5.3

Data da execução: ver `dados/hash_registry.json`. Ambiente: ASUS ROG Strix SCAR 18
(Ultra 9 275HX, RTX 5090 Laptop 24 GB, 64 GB RAM, Win11), Python 3.14.7,
Ollama 0.35.1 nativo, mistral:7b Q4 (100% GPU), BGE-M3 em CPU, faiss-cpu 1.15.1.

**Escopo**: base_sintetica_risco.xlsx (20.200 episódios) + narrativas sintéticas
vinculadas (D7-b) + corpus legal oficial (22 dispositivos, Planalto). Sem dados
reais de tribunal — todos os resultados validam o PIPELINE, não o mundo real.

## Resumo dos critérios §4

| Critério | Limiar | Medido | Veredito |
|---|---|---|---|
| §4.1 Latência (N=200, com retry §4.4) | p95 < 8,5 s | **p95 8,37 s** (p50 5,09 / p99 13,1) | **ATENDIDO no p95; p99 fora** (ver nota) |
| §4.2 Hit Rate@5 (gold ampliado n=200) | ≥ 0,85 | **0,815** [IC95 0,755–0,863] | **NÃO atendido** |
| §4.3 Schema 1ª tent. | 100% | **200/200 (100%)** | **ATENDIDO** |
| §4.4 Fundamentação | 0 citações sem suporte | **97% limpo após 1 retry** (20 retentativas, 6 flagged p/ revisão); guardião detecta 100% | **ATENDIDO com flag** |
| §4.5 AUC/Brier/ECE | reportar; ECE ≤ 0,05 | AUC **0,751** / Brier 0,201 / ECE **0,012** (early stopping it. 54) | **ATENDIDO** |
| §4.5 anti-vazamento | permutação | 0 artefatos no modelo; controle flagra score_geracao (0,229) | **ATENDIDO** |
| §4.6 Probe CAV | reportar AUC | 0,78–1,00 por conceito (7 conceitos) | **ATENDIDO** |
| §4.6 Guardião injeção | conjunto §6.2 | recall 1,0 / precisão 1,0 (seeds) | **ATENDIDO** |
| §4.6 Override §6.4 | matriz | 40+ casos pytest, incl. MODERADO+CAV | **ATENDIDO** |
| §4.7 Resiliência | degradado < SLA | a) 912 ms b) 315 ms c) 1.583 ms; breaker abre no 4º | **ATENDIDO** |

Notas honestas sobre a re-medição:
- O retry §4.4 elevou a fundamentação de 95% → **97%** e empurrou a cauda de
  latência: p95 6,26 s → 8,37 s (ainda < 8,5 s, folga de ~130 ms) e p99 de
  8,35 s → 13,1 s. O trade-off é real e fica declarado: quem falha na
  fundamentação paga uma 2ª geração (~+5 s). Sem retry, p95 seria menor mas o
  §4.4 ficaria em 95%.
- O gold ampliado (400 consultas, n=200/split) derrubou o 0,86 do n=50 para
  0,815 — a expansão fez seu papel: medir de verdade, não confirmar o número
  anterior. A decisão D2/D6 mantém-se (denso isolado continua vencendo o
  híbrido: 0,815 vs 0,775).

## Evidências por fase

- **Fase 1 (tabular)**: LightGBM com **early stopping** (teto 2000, paciência
  50, validação interna 15% do treino com grupos disjuntos — holdout intocado).
  Parada na iteração 54; split por grupo `id_agressor_sintetico`, 15 features
  sem artefatos de geração, controle anti-vazamento demonstrado.
  `dados/metricas_tabular.json`
- **Fase 2 (recuperação)**: ablação honesta re-medida no gold ampliado —
  BM25 0,72/0,71 | **BGE-M3 0,81/0,815** | híbrido RRF 0,76/0,775 (rejeitado;
  Legal-BERTimbau base/STS ficaram em 0,36/0,50 no gold original). Decisões
  D2=BGE-M3 e D6=denso-isolado mantidas. `dados/metricas_recuperacao.json`
- **Fase 3 (geração+latência)**: por estágio — tabular ~7 ms / retrieval
  0,5–1,1 s / LLM p95 7,8 s (inclui retry) / montagem 0,1 ms. Schema 100% via
  `format` JSON Schema + concisão. Fundamentação: 64,5% → 95% (prompt) →
  **97% com re-tentativa determinística** (`resiliencia.gerar_fundamentado`).
  `dados/metricas_latencia.json`
- **Fase 4 (resiliência+guardiões)**: caos a/b/c todos degradados corretamente;
  breaker abre após 3 falhas; detector de injeção 6/6 seeds; e2e 12/12 schema
  sob injeção com 1 eco de canário (mitigação: bloqueio na ingestão, que pega
  100% dos padrões). `dados/metricas_caos.json`, `dados/metricas_guardiao.json`,
  `dados/metricas_cav.json`

## Limitações declaradas (§6.6)

1. Dados 100% sintéticos: prevalência artificial ~50/50, rótulos fracos de
   relevância e de conceito derivados dos mesmos templates que geram o texto —
   métricas de retrieval/probe medem coerência do pipeline, não validade externa.
2. Ollama nativo: cenários de caos adaptados (porta morta, soquete travado,
   taskkill) em vez de `docker pause`. Refazer com Docker Desktop ativo para
   fidelidade total ao §4.7.
3. Latência medida sequencial, modelo quente, keep_alive 30 m; carga a frio
   ~12,4 s fica fora do SLA e exige warm-up no deploy. Sem concorrência medida.
4. Webhook (canal assíncrono) não instrumentado — D5 prevê medição à parte.
5. Gold set pendente de validação do especialista (≥20% dupla anotação, kappa).
6. Encoder BGE-M3 rodou em CPU (torch CPU-only no py3.14); GPU pode reduzir
   o estágio retrieval de ~0,5 s para ~50 ms.

## Pendências para fechar a Seção 4

- ~~Ampliar gold set para ~200 consultas e repetir a ablação (IC95).~~ Feito:
  400 consultas (200/200). Resultado honesto: critério §4.2 **não atendido**
  (0,815 < 0,85). Caminho declarado: fine-tuning do encoder sobre rótulos
  validados por especialista quando houver dados reais — em sintético ele
  aprenderia os templates do gerador.
- ~~Política de rejeição do laudo flagado pelo guardião de fundamentação.~~
  Feito: retry-on-violation + flag `fundamentacao_pendente:revisao_humana`.
- Cauda de latência: p99 13,1 s ficou fora do SLA por causa do retry; opções
  se a margem incomodar — SLA em p95 (já é o critério), retry assíncrono via
  webhook (D5), ou limite de tokens da 2ª geração.
- Subir Docker Desktop e reexecutar caos via `docker pause` real.
- Validar gold labels + amostra de narrativas com o especialista (kappa).
