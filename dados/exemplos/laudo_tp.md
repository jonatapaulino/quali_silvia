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
