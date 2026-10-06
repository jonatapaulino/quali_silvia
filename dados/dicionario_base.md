# Dicionário — base_sintetica_risco.xlsx (20.200 episódios)

| coluna | papel | descrição | r(y) |
|---|---|---|---|
| `id_episodio` | id | identificador único do episódio (sintético) | — |
| `id_agressor_sintetico` | id | hash estável do requerido — liga episódios da mesma pessoa | — |
| `id_vitima_sintetica` | id | hash estável da vítima | — |
| `n_episodios_anteriores` | feature | nº de episódios anteriores do mesmo agressor | +0.268 |
| `perfil_risco_agressor` | artefato | ARTEFATO da geração sintética — rótulo gerador (banido) | — |
| `idade_requerido` | feature | idade do requerido | +0.009 |
| `idade_vitima` | feature | idade da vítima | +0.013 |
| `escolaridade_requerido` | descartada | escolaridade do requerido (~95% 'Não Informado') | — |
| `escolaridade_vitima` | descartada | escolaridade da vítima (~95% 'Não Informado') | — |
| `sexo_requerido` | feature | sexo do requerido (95% M) | — |
| `sexo_vitima` | feature | sexo da vítima (92% F) | — |
| `local` | descartada | município — constante 'Manaus' nesta base | — |
| `classe` | feature | classe processual (IP, MPU, Ação Penal…) | — |
| `situacao_processo` | feature | situação atual do processo | — |
| `ameaca_morte` | feature | agressor ameaçou de morte (0/1) | +0.286 |
| `acesso_arma` | feature | acesso a arma de fogo (0/1) | +0.196 |
| `uso_alcool_drogas` | feature | uso de álcool/drogas no episódio (0/1) | +0.197 |
| `separacao_recente` | feature | separação do casal nas últimas semanas (0/1) | +0.158 |
| `descumpriu_medida` | feature | descumpriu medida protetiva vigente (0/1) | +0.253 |
| `filhos_comum` | feature | filhos em comum com a vítima (0/1) | +0.061 |
| `desemprego_agressor` | feature | requerido desempregado (0/1) | +0.125 |
| `controle_coercitivo` | feature | controle coercitivo/vigilância (0/1) | +0.173 |
| `nova_agressao` | alvo | ALVO: houve nova agressão posterior (0/1) | +1.000 |
| `prob_geracao` | artefato | ARTEFATO da geração sintética — vazamento (banido) | +0.484 |
| `score_geracao` | artefato | ARTEFATO da geração sintética — vazamento (banido) | — |

## Amostra (5 episódios, colunas principais)

```
id_episodio  n_episodios_anteriores                              classe  ameaca_morte  acesso_arma  descumpriu_medida  controle_coercitivo  nova_agressao
   EP000001                     0.0                  Inquérito Policial           0.0          0.0                0.0                  0.0            1.0
   EP000002                     1.0   Ação Penal - Procedimento Sumário           0.0          0.0                0.0                  0.0            1.0
   EP000003                     0.0 Ação Penal - Procedimento Ordinário           0.0          0.0                0.0                  0.0            1.0
   EP000004                     0.0 Ação Penal - Procedimento Ordinário           0.0          0.0                0.0                  0.0            1.0
   EP000005                     1.0                  Inquérito Policial           1.0          0.0                0.0                  1.0            1.0
```

## Narrativa sintética renderizada (exemplo)

```
TERMO DE DEPOIMENTO — A declarante VÍTIMA_DB2F17, 45 anos, narra episódio ocorrido em Manaus, atribuído ao requerido AGRESSOR_4CCF9A, 38 anos. Consta que o requerido descumpriu medida protetiva de urgência vigente, aproximando-se da residência da vítima, nos termos do art. 24-A da Lei 11.340/2006. Constam ameaças de morte direcionadas à vítima e, por extensão, aos familiares que a abrigam. O fato ocorreu enquanto o agressor apresentava visíveis sinais de embriaguez. Consta vigilância constante sobre a vítima, com exigência de prestação de contas de rotina e de amizades. Registra-se reiteração: 2 fatos anteriores já documentados contra o mesmo agressor. Diante do exposto, lavrou-se o presente termo e a vítima foi orientada quanto aos direitos previstos na Lei 11.340/2006.
```