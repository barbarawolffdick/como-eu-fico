# Comparação entre cidades

**Data:** 15/10/2026. Primeira versão da jornada de comparação, orientada pelo [contrato editorial](contrato-editorial-dados-v1.md).

## Entrada e interação

`/comparar` começa com São Paulo e Rio de Janeiro como exemplo explícito, substituível por qualquer cidade do cadastro. A navegação principal e a entrada oferecem acesso; a página municipal abre a comparação com a cidade atual em A. Se A já for Rio de Janeiro, B inicia como São Paulo.

Buscas independentes permitem trocar A ou B sem sair da comparação, por mouse, teclado ou toque. A mesma cidade não pode ser selecionada nos dois lados. Há inversão dos lados, links para os detalhes municipais e botão para copiar o endereço. A URL preserva `a`, `b` (códigos IBGE) , `modo` (`habitante` ou `total`, para saúde) e `bolsa` (`pessoa`, `familia` ou `total`); voltar, avançar e recarregar mantêm as escolhas. Se copiar para a área de transferência não estiver disponível, a tela orienta copiar o endereço do navegador.

As cores identificam as cidades, não partidos, aprovação política ou qualidade dos serviços. As letras A/B e os nomes também permanecem visíveis. Em celular, os seletores ficam em uma coluna, enquanto cada indicador mantém seus dois valores lado a lado, sem exigir rolagem lateral.

## Medidas e comparabilidade

| Medida | Regra |
|---|---|
| Votação | Primeiro turno presidencial de 2026; distribuição sobre a soma dos votos dos candidatos listados em cada cidade. Liderança e empate são explícitos. Ausência eleitoral não é preenchida com resultados ou zeros. |
| Dinheiro federal para saúde | Último recorte publicado de transferências FNS fundo a fundo ao destinatário municipal. Comparação exige mesmo início, fim e condição de período completo/parcial. Valores estaduais/distritais ou de outras instituições sediadas na cidade ficam fora. |
| Vagas do Mais Médicos | Vagas ocupadas no provimento federal, não profissionais únicos, todos os médicos ou atendimentos. Só calcula diferença se a data de referência for a mesma. Mantém quantidade absoluta em ambos os modos. |
| Alcance do Bolsa Família | Percentual de moradores em famílias beneficiárias do MDS, com população IBGE 2026. Exige mesmo mês MDS. A diferença entre percentuais é apresentada em pontos percentuais. |
| Valores do Bolsa Família | CGU, último mês com observação em ambas as cidades. Não compara automaticamente o último mês de cada uma, nem soma meses incompletos como se fossem séries completas. Sem mês comum, o indicador permanece indisponível. Valores não comprovam saque. |

Na saúde, o modo inicial por habitante divide os valores monetários pela população IBGE positiva e com ano informado. Para calcular uma diferença por habitante, os anos de referência da população devem coincidir. Não cria pagamento individual, benefício médio por família ou equivalência de necessidades locais. População nula, zero ou sem referência impede essa divisão. Valores totais permanecem disponíveis sem exigir denominador populacional.

Diferenças e barras na mesma escala só aparecem com valores disponíveis nas duas cidades, fontes carregadas e condições de comparação atendidas. No alcance populacional, a escala da barra é fixa de 0 a 100%; nos demais indicadores, a mesma escala relativa é usada para as duas cidades. As diferenças são calculadas antes do arredondamento, com aviso visível. Em períodos diferentes, os valores e suas datas continuam visíveis individualmente, sem calcular diferença. Zero explícito é preservado; ausência e falha de consulta têm mensagens distintas.

## Dados e limites

Usa as APIs municipais de detalhe, saúde, cobertura e beneficiários, com os snapshots publicados e consulta agregada ao MDS quando falta histórico mensal local. Não reexecuta ingestões nacionais. Consultas independentes carregam em paralelo. A troca de cidade aborta consultas anteriores e não reutiliza seus valores na nova seleção. Uma falha em saúde ou cobertura permite tentar novamente sem perder as demais fontes.

Comparações são descritivas. Não classificam qual cidade é melhor, não comprovam atendimento a partir de dinheiro recebido e não inferem voto individual ou impacto da presidência. A comparação territorial exige contexto de população, necessidades e rede regional de serviços.

## Verificação

Testes em computador e celular conferem valores contra os snapshots, modo total/por habitante, buscas, duplicidade, inversão, histórico, links, último mês comum, pontos percentuais, períodos incompatíveis, zeros explícitos, ausências e recuperação de falha. Capturas verificam o layout; avaliação com cidadãos permanece como pesquisa futura de compreensão.


## Revisão de compreensão — 15/10/2026

A normalização por população passa a ser explicitamente um controle **dos recursos de saúde**. No Bolsa Família, o padrão é **por pessoa da família beneficiária**, com opções independentes **por família** e **total na cidade**. A URL preserva `bolsa=pessoa|familia|total`. Nenhuma dessas médias usa a população inteira. O denominador deve existir exatamente no último mês financeiro comum. O percentual de alcance continua usando todos os moradores como denominador, acompanhado de leitura “em cada 100 moradores” e contagens absolutas. Consulte [regras, fontes históricas e tratamento de lacunas](bolsa-familia-indicadores.md).
