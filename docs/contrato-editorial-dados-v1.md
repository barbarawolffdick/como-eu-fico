# Como Eu Fico — contrato editorial e de dados v1.0

**Estado:** proposta versionada para revisão, não autorização automática para novas ingestões.  
**Data:** 2026-10-12  
**Unidade central:** município brasileiro identificado por `codigo_ibge` (texto, sete dígitos).  
**Referência eleitoral:** primeiro turno presidencial de 2026, fixo para as análises iniciais.

## 1. Objetivo editorial

Tornar observável, por município, como políticas, serviços, investimentos, transferências e benefícios com participação federal estão presentes na vida cotidiana e como sua trajetória temporal se relaciona descritivamente com os resultados eleitorais de 2026.

O projeto procura responder, para um cidadão: **“O que o governo federal tem a ver com a minha vida e com a minha cidade?”**

Não restringir a presença federal a fluxos financeiros. Além de valores, considerar entregas, alcance, acesso e resultados observáveis quando a fonte os medir. Não presumir impacto a partir apenas de despesa, repasse ou anúncio.

### Dimensões editoriais (não são tabelas de banco)

- Saúde: atendimento, medicamentos, imunização e financiamento verificável.
- Educação: alimentação, transporte, bolsas, serviços e financiamento verificável.
- Renda e proteção: programas de transferência, previdência e proteção social.
- Moradia e infraestrutura: habitação, saneamento, mobilidade, obras e entregas.
- Cidade e serviços: programas e apoio federal a serviços locais.

Cada medida deverá permitir rastrear a fonte, o que representa concretamente e o grau de atribuição federal. Categorias são de navegação editorial e podem consultar múltiplos domínios.

## 2. Contrato territorial

- `codigo_ibge`: chave externa comum, string de sete dígitos; nunca converter em identificador numérico para junção.
- `codigo_tse`: chave própria do TSE; relação por tabela oficial de correspondência TSE–IBGE.
- Cadastro e versão territorial devem ser preservados; mudanças de nome, desmembramentos e reorganizações exigem tabela de correspondência histórica explícita.
- Brasília/DF e demais particularidades territoriais devem seguir o conjunto oficial declarado para cada extração, nunca regras presumidas.
- Uma série só pode ser comparada se a cobertura territorial for definida. Ausência não significa zero.

## 3. Contrato temporal

- **Unidade analítica padrão:** mês de referência, `AAAA-MM`.
- **Janela inicial da investigação:** janeiro de 2023 a setembro de 2026, com extensão histórica quando houver informação oficial comparável.
- **Eleição:** evento fixo de 2026; não repetir resultados eleitorais como se fossem fatos mensais.
- Cada observação registra `periodo_referencia_inicio`, `periodo_referencia_fim`, `tipo_periodo` (competência, pagamento, execução, exercício, medição), `data_publicacao` quando disponível e `data_extracao`.
- Dado anual ou pontual mantém sua frequência original; proibido distribuir valores anuais pelos meses ou interpolar sem método e rótulo explícitos.
- Séries anteriores à eleição e informações conhecidas apenas depois dela são tratadas separadamente. Uma data de competência pré-eleitoral não prova que a informação estivesse publicamente disponível naquela data.
- Variação monetária temporal exige distinguir valores nominais de valores deflacionados; índice, base, período e fórmula devem constar do indicador.
- O calendário de atualização é próprio de cada fonte, não imposto por uma execução mensal global.

## 4. Domínios independentes e contratos de registros

Cada domínio mantém armazenamento, ingestão, proveniência e validação separados. SQLite é uma implementação possível, não um compromisso de unir domínios em um banco único.

| Domínio | Unidade primária esperada | Identificação |
|---|---|---|
| `eleitoral` | Eleição, turno, cargo, município, candidato | Chaves eleitorais + `codigo_ibge` via correspondência |
| `beneficios` | Programa, município, mês e tipo de medida | Fonte + programa + município + período + medida |
| `financas` | Ente recebedor, classificação contábil, período e estágio | Fonte + ente + período + classificação + estágio |
| `territorio` | Município, indicador e período de referência | Fonte + indicador + município + período |
| `entregas_servicos` | Programa, entrega ou serviço, local e período | Identificador próprio e regras territoriais comprovadas |

Os esquemas acima são **contratos conceituais**, não nomes de tabelas já existentes.

### Campos obrigatórios para medidas observáveis

`fonte_id`, `dataset_id`, `versao_fonte` (ou hash), `data_extracao`, `codigo_ibge` quando identificável, `periodo_referencia`, `unidade_medida`, `definicao_medida`, `metodo_agregacao`, `status_qualidade`.

Quando um campo for inaplicável, marcar explicitamente como inaplicável; quando ausente, reportar ausência e impacto. Não substituir ausentes por zero.

## 5. Separação entre fenômenos

Valores pagos diretamente a pessoas, transferências intergovernamentais, financiamento de serviços, execução de obras e despesas de órgãos federais são observações distintas. Não somá-las como “total de investimento federal no município” sem identificar sobreposições e justificar o escopo.

A participação federal pode ser **direta**, **compartilhada** ou **estrutural**, sempre com explicação específica do mecanismo documentado.

Os termos `investimento`, `transferência`, `gasto`, `benefício`, `cobertura`, `entrega` e `impacto` não são sinônimos.

## 6. Camada analítica: relacionar sem misturar

- As bases são independentes; relações ficam em código ou em consultas analíticas reproduzíveis.
- Os `JOINs` devem declarar chaves e granularidade. Um registro candidato×município nunca pode ser unido diretamente a vários meses sem agregação ou tratamento explícito.
- Antes e depois de cada relacionamento, testar unicidade da chave esperada, cardinalidade, cobertura e conservação de totais nas medidas aditivas.
- Nenhuma consulta derivada altera o arquivo original ou os snapshots de uma fonte.
- Variáveis municipais descrevem agregados territoriais. Não permitem inferir comportamento individual dos eleitores (falácia ecológica).
- Correlação entre trajetória de uma política e votação de 2026 não comprova influência causal. Hipóteses explicativas exigem método e evidências adicionais.

## 7. Níveis de evidência para a experiência do cidadão

- **Financiamento:** valor empenhado, transferido ou pago, exatamente como classificado na fonte; por si só não comprova serviço entregue.
- **Alcance:** pessoas, famílias, unidades ou estabelecimentos atendidos, conforme definição oficial.
- **Entrega:** bem, obra, atendimento ou serviço efetivamente realizado e verificável.
- **Resultado:** mudança observada em indicador definido e com metodologia conhecida.
- **Impacto causal:** somente quando houver desenho empírico que sustente atribuição; não inferir de séries descritivas.

O produto deve distinguir visualmente esses níveis sem atribuir uma entrega exclusivamente à União quando houver execução compartilhada.

## 8. Qualidade e publicação

Estados: `RAW`, `VALIDATED`, `PARTIAL`, `BLOCKED`, `PUBLISHED`. O estado pertence a uma **medida, granularidade e período**, não automaticamente à fonte toda.

Verificações:
1. **Estruturais:** tipos, chaves, duplicatas, cobertura territorial/temporal, integridade dos arquivos.
2. **Semânticas:** unidade, conceito, etapa de pagamento, definição de beneficiário, competência, atribuição e categorias especiais.
3. **Analíticas:** cardinalidade de junções, preservação de totais, denominadores, períodos de comparação, limites interpretativos.

Cada resultado publicável aponta para: arquivo bruto e hash, versão do código, transformação, consulta, período, universo, indicador e limitações.

## 9. Estado atual e decisões de escopo

- A base TSE presidencial 2026 foi reconstruída para 5.571 identificadores municipais e conciliada com a correspondência TSE–IBGE. A execução local relatou `PASS` na consistência eleitoral municipal.
- A identificação de locais de votação teve 6.588 divergências e permanece **pendente**. Não liberar agregações por local como se estivessem certificadas.
- A base eleitoral secundária antiga não faz parte do pipeline.
- O trabalho experimental de população no PR #6 **não define o contrato territorial** nem deve ser mesclado sem revisão após aprovação deste documento.
- Esta etapa não executa ingestões, não move arquivos, não cria indicadores que ainda não tenham fonte/definição verificadas.

## 10. Critério de conclusão desta etapa

Este contrato e o catálogo inicial de fontes são revisados editorialmente; questões em aberto são registradas. Só então desenhar esquemas físicos, testes e ingestões por domínio.

Questões pendentes para etapa 2: janela histórica para fontes que não têm 2023–2026 completo; política de revisões retroativas; nomenclatura e contagem de famílias beneficiárias; condições de inferência de alcance/entrega; regra editorial para casos de município sem evidências suficientes.

## Referências oficiais verificadas em 2026-10-12

- TSE, Resultados 2026: https://dadosabertos.tse.jus.br/dataset/resultados-2026
- IBGE, Códigos dos municípios: https://www.ibge.gov.br/explica/codigos-dos-municipios.php
- CGU, documentação de dados do Portal da Transparência: https://api.portaldatransparencia.gov.br/swagger-ui/index.html

## Adendo aprovado em conversa — 15/10/2026

- **A cidade é o centro de todo o produto.** Cada indicador deve chegar à página municipal. Estado, região de saúde, estabelecimento regional e país podem fornecer contexto, sem substituir esse ponto de entrada.
- Uma relação regional deve declarar município de localização, município de residência/atendimento e ente recebedor quando a fonte permitir. A sede de um fundo estadual não autoriza atribuir seu orçamento aos moradores da cidade.
- Todo indicador publicado deve mostrar na interface, inclusive em nota de rodapé, a data ou o intervalo efetivamente coberto, a fonte e sua unidade. Parcela de financiamento, competência CNES, pagamento e extração são datas distintas.
- Médias, projeções e cruzamentos estão autorizados como evolução futura, quando houver base suficiente e método validado. Devem permanecer separados dos valores observados, com janela, fórmula/modelo, hipóteses, versão e limites visíveis. Ausência não vira zero nem observação fictícia.
- Primeiro piloto autorizado: repasses federais de atenção primária, equipes financiadas e profissionais do Mais Médicos, em cinco cidades, com expansão condicionada à validação da integração.

### Expansão nacional da saúde — 15/10/2026

Expansão autorizada após validação do piloto. As páginas do cadastro municipal completo apresentam repasses, equipes e vagas do provimento federal, com cobertura e datas independentes. A versão nacional utiliza o consolidado de vagas ocupadas (`total_ocupadas`) do Mais Médicos, incluindo instituições vinculadas, em vez de apresentar registros antigos da série histórica como situação atual. Zeros explicitamente publicados são distintos de ausência. DSEI e registros estaduais do provimento não são municipalizados. Não há novo programa, projeção ou atribuição causal nesta expansão.

### Financiamento e estrutura de saúde — expansão autorizada

Total municipal e valor por habitante abrangem transferências FNS fundo a fundo de todas as áreas; emendas e atenção primária já integram o total. A evolução usa anos completos comparáveis (2024/2025), mantendo 2026 parcial separado. Composição de despesas SIOPS é identificada como despesa por fonte, sem ser apresentada como composição de receitas. A rede CNES descreve localização e cadastro, sem inferir compra federal, residência dos atendidos ou acesso efetivo. Destinatários não municipais sediados na cidade ficam separados, incluindo a AgSUS identificada em Brasília. Traços de equipamentos e ausência de linha permanecem indisponíveis.


### Complementação das cidades e competência MDS — 15/10/2026

As seis ausências cartográficas de pessoas em famílias beneficiárias são completadas exclusivamente pela consulta tabular oficial VIS DATA 3 por código IBGE. A publicação é condicionada à soma das três faixas, total Brasil e cinco cidades de controle da mesma competência. A auditoria revelou que os valores do mapa inicialmente rotulados como agosto eram de setembro/2026; o período publicado foi corrigido para 202609, com preservação dos 5.565 valores anteriores e rastreabilidade da correção. Famílias MDS e parcelas CGU mantêm seus períodos independentes. As 5.571 cidades passam a ter cobertura populacional validada, sem médias ou valores estimados.
