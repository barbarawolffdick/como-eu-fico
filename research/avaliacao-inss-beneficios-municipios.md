# Avaliação de fonte — benefícios do INSS por município (Ministério da Previdência)

**Data:** 17/10/2026. **ID proposto:** RENDA-03 — Aposentadorias, pensões e demais benefícios do INSS. **Estado:** avaliada sobre amostra baixada; **não integrada**. Nenhum arquivo foi versionado ou publicado em `data/`.

**Veredito:** fonte estruturalmente limpa, com série anual 2019–2025 validada, mas **ainda não IMPLEMENTÁVEL** segundo o [catálogo de fontes](../docs/catalogo-fontes-v0.md). O bloqueio é semântico: o município é o do **órgão pagador**, e não o de residência. O teste de escala (seção própria) indica a **região imediata do IBGE** como menor unidade publicável sem essa distorção; o município só pode aparecer como contexto, com ressalva. Faltam licença, dicionário de espécies e um teste com população idosa.

## Origem examinada

- Página: [Emitidos por Municípios — Ministério da Previdência Social](https://www.gov.br/previdencia/pt-br/assuntos/previdencia-social/emitidos-municipios-2023) (o endereço termina em `2023`, mas a página lista os arquivos de 2025; atualizada em 25/05/2026).
- Arquivos baixados em 17/10/2026:

| Arquivo | Bytes | SHA-256 |
|---|---|---|
| `ben_municipios_especie_2025.xlsx` | 3.171.583 | `439e7af2d9f9e33c6acc05ea4e46e80c82d18e1f571fd8173636293e48537358` |
| `ben_municipios_clientela_2025.xlsx` | 918.024 | `017eed6e12a774dc3ed9647d48993ee0f5bcd2a20130d7ba293a379fbc94eda1` |

- Rodapé das planilhas: “INSS / Síntese, consulta efetuada em 22/05/2026; IBGE / Estimativas de população. Elaboração: CGEET/DRGPS/SRGPS/MPS”.

## Estrutura encontrada

**`ben_municipios_especie_2025.xlsx`** — quatro abas, cabeçalho em três linhas mescladas (linhas 5–7), dados a partir da linha 8:

| Aba | Medida | Período |
|---|---|---|
| `Qtd_dez2025` | Quantidade de benefícios emitidos | Dezembro de 2025 (estoque do mês) |
| `Valor_R$_dez25` | Valor líquido emitido, R$ | Dezembro de 2025 |
| `Valor_Médio_R$_dez24` | Valor líquido médio, R$ | **Dezembro de 2025**, apesar do nome da aba; confere exatamente com valor ÷ quantidade |
| `Valor_Total_2025` | Valor líquido emitido, R$ | Ano de 2025 (soma dos meses) |

Colunas: `Nome`, `Código IBGE` (inteiro de 7 dígitos), `UF`; benefícios do RGPS — aposentadorias (total, por idade, por invalidez, por tempo de contribuição), pensões por morte, auxílios, outros previdenciários, total previdenciário; **benefícios assistenciais e de legislação específica** (uma coluna única: BPC/LOAS somado aos BLE); total geral. A aba de quantidade traz ainda `População no Município` e uma coluna de notas.

**`ben_municipios_clientela_2025.xlsx`** — uma aba, somente RGPS, com população 2025, “% benefícios sobre população” e quantidade (dezembro), valor (dezembro) e valor anual, cada um separado em **urbano e rural**.

## Verificações executadas

| Verificação | Resultado |
|---|---|
| Cobertura territorial | 5.571 municípios nas abas de valor, com o mesmo conjunto de códigos IBGE usado no projeto. |
| Código ausente | Em `Qtd_dez2025`, Boa Esperança do Norte (MT, 5101837) aparece com o código em branco (`' '`). As demais abas trazem o código. A junção exige corrigir isso com regra explícita, nunca por nome. |
| Nomes | 39 grafias diferem do cadastro IBGE do projeto (ex.: “Itapagé” × “Itapajé”, “Araças” × “Araçás”), com códigos e UFs coincidentes. **Junção só por código.** |
| Somas internas | Zero erros: tipos de aposentadoria somam o total; componentes somam o total previdenciário; previdenciário + assistencial somam o total geral (quantidade, dezembro e ano). |
| Conciliação com a linha BRASIL | Quantidade: diferença de 346, que é exatamente a linha sem código de Boa Esperança do Norte. Valor de dezembro: diferença zero. Valor anual: a linha BRASIL supera a soma dos municípios em R$ 5.660,92 (cerca de 6 × 10⁻⁹ do total), resíduo não alocado a município e não explicado. |
| Ausências | Nenhuma célula vazia. Zeros explícitos existem (ex.: 117 municípios sem aposentadoria por tempo de contribuição) e devem ser preservados como zero da fonte. |
| Clientela × espécie | O total RGPS de dezembro coincide em 5.570 de 5.571 municípios (a exceção é a linha sem código). Mesma população nas duas planilhas. |
| População | Prévia IBGE de 30/12/2025 baseada no Censo 2022, com **27 municípios** (AM e MA) usando população judicial, conforme notas. Difere da população IBGE 2026 publicada pelo projeto. |
| Histórico | A página lista só 2025. Os mesmos nomes de arquivo existem para 2019–2024; ver seção “Série 2019–2025”. |

## Série 2019–2025

Arquivos não listados na página, baixados em 17/10/2026 pelo mesmo padrão de endereço (`ben_municipios_{especie|clientela}_{ano}.xlsx`). Não há arquivo de clientela para 2019 nem arquivos de 2026.

| Arquivo | Bytes | SHA-256 |
|---|---|---|
| `ben_municipios_especie_2019.xlsx` | 2.413.238 | `b006a6b4fdd61fc651ce39f9d58b6532a2e9aef146616b5d6347cbb4d44f5d64` |
| `ben_municipios_especie_2020.xlsx` | 2.184.680 | `b5acc3d5cb2bf34d34c322f0a03739c20c08b71e568d205ad718ea9467cc619e` |
| `ben_municipios_clientela_2020.xlsx` | 822.579 | `5cebadfe836624a9d4a3297f1553ed6105b1867555174a2f01160263546bdf09` |
| `ben_municipios_especie_2021.xlsx` | 2.209.867 | `e2ad93e8a3b3c7603be78674a887c24efb01825757fea907c26c09ed56a7e522` |
| `ben_municipios_clientela_2021.xlsx` | 840.354 | `a63a408ab9b17ff1b73895029c0432db42177bfd8fb98e24851c1f6a4994d715` |
| `ben_municipios_especie_2022.xlsx` | 2.174.679 | `eced643d878a2c69289e19dca601bc65bc247635813addbea712b6a23beda578` |
| `ben_municipios_clientela_2022.xlsx` | 846.912 | `2281581ca36d6cab562942b69ed27060a0b6a9d9692c6ef6f2b4afa640114ccb` |
| `ben_municipios_especie_2023.xlsx` | 3.179.172 | `bc36dd970b5b169dfe2318590d40a9286f98c86a36eda0bceb9280750e420215` |
| `ben_municipios_clientela_2023.xlsx` | 850.151 | `068cc3fb75b462d102645d983df9c02637fcff4add8669694b0e89202a08b9ae` |
| `ben_municipios_especie_2024.xlsx` | 3.175.325 | `6398150390f8bf92947b8c8c721a970e703b5a18592aced6d29584b1d875d19a` |
| `ben_municipios_clientela_2024.xlsx` | 893.925 | `68b8604a67e36797f1720bb8c2ebd8b8ab5a5dffef56bcf5035dab054431c55a` |

Controles reproduzíveis com `scripts/auditar_inss_municipios.py` (requer `requirements-dados.txt`).

**Resultado dos controles, ano a ano:** 5.570 municípios em 2019–2024 e 5.571 em 2025 (Boa Esperança do Norte-MT passa a constar). Todos os códigos existem no cadastro IBGE; nenhum município do cadastro falta no ano em que já existia. Zero erros de soma interna e zero células vazias em todos os anos. Onde há linha BRASIL (2023–2025), a soma municipal fecha exatamente, salvo o resíduo de R$ 5.660,92 no valor anual de 2025. 2019–2022 não trazem total nacional. Em todos os anos de 2020–2025, o total RGPS da planilha de clientela coincide com a de espécies, e urbano + rural = total.

**Armadilhas de leitura que uma ingestão precisa tratar:**

1. **Três leiautes.** 2019–2022: código na 1ª coluna, nome na 2ª, UF por extenso, abas `Quantidade - dezAA`, `Valor (R$) - dezAA`, `Valor (R$) - AAAA`. 2023: nome antes do código, sigla da UF, abas `Qtd_dez2023` etc., cabeçalho duas linhas acima. 2024–2025: mesmo formato de 2023, cabeçalho na linha 5.
2. **Cabeçalho invertido em `clientela_2024`.** O cabeçalho diz “Código IBGE, Município”, mas os dados trazem nome e depois código. A coluna do código deve ser identificada pelos dados (7 dígitos), nunca pelo rótulo.
3. **População como texto em 2022 e 2023.** 30 células em 2022 (ex.: Porto Velho `461.748(1)`) usam ponto de milhar e marcador de nota. Uma conversão direta leria 461,748 habitantes. Exige regra explícita.
4. **Título errado em `Valor_Total_2023`.** O título diz “benefícios Urbanos”, mas os valores coincidem com o total urbano + rural da planilha de clientela em 5.570 de 5.570 municípios, e com o total urbano em nenhum. É o total.
5. **Nomes de municípios com “Brasil”** (Brasília, Brasiléia, Nova Brasilândia D'Oeste...) não podem ser confundidos com a linha BRASIL. Comparar o rótulo inteiro.
6. **Colunas extras vazias** nas abas anuais de 2020–2022 (26–27 colunas, sem conteúdo após a 13ª).

## O problema central: município do órgão pagador

A nota das planilhas diz que os benefícios são “agregados por município de acordo com o de localização do órgão pagador”, e que “não necessariamente refletem o município de residência” dos beneficiários.

O efeito é grande. Usando a população da própria planilha, os benefícios por 100 habitantes variam de **0,2** (São Raimundo do Doca Bezerra-MA) a **78,2** (Nova Petrópolis-RS), com mediana de 18,7. Há **72 municípios abaixo de 2 por 100** e polos regionais acima de 60 (Pau dos Ferros-RN, Valença do Piauí-PI). Isso é deslocamento para a cidade da agência bancária, não diferença de cobertura previdenciária.

O padrão é estrutural e persistente: entre 67 e 104 municípios ficam abaixo de 2 benefícios por 100 habitantes em cada ano de 2019–2025, e 58 dos 72 casos de 2025 já estavam nessa situação em 2024.

Exemplo, região imediata de Pau dos Ferros-RN (34 municípios, 2025): a cidade-polo tem 13,7% da população da região e 33,6% dos benefícios emitidos (75,5 por 100 habitantes). Riacho da Cruz e Francisco Dantas, com 1,2% da população cada, têm 0,2% dos benefícios (cerca de 6 por 100).

Consequências para o contrato:
- **Valores por habitante e rankings municipais não são válidos** com esta medida. Comparar Pau dos Ferros com seus vizinhos mediria a rede bancária, não a previdência.
- Agregações maiores reduzem o problema; ver o teste de escala abaixo.
- Na página da cidade, a medida só pode aparecer com a ressalva explícita, e nunca ao lado do placar como se descrevesse os moradores.

## Teste de escala: município, região imediata e UF

Regiões imediatas do IBGE (510) vêm de `data/reference/ibge_municipios_raw.json`, que cobre os 5.571 municípios. População: a da própria planilha de cada ano. Duas medidas:

- **Benefícios emitidos por 100 habitantes** (quantidade em dezembro) em cada escala.
- **Índice de dissimilaridade:** percentual dos benefícios que precisaria mudar de unidade, dentro de cada grupo, para ficar proporcional à população. É um **limite superior** da distorção, porque também inclui diferenças reais de idade entre lugares.

**Benefícios por 100 habitantes, 2025**

| Escala | Unidades | Mín. | P5 | Mediana | P95 | Máx. | Abaixo de 5 | Acima de 40 |
|---|---|---|---|---|---|---|---|---|
| Município | 5.570 | 0,2 | 4,3 | 18,7 | 36,3 | 78,2 | 358 | 167 |
| Região imediata | 510 | 3,4 | 11,3 | 22,2 | 30,4 | 39,0 | 1 | 0 |
| UF | 27 | 8,7 | 10,3 | 19,3 | 22,1 | 26,9 | 0 | 0 |

**Dissimilaridade em relação à população (%)**

| Comparação | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Municípios dentro da região imediata | 9,8 | 9,7 | 9,8 | 9,8 | 9,6 | 9,7 | 9,8 |
| Municípios dentro da UF | 12,0 | 11,9 | 11,9 | 12,0 | 11,6 | 11,5 | 11,5 |
| Regiões imediatas dentro da UF | 6,7 | 6,7 | 6,7 | 6,8 | 6,3 | 6,0 | 5,9 |
| UFs no Brasil | 6,1 | 6,1 | 6,2 | 5,4 | 5,7 | 5,1 | 5,1 |

**Leitura:**

- Cerca de **10% dos benefícios** estão “fora do lugar” entre os municípios de uma mesma região imediata, de forma estável em sete anos. É a parcela que a agregação regional elimina, e é compatível com o deslocamento para o município do órgão pagador.
- Na região imediata, os extremos ficam plausíveis. Os valores mais altos são regiões envelhecidas do interior gaúcho (Encantado 39,0; Cerro Largo 38,3; Três Passos 38,1), e os mais baixos são regiões jovens do Norte (Porto Grande-AP 6,2; Caracaraí-RR 7,2). O resíduo de ~6% entre regiões é, ao menos em parte, demografia real.
- **Exceção a investigar:** a região de Pacaraima-RR (3,4 por 100) fica isolada abaixo das demais. Pode ser população jovem e migrante na fronteira, ou benefícios pagos em Boa Vista, que é outra região imediata.
- A UF é a escala mais segura, mas perde quase toda a leitura territorial que o projeto busca.

**Recomendação:** usar a **região imediata** como menor unidade publicável para quantidades, valores e taxas. Na página da cidade, mostrar o indicador da região imediata, com a lista de municípios que a compõem. O valor municipal bruto só como contexto, com a ressalva do órgão pagador, sem ranking nem taxa por habitante. Antes de publicar, testar contra a população de 60 anos ou mais do Censo 2022: se a distorção restante entre regiões for demográfica, a razão benefícios/idosos deve variar bem menos que benefícios/habitantes.

## Avaliação segundo os critérios do catálogo

| Critério para IMPLEMENTÁVEL | Situação |
|---|---|
| 1. URL oficial e licença/restrições de uso | URL oficial confirmada. **Licença não verificada** na página. |
| 2. Dicionário, período de referência e unidade | Definições de quantidade (créditos emitidos) e valor (líquido = bruto − descontos) na página; abas definem dezembro/ano. **Falta dicionário formal** das espécies em cada grupo (ex.: quais espécies compõem “outros” e “assistenciais e legislação específica”). |
| 3. Identificador mapeável a `codigo_ibge` | Sim, código IBGE de 7 dígitos, com uma exceção corrigível. **Mas o território é o do órgão pagador.** |
| 4. Frequência, histórico e atualização | Anual (estoque de dezembro + soma do ano). Série 2019–2025 validada (clientela 2020–2025), com três leiautes. Arquivos anteriores a 2025 não estão listados na página. Calendário de publicação não declarado. |
| 5. Ausências, revisões e duplicação | Sem ausências; zeros explícitos. Política de revisão retroativa não documentada (os arquivos antigos podem ter sido regravados). Linha BRASIL fecha exatamente em 2023–2025, salvo R$ 5.660,92 no valor anual de 2025; 2019–2022 sem total nacional. BPC aparece somado aos BLE, sem separação. |
| 6. Exemplo verificável, teste e limitações | Exemplo e controles acima, reproduzíveis com os hashes registrados. Limitação principal documentada. |

## Distinções exigidas pelo contrato

- **Quantidade ≠ pessoas.** São créditos emitidos; uma pessoa com dois benefícios conta duas vezes.
- **Emitido ≠ pago ≠ sacado.** O valor é líquido emitido no mês, não o recebido ou gasto no município.
- **Estoque ≠ fluxo.** Dezembro é o estoque de benefícios mantidos naquele mês; o anual é soma de emissões. Não converter o anual em mensal.
- **Federal, mas não discricionário.** Aposentadorias e pensões do RGPS são direitos contributivos regidos por lei. Sua presença no município não indica escolha política de um governo; a variação anual reflete demografia, regras e reajustes. Isso deve constar de qualquer leitura ao lado do voto.
- **Nominal.** Valores sem ajuste pela inflação; reajustes anuais do salário mínimo e do INSS mudam o valor médio sem mudar a cobertura.

## Pendências antes de uma eventual integração

1. Confirmar a licença e os termos de uso com o Ministério da Previdência ou o rodapé institucional.
2. Obter o dicionário das espécies por grupo (especialmente “assistenciais e de legislação específica”) e verificar se o BPC pode ser separado em outra publicação.
3. ~~Validar 2019–2024~~ — feito em 17/10/2026; ver “Série 2019–2025”. Confirmar com o Ministério se os arquivos não listados são oficiais e definitivos.
4. ~~Testar a escala~~ — região imediata recomendada; falta o teste com população de 60+ do Censo 2022 e a investigação de Pacaraima-RR.
5. Comparar com uma fonte por residência, se existir (ex.: dados abertos do INSS, “benefícios mantidos”). Notícia de jan/2026 relata que o portal do INSS deixou de publicar valores; verificar o que está disponível hoje.
6. Revisar este documento no contrato editorial (seção de dimensões “Renda e proteção”) antes de escrever qualquer ingestão.

## Referências

- [Ministério da Previdência — Emitidos por Municípios](https://www.gov.br/previdencia/pt-br/assuntos/previdencia-social/emitidos-municipios-2023)
- [INSS — Dados abertos e Plano de Dados Abertos](https://www.gov.br/inss/pt-br/acesso-a-informacao/dados-abertos/dados-abertos)
- [IBDP — Estatísticas municipais atualizadas no portal da Previdência](https://www.ibdp.org.br/?p=11253)
- [Correio da Manhã, 26/01/2026 — retirada de valores do portal do INSS](https://digital.correiodamanha.com.br/jornalcorreiodamanha/2026/01/26/23010b/pdf/2601cmanha09.pdf)
