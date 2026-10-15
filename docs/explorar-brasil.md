# Explorar o Brasil

**Data:** 15/10/2026. A jornada parte de uma pergunta e de um recorte territorial, com o resultado eleitoral disponível como contexto e filtro. Usa apenas snapshots publicados; não executa ingestões.

## Organização e navegação

Três temas organizam os indicadores disponíveis: Bolsa Família, Saúde e Voto. A região é escolhida por botões; o painel permite refinar por estado, resultado eleitoral, indicador, ordem e quantidade de cidades por página. Ao trocar de região, o estado é limpo para evitar recortes incompatíveis. A troca de filtros volta à primeira página, exceto quando a ação é paginar.

Todos os filtros ficam no endereço de `/explorar` e são interpretados pela mesma validação usada em `/api/explorar`. Recarregar, voltar e avançar preservam as escolhas. Links inválidos oferecem uma nova exploração. Estados fora da região selecionada e parâmetros inválidos são rejeitados.

A lista apresenta posição, cidade/UF, população com referência, valor do indicador, resultado eleitoral e seleção para comparar. Empates eleitorais são identificados, sem declarar um candidato vencedor. No celular, os elementos são reorganizados em linhas dentro de cada cidade, evitando tabela com rolagem lateral.

Selecionar até duas cidades exibe uma barra de comparação. A seleção permanece ao trocar filtros ou páginas, com os nomes visíveis e ações para removê-los. O botão abre `/comparar` com as duas cidades selecionadas. O nome de cada cidade abre sua página municipal.

## Indicadores publicados

| Tema / indicador | Fonte, período e regra |
|---|---|
| Bolsa Família — alcance | MDS, mês de referência do snapshot de pessoas, dividido pela população IBGE 2026. Pessoas em famílias beneficiárias, não titulares de pagamento. |
| Bolsa Família — total | CGU, intervalo publicado no snapshot de rankings. Exige observações em todos os meses desse intervalo; parcelas não equivalem a famílias únicas ou saque comprovado. |
| Bolsa Família — por habitante | Mesmo acumulado CGU, dividido pela população IBGE 2026 positiva e disponível. Não representa pagamento individual, benefício médio de uma família ou valor mensal. |
| Saúde — total | FNS, janeiro a julho de 2026, parcial. Somente dinheiro enviado ao destinatário municipal no recorte publicado. Recursos estaduais/distritais ou de outras instituições sediadas na cidade não são atribuídos ao município. |
| Saúde — por habitante | Mesmo recorte FNS, com o valor por habitante já publicado e população de referência 2026. Ausência de destinatário municipal mantém o indicador indisponível. |
| Saúde — mudança | Variação nominal publicada entre 2024 e 2025, com observações municipais disponíveis nos dois anos completos. Mantém sinais e zero; não compara o parcial de 2026 com um ano completo. |
| Voto — percentual do mais votado | TSE, primeiro turno presidencial de 2026, sobre a soma dos votos dos candidatos listados. Mantém a indicação de empate quando houver. |

O recorte geral inclui municípios independentemente de haver empate ou ausência eleitoral. Um filtro de candidato exige liderança única desse candidato. “Outros” exclui Lula e Flávio Bolsonaro e também exige liderança única. Empate e ausência eleitoral têm filtros próprios.

## Cobertura, ordenação e gráficos

Os três números de cobertura referem-se ao mesmo recorte territorial e eleitoral: cidades no recorte, com indicador comparável e sem dado comparável. Ausência não vira zero. Um recorte sem resultados oferece ampliação para o Brasil; falha de consulta oferece nova tentativa.

Valores maiores ou menores podem ser ordenados primeiro. Empates no indicador usam código IBGE como desempate estável. Páginas têm 10, 25 ou 50 cidades e não repetem registros. Páginas além do fim retornam a última página disponível.

Barras percentuais usam escala de 0 a 100%; valores monetários usam uma escala relativa comum aos registros da página. Variações usam sinal, seta, cor e número para distinguir aumento, redução e estabilidade. Posição no ranking não é avaliação de qualidade de vida, atendimento ou desempenho governamental. Valores monetários permanecem nominais.

## Dados e publicação

`/api/explorar` consulta `rankings_2026.json` como cadastro e contexto eleitoral, `pessoas_mds.json` para alcance ou `financiamento_saude.json` para saúde. Lê somente as fontes necessárias ao indicador; fontes independentes carregam em paralelo. Retorna apenas a página e os metadados do recorte, não os snapshots nacionais. As rotas anteriores de rankings e cobertura continuam disponíveis.

O período FNS desta versão é explicitamente janeiro–julho/2026. Uma futura mudança do recorte exige atualizar a regra e a apresentação conjuntamente; registros com datas incompatíveis não são classificados nesse ranking.

Testes verificam os valores contra os snapshots, filtros combinados, empates, paginação, seleção para comparação, períodos, dados ausentes, falhas e layout em computador e celular. Pesquisa de compreensão com cidadãos permanece como próxima etapa de UX.
