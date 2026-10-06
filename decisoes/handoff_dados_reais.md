# Handoff — transição para dados reais (Arquitetura Tese)

> **Para o agente/executor futuro**: este documento é autossuficiente. Ele
> descreve o que existe, o que foi validado, o que muda quando os dados
> reais chegarem e a ordem correta de execução. Leia inteiro antes de agir.

## 0. O que é o sistema

Arquitetura neurossimbólica (decisão **D9-b**) de apoio à qualificação de
risco de reiteração de violência contra a mulher, desenvolvida como smoke
test sobre a base sintética `dados/base_sintetica_risco.xlsx` (20.200
episódios, alvo `nova_agressao`). Três ramos com responsabilidades
separadas:

| Ramo | Componente | Papel |
|---|---|---|
| Tabular | LightGBM (`arquitetura_tese/tabular.py`) | Score 0–1 + banda D8 — **determinístico, é quem decide o risco** |
| Recuperação | BGE-M3 denso (`recuperacao.py`, `evidencias.py`) | Traz dispositivos legais/narrativas para fundamentação |
| Geração | Mistral-7B via Ollama (`llm.py`, `prompts.py`) | **Só escreve texto** (laudo Toulmin §5.7) — nunca decide |

Guardiões determinísticos envolvem o LLM: verificação de citações
(`verificar_fundamentacao`), detector de injeção (`guardiao.py`),
circuit breaker + `LaudoDegradado` (`resiliencia.py`), probes CAV.

Repositório: `https://github.com/jonatapaulino/quali_silvia` — pasta local
`D:/experimento_silvia/judicata`. 65 testes (`pytest -q`).

## 1. Estado validado no smoke test (base sintética)

- AUC holdout 0,751 · ECE 0,012 · early stopping it. 54
- Hit Rate@5 BGE-M3 **0,815** (n=200 teste) — **abaixo do critério 0,85**;
  déficit real medido, não cosmético
- Fundamentação 97% (retry-on-violation ativo) · schema 100%
- Latência p50 5,1s · p95 8,37s · p99 13,1s
- Caos nativo degradado corretamente; injeção recall/precisão 1,0 (seed)
- 8 de 9 critérios §4 atendidos — ver `decisoes/relatorio_smoke.md`

## 2. O que NÃO muda com dados reais

Contratos e guardiões são agnósticos à fonte: `iterar_episodios`,
schemas §5.1, regras §5.2–5.3, `gerar_laudo`, `verificar_fundamentacao`,
breaker, harness de métricas, testes. A troca da base é uma **re-treino +
revalidação**, não um re-projeto.

## 3. Checklist de execução com dados reais

**Passo 0 — governança primeiro.** Confirmar acordo/base legal (CNJ/TJAM),
anonimização, e termo de uso antes de qualquer processamento. LGPD: dados
de violência doméstica são sensíveis (art. 11) — minimização e controle de
acesso desde o primeiro read.

**Passo 1 — adaptação do ingest.** Escrever `iterar_episodios`-equivalente
para a base real produzindo os mesmos campos de `schemas.py` (ou estender o
schema com campos novos). Manter `grupo_split` por agressor — **nunca**
split aleatório por episódio (vazamento por repetição de agressor).

**Passo 2 — re-treino tabular.** `treinar()` com early stopping sobre
validação interna por grupo; depois **recalibrar** (Platt/isotônica) —
prevalência real de reincidência é muito menor que os 50/50 sintéticos e
invalida os scores brutos. Re-derivar os limiares D8 (0,25/0,50/0,75 eram
provisórios) e o ponto de operação §8 (maior limiar com recall ≥0,95).
**Não transportar** o limiar 0,25 sintético.

**Passo 3 — gold set real.** Reanotar consultas com especialista;
medir kappa em ≥20% de dupla anotação. Rótulos de template não servem
como ground truth real.

**Passo 4 — fine-tuning do encoder (justificativa já medida).** Faltam
3,5 p.p. no §4.2. Treino contrastivo BGE-M3 em pares (consulta→dispositivo)
do gold **validado**. Hardware: RTX 5090 exige env separado Python
≤3.13 + torch cu128 (o env principal é CPU-only — ver §ambiente do
relatorio_smoke).

**Passo 5 — LoRA do Mistral (opcional, só estilo).** Só se a redação dos
laudos sobre prosa jurídica real precisar de ajuste. Não melhora métricas
preditivas — o LLM não decide.

**Passo 6 — revalidação completa.** Re-rodar §4.1–§4.7 na base real e
república a tabela de vereditos honestamente — incluindo o que falhar.

## 4. Pendências já conhecidas (herdar, não esquecer)

1. Validação do especialista: dupla anotação ≥20% + kappa (sem isso, todo
   número de retrieval tem asterisco).
2. §4.7 com `docker pause` real (executamos equivalentes nativos:
   porta morta, socket travado, taskkill — comportamento provado, fidelidade
   ao método prescrito pendente).
3. Defesa de injeção avaliada só no seed próprio — precisa de conjunto
   adversarial externo.
4. Fine-tuning adiado **de propósito**: treinar sobre dados sintéticos
   ensina padrões do gerador, não do mundo (declarado em §6.6).

## 5. Armadilhas — o que não fazer

- **Não** reportar métricas sintéticas como evidência de validade real.
- **Não** reutilizar limiares/bandas do sintético na base real.
- **Não** treinar encoder/LLM antes do gold validado por especialista.
- **Não** deixar o LLM influenciar o score (D9-b) — ele só fundamenta.
- **Não** remover guardiões "porque o modelo novo é melhor" — verificação
  de citação e revisão humana são invariantes, não contingentes.
- **Não** versionar dados reais no Git público — `dados/` da base real fica
  fora do repo (adicionar ao `.gitignore` antes do primeiro ingest).

## 6. Comandos de referência

```bash
pip install -r requirements.txt && python -m pytest -q
python scripts/gerar_graficos.py              # fig1-4 (ROC, HR@5, latência, guardiões)
python scripts/gerar_material_quali.py        # fig5-11 (calibração, bandas, arquitetura, treino, confusão, ponto de operação)
python scripts/medir_latencia.py --n 200      # §4.1 + §4.4 (exige Ollama + mistral:7b)
python scripts/avaliar_recuperacao.py         # §4.2 (BGE-M3 CPU ~min)
python scripts/gerar_pdf_metodologia.py       # regenera decisoes/metodologia_smoke_test.pdf
python scripts/md_para_docx.py in.md out.docx # conversão p/ Word
```

Métricas consolidadas em `dados/metricas_*.json`; figuras em
`dados/figuras/`; exemplos executados em `dados/exemplos/`.
