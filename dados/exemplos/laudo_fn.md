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
