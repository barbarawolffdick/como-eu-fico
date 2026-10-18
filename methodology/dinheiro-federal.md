# Dinheiro federal na economia local — PIB, INSS e FPM

Versão de 17/10/2026. Snapshots, esquema 1, ainda **não lidos pelo site**:

- `data/public/dinheiro_federal.json` — **2023**, tudo observado (o PIB municipal mais recente do IBGE);
- `data/public/dinheiro_federal_2025.json` — **2025**, INSS e FPM observados; **PIB estimado e rotulado** (ver abaixo).

Reprodução:

```bash
pip install -r requirements-dados.txt
python -m scripts.publicar_dinheiro_federal --ano 2023
python -m scripts.publicar_dinheiro_federal --ano 2025 --pib estimado
python -m scripts.publicar_dinheiro_federal --diagnosticar 2019 2020 2021 2022 2023 2024 2025
python -m unittest discover -s tests -p 'test_dinheiro_federal.py' -v
```

`--diagnosticar` só relata a completude de INSS e FPM por ano; não publica. Anos fora de 2023 e 2025 gravam em `dinheiro_federal_{ano}.json`.

O cache `data/raw/dinheiro_federal/` guarda cada resposta com URL, SHA-256 e data de extração; sem `--atualizar`, a execução reutiliza os arquivos verificados. A saída só é substituída depois de todos os controles.

## Fontes

| Fluxo | Fonte | Medida | Unidade territorial |
|---|---|---|---|
| PIB | IBGE, tabela 5938, variável 37 (API de agregados) | PIB a preços correntes do ano | Município |
| INSS | Ministério da Previdência, `ben_municipios_especie_{ano}.xlsx` | Valor líquido emitido no ano, por grupo de espécies; quantidade emitida em dezembro | **Município do órgão pagador** |
| FPM | Tesouro Nacional, transferências constitucionais mensais (CKAN, licença ODbL) | Linhas `FPM/FPM` (cota mensal, líquida da retenção para o FUNDEB) e `FPM 1%/FPM 1%` (cotas extraordinárias de julho, setembro e dezembro) | Município |
| Cadastro | IBGE, API de localidades | Nome, UF, região imediata | Município |

Totais publicados:

| Ano | PIB | INSS | FPM |
|---|---|---|---|
| 2023 | R$ 10,94 trilhões (observado) | R$ 802,2 bilhões (concilia exatamente com a linha BRASIL) | R$ 152,0 bilhões |
| 2025 | R$ 12,74 trilhões (**estimado**) | R$ 950,0 bilhões (resíduo não alocado de R$ 5,7 mil frente à linha BRASIL) | R$ 171,6 bilhões |

## Situação por ano (diagnóstico de 17/10/2026)

| Ano | INSS | FPM | Publicável? |
|---|---|---|---|
| 2019 | completo; concilia | **incompleto**: 09 parcial (3º decêndio zerado), 10 sem crédito de FPM | não |
| 2020 | completo; concilia | 12 meses íntegros; **27 nomes antigos** sem correspondência revisada | não, até revisar os nomes |
| 2021 | completo; concilia | 12 meses íntegros (08 lido com formato misto); mesmos 27 nomes até 2021-07 | não, até revisar os nomes |
| 2022 | completo; concilia | **incompleto**: 10 ausente do catálogo | não |
| 2023 | completo | completo | sim (PIB observado) |
| 2024 | completo | **incompleto**: 01, 02, 08, 10, 11 parciais; 09 com escala ×96 | não |
| 2025 | completo | completo | sim (PIB estimado) |

O PIB municipal do IBGE vai até 2023; para 2024 e 2025 só com `--pib estimado` ou `--pib ausente`. Os 27 nomes de 2019–2021 (ex.: Parati, Embu, Gouvêa, Santarém-PB, Augusto Severo) são grafias anteriores a renomeações e ficam fora de `ALIASES_FPM` até revisão um a um. A API de transferências do Tesouro (`apiapex.tesouro.gov.br/.../por_estado_municipio_detalhe`) foi avaliada para repor meses ausentes e não respondeu (tempo esgotado em 17/10/2026); não é usada.

## Regras de transformação

- **FPM, cotas extraordinárias.** Até 18/10/2026 a linha `FPM 1%` ficava de fora e o FPM publicado era cerca de 13% menor. A conciliação com o Siconfi (DCA 2025 de Juazeiro do Norte, FPM líquido de R$ 179,87 mi) fecha ao centavo com a soma das duas linhas. O valor das cotas extraordinárias é publicado à parte em `fpm.cotas_extraordinarias_centavos`.

- **Fluxos separados.** INSS é benefício pago a pessoas; FPM é transferência constitucional ao governo municipal. O snapshot não soma os dois nem os chama de investimento.
- **INSS por órgão pagador.** O valor mostra quanto dinheiro de benefícios entra na economia pela cidade, não quantos moradores recebem. Não calcular taxas por habitante nem rankings municipais de cobertura; para comparar territórios, agregar por região imediata (ver [avaliação da fonte](../research/avaliacao-inss-beneficios-municipios.md)).
- **INSS, leiautes.** O cabeçalho é localizado pelo rótulo “IBGE” e a coluna do código é decidida pelos dados. Cada linha precisa fechar as somas internas; a linha BRASIL, quando existe, precisa conciliar com os municípios (quantidade exata; valor com tolerância de R$ 10 mil). Linha sem código só é aceita por nome e UF idênticos ao cadastro e fica registrada.
- **INSS, linha de total.** Rotulada “BRASIL” (2023–2025), “Total” na coluna do código com nome vazio (2019–2022) ou sem rótulo; precisa ser única e conciliar. De 2019 a 2022 o resíduo é zero.
- **Ruído do Excel.** Somas grandes chegam como ponto flutuante; valores são arredondados ao centavo apenas se o excesso for menor que 1/100 de centavo **ou** que 10⁻¹² do próprio valor. Em 2019 as células municipais são somas em ponto flutuante feitas pela fonte: 97 células passam de 1/100 de centavo (até 0,17 centavo em São Paulo), mas o desvio relativo máximo é 2,2×10⁻¹³, típico de acumulação de arredondamento. O limite relativo dá margem de 4× e continua recusando fração real de centavo em qualquer célula abaixo de R$ 5 bilhões; as somas internas e a conciliação com o total nacional seguem como controles.
- **FPM, competência pelo conteúdo.** O nome do arquivo no catálogo nem sempre corresponde ao mês (2024-01 saiu em `…202402`); o mês vem das colunas `ANO`/`Mês` (cabeçalho comparado sem caixa; mês “8” vira “08”). Por isso também são lidos os arquivos com nome de janeiro e fevereiro do ano seguinte. Exige os 12 meses e os 12 créditos de cada município.
- **FPM, formato numérico.** Padrão: ponto decimal. O arquivo de 2021-08, exportado do Excel, mistura ponto decimal, vírgula decimal com ponto de milhar e “-” contábil para zero; os três são aceitos e registrados em `formatos_numericos` da fonte do mês. Ponto seguido de três dígitos sem vírgula é ambíguo e interrompe.
- **FPM, meses parciais.** Mês cujo 3º decêndio nacional da linha `FPM/FPM` é zero foi publicado antes do último crédito; é recusado, salvo se houver no catálogo uma versão completa que o contenha (ela é escolhida e a parcial, descartada). Mês sem nenhum crédito de FPM também é recusado.
- **FPM, escala.** O total nacional de cada mês precisa ficar entre ¼ e 4× a mediana dos demais meses do ano (a variação legítima fica abaixo de 2×). Em 2024-09 os valores vêm sem ponto decimal (×100): o mês é recusado, **nunca reescalado automaticamente**.
- **FPM, relatório.** Um ano com qualquer mês ausente, parcial ou de escala suspeita não é publicado; o erro lista todos os meses e motivos de uma vez.
- **FPM, versões repetidas.** Se um mês aparece mais de uma vez, as versões precisam ser encadeadas (a menor contida na maior, com valores idênticos onde já havia valor); fica a mais completa e as demais são registradas em `fontes.fpm.versoes_descartadas`. Versões divergentes interrompem a publicação. Em 2023, uma versão de março sem o 3º decêndio foi descartada.
- **FPM, nomes.** O arquivo não traz código IBGE. A correspondência é exata (sem acentos e apóstrofos) ou por uma das 34 correspondências revisadas em `ALIASES_FPM`, incluindo as renomeações Açu → Assú e Presidente Juscelino → Serra Caiada. Nome sem correspondência interrompe a publicação.
- **Excluído do FPM:** linhas de FUNDEB (inclusive impostos estaduais redistribuídos), royalties, ITR, IOF-Ouro e CIDE.

## PIB estimado (2025)

O IBGE publica o PIB municipal com dois anos de defasagem. Todo snapshot traz um bloco `pib` que diz de onde vem `pib_centavos`: `{"ano_fonte": <ano>, "estimado": false}` quando é o PIB publicado do próprio ano. Com `--pib estimado`, `pib_centavos` recebe a estimativa (centavos inteiros) e o bloco fica `{"ano_fonte": 2023, "estimado": true, "fator", "metodo", "fonte_fator", "pib_brasil_milhoes"}`; a definição de `pib_centavos` começa com “ESTIMATIVA”. Leitores devem consultar `pib.estimado` antes de exibir o valor. A estimativa é:

> PIB municipal observado de 2023 × (PIB nacional nominal de 2025 ÷ PIB nacional nominal de 2023)

O PIB nacional é a soma dos quatro trimestres da tabela 1846 do IBGE (valores correntes, PIB a preços de mercado): R$ 10.943.344 milhões em 2023 e R$ 12.738.566 milhões em 2025, fator **1,164047**. O resultado é arredondado a mil reais. Antes de estimar, a soma do PIB municipal de 2023 precisa conferir com o nacional trimestral (tolerância de 2%). O documento declara `natureza: "fluxos observados; PIB estimado"`; a publicação é recusada se faltar fator, método ou fonte do fator, ou se um PIB de outro ano vier marcado como não estimado. Com `--pib ausente`, `pib_centavos` fica nulo com motivo e o bloco é `{"ano_fonte": null, "estimado": false}`.

Limite: a estimativa supõe que todo município cresceu como o país. Não capta safra, preço de commodities, royalties nem choques locais; razões fluxo/PIB de 2025 devem ser apresentadas como aproximação. Município sem PIB em 2023 (Boa Esperança do Norte) fica sem estimativa. Substituir pelo PIB observado quando o IBGE publicar 2025 (rodar com `--atualizar`, porque a resposta vazia do IBGE fica no cache).

## Ausências

Ausência é nula com motivo, nunca zero:
- Boa Esperança do Norte-MT (`5101837`): instalada após 2023, sem PIB, INSS nem FPM em 2023. Em 2025 tem INSS (código inferido por nome e UF idênticos) e FPM, mas não PIB (sem base de 2023 para estimar).
- Fernando de Noronha-PE (`2605459`): distrito estadual, sem FPM.

## Limites

Valores nominais, sem ajuste pela inflação. O PIB mede produção no território, não renda dos moradores; a razão entre fluxos e PIB indica peso relativo, não dependência ou efeito. A quantidade do INSS conta créditos, não pessoas. O grupo “assistencial e legislação específica” soma BPC/LOAS e benefícios especiais, sem separação.
