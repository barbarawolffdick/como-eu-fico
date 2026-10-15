# Arquitetura de informação e página da cidade

**Data:** 15/10/2026. Primeira implementação dos pontos 2 e 3 do revamp de UX/UI, orientada pela [promessa e jornadas do produto](contrato-editorial-dados-v1.md#1-objetivo-editorial).

## Entrada e navegação

A navegação principal é compartilhada e aparece no topo: Minha cidade, Explorar o Brasil, Comparar cidades, Análises e Sobre os dados. A seção corrente é identificada visualmente e para tecnologias assistivas.

A página inicial apresenta a promessa, a busca e uma descoberta regional para convidar à investigação. Logo abaixo, um ranking e caminhos para análises e fontes apresentam o potencial das páginas internas.

- **Variação regional:** compara as somas de famílias beneficiárias nos dois períodos publicados pelo MDS. Cada região inclui somente municípios com observações nas duas pontas; a interface informa a cobertura quando incompleta. A variação é calculada sobre as somas, não pela média de percentuais municipais. O gráfico representa a magnitude, com sinal explícito para aumento ou redução. Não presume uma série contínua entre as duas observações.
- **Ranking de alcance:** mostra os cinco maiores percentuais de moradores em famílias beneficiárias entre municípios com dados de pessoas e cobertura disponíveis. Usa os percentuais publicados MDS/IBGE, sem filtro eleitoral. Não classifica o desempenho da gestão nem mede titulares de pagamentos. Empates são ordenados por código IBGE.
- As duas descobertas usam períodos e unidades próprios, visíveis. Falhas de leitura não produzem valores fictícios.

## Página municipal

Cada cidade tem endereço próprio em `/cidade/{codigo_ibge}`. Os endereços anteriores `/?municipio={codigo_ibge}` continuam acessíveis por redirecionamento. Links de rankings, análises e fontes usam o novo endereço. A troca de cidade mantém o histórico de navegação, permitindo voltar à cidade anterior.

Ordem do conteúdo e do menu local:

1. **Identificação:** nome, UF, população, referência IBGE e busca para trocar de cidade.
2. **Panorama:** placar eleitoral, recursos federais transferidos ao fundo municipal de saúde e alcance populacional do Bolsa Família. Cada cartão declara seu período, fonte e significado e oferece acesso ao detalhe.
3. **Saúde:** financiamento, evolução de anos completos, despesas, estrutura, equipes e vagas do provimento federal, com os recortes já publicados.
4. **Bolsa Família:** alcance populacional MDS e valores/parcelas CGU, preservando conceitos e datas independentes.
5. **Eleição 2026:** distribuição dos votos dos candidatos listados, totais, turno e limites de interpretação.
6. **Fontes:** resumo das origens e acesso à metodologia completa.

O placar municipal apresenta o candidato mais votado, seu percentual e a margem sobre o segundo quando não há empate. Em empate, informa a situação sem escolher vencedor. O denominador é a soma dos votos dos candidatos listados. Indisponibilidade eleitoral não é substituída por resultado presumido.

## Comportamentos e acessibilidade

- Em telas menores, o conteúdo passa a uma coluna e o menu de temas permite rolagem horizontal.
- O menu local permanece acessível durante a rolagem e identifica a seção em leitura. Os destinos têm espaçamento para não ficarem encobertos pelo menu.
- A busca oferece resultados com cidade e UF, estados de carregamento, erro e nenhum resultado, navegação por setas, seleção com Enter e fechamento com Escape.
- A navegação inclui atalho para pular ao conteúdo, foco visível e respeito à preferência de movimento reduzido.
- Detalhe municipal, cobertura e saúde carregam em paralelo; falhas de consulta oferecem nova tentativa sem converter ausência em zero. Panorama e detalhe de saúde compartilham a mesma resposta.

## Escopo desta versão

Esta versão reorganiza a experiência usando os dados publicados e inclui [comparação direta entre duas cidades](comparacao-cidades.md). Novas áreas como educação e evidências de percepção de valor continuam como evoluções futuras, dependentes de dados e método. Não há novas ingestões ou inferências causais nesta alteração.

A validação técnica cobre navegação e dados em computador e celular. A validação da compreensão com cidadãos permanece como próxima etapa de pesquisa de UX.
