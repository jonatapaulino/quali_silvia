# Roteiro de perguntas prováveis — banca de qualificação

Respostas curtas e honestas, todas ancoradas nos artefatos do repositório.

## Dados e validade

**"Você usou dados reais?"**
Não — e isso é declarado, não escondido. A base é 100% sintética
(`dados/base_sintetica_risco.xlsx`, 20.200 episódios) e as narrativas foram
geradas dos próprios registros (D7-b). O smoke test responde "a arquitetura
funciona de ponta a ponta?", não "o modelo é válido no mundo real?". A troca
de fonte não muda nenhum contrato — o mesmo pipeline recebe a base real.

**"Rótulos gerados pelo mesmo código que gera o texto não é circular?"**
É — e está declarado como rótulo fraco (§6.6). Por isso o gold set aguarda
validação do especialista (≥20% dupla anotação, kappa) e por isso o fine-tuning
de encoder foi adiado: treinar em sintético aprenderia os templates do
gerador. Métricas de retrieval/probe medem coerência do pipeline.

**"Por que a prevalência 50/50 é um problema?"**
Reincidência real é rara (dígitos baixos). Um classificador treinado em 50/50
superestima a probabilidade absoluta — por isso os limiares D8 são provisórios
e a calibração absoluta deve ser refeita com Platt/isotônica sobre dados
reais, junto com o ponto de operação de recall-alvo do §8.

## Modelo tabular

**"AUC 0,751 é bom?"**
Para ruído real e sem vazamento, sim. AUC muito alto seria suspeito de
vazamento — e temos o controle: incluindo `score_geracao` de propósito, ele
domina a importância (0,229) e o teste flagra. 0,75 com ECE 0,012 diz
"discrimina moderadamente e está bem calibrado".

**"Quantas épocas? O treino é saudável?"**
Boosting, não épocas: early stopping parou na iteração 54 (teto 2.000,
paciência 50) sobre validação interna por grupo — o holdout não participou da
escolha. Antes, com 300 árvores fixas, havia ~150 árvores redundantes
(gap +0,075 AUC). O early stopping subiu o AUC para 0,751 e quase dividiu o
ECE pela metade (fig8).

**"E quando o modelo erra?"**
Os dois erros são interpretáveis (seção 3.3 do PDF): o FP acumulou fatores
graves sem os dois mais fortes e a banda CRÍTICO disparou revisão humana —
comportamento seguro para falso positivo. O FN (controle coercitivo isolado)
mostra o limite do tabular e justifica o override de MODERADO divergente e o
recall-alvo §8. Em produção, o limiar não seria 0,50: o ponto de operação que
garante recall ≥0,95 no holdout é ~0,25 — lá o FN cai de 709 para 99 e
~90% dos casos vão à revisão humana (fig11). O FN do exemplo (score 0,319)
ficaria acima de 0,25 → seria capturado. A escolha do erro é institucional,
não acidental: o modelo ranqueia, a política decide, e fica auditável.

## Recuperação

**"O §4.2 falhou. E daí?"**
Foi o resultado mais útil do smoke test. Com n=50 parecia 0,86 (dentro); com
n=200 caiu para 0,815 — a expansão revelou efeito de amostra pequena, não
regressão. O denso isolado continua vencendo BM25 (0,71) e híbrido (0,775), e
o déficit de 3,5 p.p. transforma "queremos melhorar" em justificativa medida
para fine-tuning com rótulos reais.

**"Por que BGE-M3 e não um modelo jurídico (BERTimbau)?"**
A ablação decidiu: Legal-BERTimbau base = 0,38, STS = 0,46, BGE-M3 = 0,81 no
dev ampliado. O prior "especializado em jurídico" não se confirmou — STS foi
treinado para similaridade frase-a-frase, não para consulta-narrativa→
dispositivo.

## LLM e geração

**"O LLM pode inventar risco ou lei?"**
Não pode — por construção (D9-b): o Mistral só preenche campos textuais do
schema; score, nível, incerteza e revisão humana vêm de código determinístico.
Citações são verificadas contra os doc_id recuperados; violação → 1
re-tentativa com os erros no prompt → persistindo, sai com flag de revisão
humana, nunca aceito em silêncio (95%→97% com o retry).

**"E se o modelo cair no meio?"**
LaudoDegradado em <1,6 s com o score tabular preservado e revisão humana
forçada; circuit breaker abre após 3 falhas. Medido em caos real (porta
morta, soquete travado, kill na geração).

**"Injeção de prompt?"**
Detector na entrada pega 100% dos padrões §6.2 (recall=precisão=1,0). No teste
ponta a ponta, 12/12 laudos mantiveram schema válido sob injeção; houve 1 eco
de canário — por isso o bloqueio real mora na ingestão, antes do modelo.

## Sistema

**"Cabe no SLA?"**
p95 = 8,37 s < 8,5 s com 200 requisições sequenciais e modelo quente. O p99
(13,1 s) ficou fora por causa do retry de fundamentação — trade-off declarado
no relatório; mitigações: retry assíncrono (webhook D5) ou teto de tokens na
2ª geração. Carga a frio ~12,4 s exige warm-up no deploy.

**"O que falta para produção?"**
Dados reais (re-treino + recalibração + novos limiares), gold validado por
especialista, fine-tuning do encoder (déficit medido), concorrência e caos
com `docker pause` real, e o canal webhook instrumentado.
