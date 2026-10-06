# Exemplos de classificação e de laudo — Arquitetura Tese

Matriz de confusão no holdout (n=3993, limiar 0,50): TP=1294, FP=524, TN=1463, FN=712 → acurácia 69.0%, recall 64.5%, precisão 71.2% (prevalência artificial ~50%).

### Caso TP — episódio EP013595

- score previsto: **0.901** → classe predita reincidência (limiar 0,50) — real: reincidência
- banda D8: **critico**

| feature | valor |
|---|---|
| n_episodios_anteriores | 1 |
| ameaca_morte | 1 |
| acesso_arma | 1 |
| uso_alcool_drogas | 1 |
| separacao_recente | 1 |
| descumpriu_medida | 1 |
| filhos_comum | 1 |
| desemprego_agressor | 0 |
| controle_coercitivo | 1 |
| classe | Inquérito Policial |
| situacao_processo | Suspenso |

### Caso FP — episódio EP013146

- score previsto: **0.841** → classe predita reincidência (limiar 0,50) — real: sem reincidência
- banda D8: **critico**

| feature | valor |
|---|---|
| n_episodios_anteriores | 2.0 |
| ameaca_morte | 0 |
| acesso_arma | 0 |
| uso_alcool_drogas | 1 |
| separacao_recente | 1 |
| descumpriu_medida | 1 |
| filhos_comum | 1 |
| desemprego_agressor | 0 |
| controle_coercitivo | 1 |
| classe | Inquérito Policial |
| situacao_processo | Suspenso |

### Caso FN — episódio EP017662

- score previsto: **0.311** → classe predita sem reincidência (limiar 0,50) — real: reincidência
- banda D8: **moderado**

| feature | valor |
|---|---|
| n_episodios_anteriores | 0 |
| ameaca_morte | 0 |
| acesso_arma | 0 |
| uso_alcool_drogas | 0 |
| separacao_recente | 0 |
| descumpriu_medida | 0 |
| filhos_comum | 1 |
| desemprego_agressor | 0 |
| controle_coercitivo | 1 |
| classe | Ação Penal - Procedimento Sumário |
| situacao_processo | Suspenso |

### Caso TN — episódio EP002641

- score previsto: **0.219** → classe predita sem reincidência (limiar 0,50) — real: sem reincidência
- banda D8: **baixo**

| feature | valor |
|---|---|
| n_episodios_anteriores | 0 |
| ameaca_morte | 0 |
| acesso_arma | 0 |
| uso_alcool_drogas | 0 |
| separacao_recente | 0 |
| descumpriu_medida | 0 |
| filhos_comum | 0 |
| desemprego_agressor | 0 |
| controle_coercitivo | 0 |
| classe | Auto de Prisão em Flagrante |
| situacao_processo | Suspenso |

## Exemplo ponta a ponta — TP (EP013595)

**Entrada (features do episódio):** 1 episódios
anteriores; ameaça de morte=1; arma=1;
separação recente=1; descumprimento de
medida=1; controle coercitivo=1;
classe=Inquérito Policial; situação=Suspenso

**Narrativa associada (sintética, D7-b):**

> TERMO DE DEPOIMENTO — A declarante VÍTIMA_97DB69, 35 anos, narra episódio ocorrido em Manaus, atribuído ao requerido AGRESSOR_01EE4A, 45 anos. Há registro de descumprimento de medida protetiva: o requerido enviou mensagens intimidadoras à vítima mesmo após a proibição judicial de contato. Constam ameaças de morte direcionadas à vítima e, por extensão, aos familiares que a abrigam. Há indício de acesso a arma de fogo pelo requerido, fator que agrava o risco de escalada. Consta uso habitual de álcool e/ou entorpecentes pelo agressor no contexto dos episódios. A vítima comunicou o fim do relacion…

**Estágio 1 — LightGBM:** score = **0.901** → banda **critico**
(decisão determinística, não do LLM) · revisão humana = True

**Estágio 2 — Evidências recuperadas (BGE-M3/FAISS, top-5 dispositivos + 2 casos):**
  - lei11340_art24a — “Lei 11.340/2006 — Art. 24-A”
  - lei11340_art12 — “Lei 11.340/2006 — Art. 12”
  - lei11340_art22 — “Lei 11.340/2006 — Art. 22”
  - lei11340_art18 — “Lei 11.340/2006 — Art. 18”
  - cp_art147 — “Código Penal — Art. 147”
  - lei11340_art19 — “Lei 11.340/2006 — Art. 19”
  - narr_EP004136 — “Episódio EP004136 — Inquérito Policial”

**Estágio 3 — Laudo Toulmin gerado pelo Mistral 7B** (tentativas: 1):
- *Alegação:* O agressor descumpriu medida protetiva de urgência, conforme Art. 24-A da Lei 11.340/2006, e ameaçou a vítima, conforme Art. 147 do Código Penal.
- *Raciocínio da garantia:* O agressor descumpriu uma medida protetiva de urgência, conforme Art. 24-A da Lei 11.340/2006, que proíbe o contato com a vítima. Além disso, o agressor ameaçou a vítima, conforme Art. 147 do Código Penal, que criminaliza a ameaça de causar mal injusto e grave a alguém.
- *Dispositivos citados:*
  - lei11340_art24a (Lei 11.340/2006, Art. 24-A)
  - cp_art147 (Código Penal, Art. 147)
- *Casos de apoio:*
  (nenhum)
- *Refutação:* Nenhum atenuante ou falha identificado nos dados fornecidos.

**Estágio 4 — Verificação determinística:** citações íntegras
· flags de refutação: nenhuma
· incerteza: alta (cálculo padrão §5.2)

## Exemplo ponta a ponta — FN (EP017662)

**Entrada (features do episódio):** 0 episódios
anteriores; ameaça de morte=0; arma=0;
separação recente=0; descumprimento de
medida=0; controle coercitivo=1;
classe=Ação Penal - Procedimento Sumário; situação=Suspenso

**Narrativa associada (sintética, D7-b):**

> TERMO DE DEPOIMENTO — A declarante VÍTIMA_B2FBEA, 35 anos, narra episódio ocorrido em Manaus, atribuído ao requerido AGRESSOR_B809B0, 47 anos. A vítima relata controle financeiro e impedimento de trabalhar fora, em dinâmica de subordinação prolongada. Registra-se a existência de filhos comuns, usados pelo requerido como pretexto de aproximação. Encerra-se o registro com orientação sobre medidas protetivas e encaminhamento à rede de apoio.

**Estágio 1 — LightGBM:** score = **0.319** → banda **moderado**
(decisão determinística, não do LLM) · revisão humana = False

**Estágio 2 — Evidências recuperadas (BGE-M3/FAISS, top-5 dispositivos + 2 casos):**
  - lei11340_art12 — “Lei 11.340/2006 — Art. 12”
  - cp_art129_9 — “Código Penal — Art. 129, § 9º”
  - cp_art216a — “Código Penal — Art. 216-A”
  - cp_art150 — “Código Penal — Art. 150”
  - cp_art147a — “Código Penal — Art. 147-A”
  - cp_art147 — “Código Penal — Art. 147”
  - narr_EP003177 — “Episódio EP003177 — Ação Penal - Procedimento Ordinário”

**Estágio 3 — Laudo Toulmin gerado pelo Mistral 7B** (tentativas: 1):
- *Alegação:* A acusação é de violência doméstica contra a mulher, conforme a Lei 11.340/2006, Art. 12, e lesão corporal doméstica contra a mulher, conforme o Código Penal, Art. 129, § 9º.
- *Raciocínio da garantia:* A acusação é baseada no registro da ocorrência e na declaração da vítima, conforme o procedimento em inquérito policial, como previsto na Lei 11.340/2006, Art. 12. A lesão corporal doméstica contra a mulher é considerada crime, conforme o Código Penal, Art. 129, § 9º, quando resulta em incapacidade para as ocupações habituais, perigo de vida, debilidade permanente de membro, sentido ou função, aceleração de parto, incapacidade permanente para o trabalho, enfermidade incuravel, perda ou inutilização do membro, sentido ou função, deformidade permanente ou aborto. Neste caso, a vítima relata cont
- *Dispositivos citados:*
  - lei11340_art12 (Lei 11.340/2006, Art. 12)
  - cp_art129_9 (Código Penal, Art. 129, § 9º)
- *Casos de apoio:*
  (nenhum)
- *Refutação:* Nenhum atenuante ou falha identificado nos dados fornecidos.

**Estágio 4 — Verificação determinística:** citações íntegras
· flags de refutação: nenhuma
· incerteza: alta (cálculo padrão §5.2)
