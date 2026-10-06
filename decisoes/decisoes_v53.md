# ARQUITETURA TESE — Registro de decisões (DDA v5.3, Fase 0)

Data: 2026-10-05. Ambiente medido na máquina de referência.

## §3.2 — Dados e insumos

### D1 — Hardware de referência (medido)

| Item | Valor |
|---|---|
| Máquina | ASUS ROG Strix SCAR 18 G835LX |
| CPU | Intel Core Ultra 9 275HX, 24C/24T @ 2,7 GHz |
| GPU | NVIDIA RTX 5090 Laptop, 24.463 MiB VRAM |
| Driver / CUDA | 610.88 / CUDA 13.3 |
| RAM | 64 GB |
| SO | Windows 11 Home SL, build 26200, x64 |
| Docker | 29.8.0 (verificar `docker run --gpus all` para cenários §4.7) |
| Ollama | **pendente de instalação** — registrar versão ao instalar (suporte sm_120/Blackwell) |

Condições de medição: energia na tomada + modo performance; keep_alive ativo;
5 warmups descartados; cold start reportado à parte (§4.0).

### Amostra e narrativas (D7 decidido: opção b)

- Base tabular: `base_sintetica_risco.xlsx` — 20.202 episódios, target
  `nova_agressao` (10.217 pos / 9.983 neg ≈ 50/50), 14.591 agressores e
  14.592 vítimas com ids sintéticos estáveis.
- **Sem texto narrativo real** — narrativas geradas sinteticamente por
  `arquitetura_tese/dados/narrativas.py`, vinculadas por `id_agressor_sintetico` /
  `id_vitima_sintetica` (liga pessoa↔episódios → grafo de reincidência viável).
- **Limitação declarada (§6.6)**: Hit Rate@5 medido vale para o pipeline, não
  para texto real. Revalidar com dados reais antes de escala (R4).
- Ligação real pessoa↔processos via CNJ/DataJud não se aplica: amostra é
  sintética. Pseudonimização real será exigida na fase de dados reais.
- Features proibidas (vazamento, §4.5): `prob_geracao`, `score_geracao`,
  `perfil_risco_agressor` — artefatos do gerador sintético.

### Auditoria da base (scripts/analisar_base.py, 2026-10-05)

- 20.200 registros, **0 nulos**; alvo 50,6% positivo (artificial, §P07 — declarar).
- **Vazamento confirmado empiricamente**: `prob_geracao` (r=+0,484) e
  `score_geracao` (r=+0,409) são as maiores correlações com o alvo; o artefato
  categórico `perfil_risco_agressor` tem taxa_pos de 0,70 no nível "alto".
  Os três ficam **fora das features** (ver `tabular.py: FEATURES_PROIBIDAS`) —
  o teste de permutação do §4.5 deve confirmar que nenhum proxy similar domina.
- Features legítimas mais correlatas: `ameaca_morte` (+0,29),
  `n_episodios_anteriores` (+0,27), `descumpriu_medida` (+0,25),
  `acesso_arma`/`uso_alcool_drogas` (~+0,20), `controle_coercitivo` (+0,17).
- **Split obrigatório por grupo** `id_agressor_sintetico` na Fase 1: 3.579
  agressores (17,7%) têm ≥2 episódios; split aleatório vazaria pessoa entre
  treino/teste e inflaria AUC. `n_episodios_anteriores` é sequencial — usar só
  informação disponível naquele episódio.
- Grafo (D6): arestas existem (17,7% multi-episódio) mas esparsas; manter a
  regra da ablação.
- `local` é constante (Manaus) e `escolaridade_*` ~95% "Não Informado" —
  remover das features (variância ~zero).

### Corpus legal e especialista

- Seed em `arquitetura_tese/corpus.py`: Lei 11.340/2006 (arts. 5º, 7º, 12, 18, 19, 22,
  24-A, 38-A) + CP (121 §2º-A, 129 §9º, 138–140, 147, 147-A, 148, 150, 163,
  213, 215-A, 216-A) + LCP art. 21. Lista final a confirmar com o especialista.
- Especialista jurídico: [PENDENTE] — anota o gold set; ≥20% em dupla anotação
  com kappa de Cohen reportado (§6.1).

### Operating point e schema

- Operating point: **proposta recall ≥ 0,95 (FN ≤ 5%)** — erro assimétrico
  (§8); ratificar com o jurídico. Reportar junto ao ECE.
- Schema §5.1: **aprovado como v1** (`schemas.py`). Ressalvas: reservar chaves
  de auditoria em `Dados.metadados`; todo doc indexado carrega `artigos: list`
  (contrato do `checar_fundamentacao`).

## D1–D9

| ID | Decisão | Justificativa |
|----|---------|---------------|
| D1 | Fixar esta máquina como referência | 24 GB VRAM comporta Mistral 7B até FP16; medir sempre em AC/performance |
| D2 | Não fixar; benchmark (a)(b)(c) no dev | Base BERT sem STS é fraca; esperado: Legal-BERTimbau-STS ou BGE-M3 + BM25 |
| D3 | (b) probe linear sobre embeddings/features | TCAV exige gradientes de rede-alvo — inaplicável a LightGBM+LLM; probe gera AUC mensurável (§4.6). Declarar: é classificador de conceito, não TCAV |
| D4 | (b) Qualificador determinístico (§5.2) | Incerteza emitida por LLM não é calibrada (P06). Override estendido a MODERADO (§5.3): FN assimétrico |
| D5 | Medir o caminho síncrono; webhook à parte | SLA 8,5 s é síncrono; webhook testado em §4.7 |
| D6 | Incremental: FAISS+BM25 → Neo4j só se ablação justificar | §4.2 torna ablação obrigatória; grafo depende da ligação pessoa↔casos (garantida só nos ids sintéticos) |
| D7 | **(b) narrativas sintéticas vinculadas à base tabular** | Sem texto real no escopo do protótipo; limitação declarada no relatório |
| D8 | Limiares provisórios 0,25/0,50/0,75 | Base 50/50 invalida significado absoluto; recalibrar com dados reais. Separar bandas de exibição do operating point (recall alvo) |
| D9 | (b) LLM só campos textuais | −tokens (§4.1), −alucinação no eixo Dados por construção (§4.4), −falhas de schema (§4.3) |

## Fase 1 — resultado (2026-10-05, seed 42, split por grupo 80/20; re-treino com early stopping)

Modelo: LightGBM 4.7, **early stopping** (teto 2000, paciência 50) sobre
16.207 treino / 3.993 holdout. Validação interna de parada: 15% do treino
(2.452 episódios) com grupos disjuntos do fit — o holdout NÃO participa da
seleção do número de iterações. Parada na **iteração 54**.

| Métrica §4.5 | Valor | Critério |
|---|---|---|
| AUC (holdout) | **0,751** (era 0,744 com 300 árvores fixas) | reportado |
| Brier | 0,201 | reportado |
| ECE | **0,012** (era 0,021) | ≤ 0,05 ✅ |
| Artefatos no modelo | nenhum | teste de vazamento ✅ |

Top importância por permutação: `n_episodios_anteriores` (0,047),
`ameaca_morte` (0,037), `descumpriu_medida` (0,017), `uso_alcool_drogas`
(0,015), `separacao_recente` (0,011) — nenhuma dominância de proxy.

O diagnóstico da fig8 antecipava o resultado: o holdout estabilizava ~it. 50–150
e o modelo fixo de 300 árvores carregava ~150 árvores redundantes. O early
stopping sobre validação interna removeu a redundância (54 árvores), reduziu
o gap treino/validação e melhorou AUC (+0,007) e calibração (ECE quase metade).

Controle §4.5 (modelo COM artefatos): `score_geracao` domina a importância
(0,229 — ~5× o resto somado) + `prob_geracao` (0,036). Demonstra que o teste
de permutação flagra o vazamento quando presente.

API `POST /score` (`arquitetura_tese/api.py`): devolve probabilidade em 0-1;
entradas anômalas → 422 + log estruturado JSON (`entrada_anomala`).

Artefatos: `dados/modelo_tabular.txt`, `dados/modelo_tabular.meta.json`,
`dados/metricas_tabular.json`. **Fase 1: critério de saída §4.5 atendido.**

## Pendências antes de congelar a Seção 4

1. Instalar Ollama (registrar versão; confirmar sm_120) e validar GPU em Docker.
   ~~Resolvido na Fase 3.~~
2. `num_predict` calibrado para 1500 (soma dos max_length ≈ 1.200+ tokens PT);
   re-medir na Fase 3. ~~Resolvido na Fase 3.~~
3. Gold set: ~~gerar ≥100~~ gerado com 400 consultas (200 dev/200 test) a
   partir de 1.500 narrativas sintéticas — a expansão revelou que o 0,86
   original superestimava (ver resultado §4.2 acima); resta a validação do
   especialista (≥20% dupla anotação, kappa reportado); congelado com hash.
4. Expandir conjuntos §6.2 (≥50 pos + ≥100 neg) e §6.3 (≥50) — seeds em
   `conjuntos/` já versionados.

---

## Resultados da Fase 2 — Recuperação (§4.2)

Corpus legal: 22 dispositivos com texto oficial do Planalto (CP, Lei 11.340/2006,
Decreto-Lei 3.688/1941) em `conjuntos/corpus_legal.jsonl`. As narrativas formam
índice à parte (ramo "caso de apoio" da geração); o gold mede recuperação de
dispositivos, que é o ramo de fundamentação citável (§4.4).

Correções de desenho do gold set (descobertas no benchmark):
- Rótulos base (art. 5º/7º, presentes em TODA narrativa) removidos — não
  discriminavam nada.
- Auto-match mascarado: a narrativa-fonte da consulta é excluída do ranking.

Benchmark de encoders — Hit Rate@5 (gold ORIGINAL n=50/split):

| config | dev | test |
|---|---|---|
| BM25 | 0,70 | 0,74 |
| FAISS Legal-BERTimbau-base + mean pooling | 0,36 | — |
| FAISS Legal-BERTimbau-sts-base | 0,50 | — |
| **FAISS BGE-M3 (dim 1024, cosseno)** | **0,86** | **0,86** [IC95 0,74–0,93] |
| híbrido RRF BM25+BGE-M3 (k=60) | 0,78 | 0,82 |

**Gold set EXPANDIDO** (ação pendente executada — 1.500 narrativas, 400
consultas: 200 dev / 200 test; 200 com dispositivo penal). Mesma regra de
rótulo fraco, mesmo mascaramento de auto-match:

| config | dev | test |
|---|---|---|
| BM25 | 0,72 | 0,71 |
| FAISS Legal-BERTimbau-base | 0,38 | — |
| FAISS Legal-BERTimbau-sts | 0,46 | — |
| **FAISS BGE-M3** | **0,81** | **0,815** [IC95 0,755–0,863] |
| híbrido RRF | 0,76 | — |

Decisões efetivadas:
- **D2 → BGE-M3**: denso isolado vence o híbrido em ambos os tamanhos de gold
  (0,86 vs 0,78 em n=50; 0,81 vs 0,76 em n=200). O prior "jurídico
  especializado" dos Legal-BERTimbau não se confirmou no gold ampliado:
  base 0,38 e STS 0,46 no dev.
- **D6 → ramo único denso**: a fusão RRF prejudicou o resultado; pela cláusula
  de remoção do §4.2, o híbrido é rejeitado e o grafo fica fora do smoke.
- Critério Hit Rate@5 ≥ 0,85: **NÃO atendido no gold ampliado** — 0,815 no
  teste [IC95 0,755–0,863]. O 0,86 do n=50 era parcialmente efeito de amostra
  pequena, exatamente o que a expansão veio medir. Consequência declarada:
  o encoder comercial pré-treinado fica ~3,5 p.p. abaixo do limiar neste
  domínio sintético — justificativa técnica REAL para fine-tuning do encoder,
  que só deve ocorrer sobre rótulos validados por especialista em dados reais
  (em sintético, aprenderia os templates do gerador).

Limitações declaradas: rótulos fracos (regras feature→dispositivo) pendentes de
validação do especialista; corpus reduzido a 22 dispositivos de 3 diplomas;
encoder rodou em CPU (torch wheel CPU em py3.14) — latência de codificação de
consulta deve ser re-mediada na GPU na Fase 3.

Artefatos: `dados/metricas_recuperacao.json` (completo, com dim/device/tempo de
carga por encoder), `conjuntos/corpus_legal.jsonl`, `conjuntos/gold_set.jsonl`.

---

## Resultados da Fase 3 — Geração estruturada e latência (§4.1, §4.3, §4.4)

Infra: Ollama 0.35.1 nativo (Docker pendente para §4.7), mistral:7b Q4 100% GPU
(RTX 5090, ~8,9 GB VRAM, 120 tok/s medidos), BGE-M3 em CPU (encode ~0,5 s/consulta).

Pipeline por requisição: LightGBM (~7 ms) → evidências BGE-M3/FAISS (~0,5 s;
5 dispositivos + 2 casos similares) → Mistral com formato JSON Schema (LaudoLLM)
→ montar_laudo determinístico + checar_fundamentacao.

Medição N=200 (modelo quente, requisições sequenciais, keep_alive 30m):

| estágio | p50 | p95 | p99 | max |
|---|---|---|---|---|
| tabular | 7,1 ms | 7,7 ms | 13,3 ms | 41,8 ms |
| retrieval | 509 ms | 939 ms | 1.082 ms | 1.204 ms |
| llm | 4.387 ms | 5.744 ms | 7.268 ms | 7.815 ms |
| montagem | 0,1 ms | 0,2 ms | 0,2 ms | 0,2 ms |
| **total** | **4.911 ms** | **6.264 ms** | **8.347 ms** | **8.829 ms** |

Vereditos §4:
- §4.1 SLA 8,5 s: **ATENDIDO** — p95 6,26 s; até o p99 (8,35 s) ficou dentro.
- §4.3 schema 1ª tentativa: **ATENDIDO** — 200/200 (100%), JSON Schema no
  parâmetro `format` + regra de concisão no prompt (regra 7).
- §4.4 fundamentação: 95% dos laudos com todas as citações dentro dos
  recuperados; o guardião detecta as violações restantes. Diagnóstico do modo
  de falha: não é alucinação de fonte, é despejo do TEXTO do dispositivo no
  campo `artigo` — mitigado explicitando no prompt que artigo recebe só o
  identificador curto ("Art. 22"). Antes do ajuste: 64,5%.
  **Pendência executada**: política de re-tentativa implementada
  (`resiliencia.gerar_fundamentado`) — laudo com violação é rejeitado
  internamente e reenviado UMA vez com o bloco `[CORREÇÃO OBRIGATÓRIA]`
  contendo os erros do verificador; se persistir, o laudo sai com flag
  `fundamentacao_pendente:revisao_humana` (nunca aceito em silêncio).
  Efeito medido na re-medição N=200 (ver abaixo).

Calibrações feitas: num_ctx 4096 (prompt ~3,5 k tok), num_predict 1500,
saída real mediana ~500 tok; carga a frio do modelo ~12,4 s (fora do SLA —
keep_alive obrigatório). Docker Desktop estava parado; cenários de caos do
§4.7 ficam para a Fase 4 (Ollama em contêiner ou degradado nativo).

Artefatos: `dados/metricas_latencia.json`, `arquitetura_tese/evidencias.py`,
`scripts/medir_latencia.py` (por estágio + prévias §4.3/§4.4).
