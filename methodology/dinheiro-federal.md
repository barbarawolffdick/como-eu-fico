# Dinheiro federal na economia local — PIB, INSS e FPM

Versão de 17/10/2026. Snapshot `data/public/dinheiro_federal.json`, esquema 1, ano de referência **2023** (o PIB municipal mais recente do IBGE). Ainda **não é lido pelo site**. Reprodução:

```bash
pip install -r requirements-dados.txt
python -m scripts.publicar_dinheiro_federal --ano 2023
python -m unittest discover -s tests -p 'test_dinheiro_federal.py' -v
```

O cache `data/raw/dinheiro_federal/` guarda cada resposta com URL, SHA-256 e data de extração; sem `--atualizar`, a execução reutiliza os arquivos verificados. A saída só é substituída depois de todos os controles.

## Fontes

| Fluxo | Fonte | Medida | Unidade territorial |
|---|---|---|---|
| PIB | IBGE, tabela 5938, variável 37 (API de agregados) | PIB a preços correntes do ano | Município |
| INSS | Ministério da Previdência, `ben_municipios_especie_{ano}.xlsx` | Valor líquido emitido no ano, por grupo de espécies; quantidade emitida em dezembro | **Município do órgão pagador** |
| FPM | Tesouro Nacional, transferências constitucionais mensais (CKAN, licença ODbL) | Linha `FPM/FPM`: crédito ao município, líquido da retenção para o FUNDEB | Município |
| Cadastro | IBGE, API de localidades | Nome, UF, região imediata | Município |

Totais de 2023 publicados: PIB R$ 10,94 trilhões; INSS R$ 802,2 bilhões (concilia exatamente com a linha BRASIL da planilha); FPM R$ 152,0 bilhões.

## Regras de transformação

- **Fluxos separados.** INSS é benefício pago a pessoas; FPM é transferência constitucional ao governo municipal. O snapshot não soma os dois nem os chama de investimento.
- **INSS por órgão pagador.** O valor mostra quanto dinheiro de benefícios entra na economia pela cidade, não quantos moradores recebem. Não calcular taxas por habitante nem rankings municipais de cobertura; para comparar territórios, agregar por região imediata (ver [avaliação da fonte](../research/avaliacao-inss-beneficios-municipios.md)).
- **INSS, leiautes.** O cabeçalho é localizado pelo rótulo “IBGE” e a coluna do código é decidida pelos dados. Cada linha precisa fechar as somas internas; a linha BRASIL, quando existe, precisa conciliar com os municípios (quantidade exata; valor com tolerância de R$ 10 mil). Linha sem código só é aceita por nome e UF idênticos ao cadastro e fica registrada.
- **Ruído do Excel.** Somas grandes chegam como ponto flutuante; valores são arredondados ao centavo apenas se o excesso for menor que 1/100 de centavo.
- **FPM, competência pelo conteúdo.** O nome do arquivo no catálogo nem sempre corresponde ao mês; o mês vem das colunas `ANO`/`Mês`. Exige os 12 meses e os 12 créditos de cada município.
- **FPM, versões repetidas.** Se um mês aparece mais de uma vez, as versões precisam ser encadeadas (a menor contida na maior, com valores idênticos onde já havia valor); fica a mais completa e as demais são registradas em `fontes.fpm.versoes_descartadas`. Versões divergentes interrompem a publicação. Em 2023, uma versão de março sem o 3º decêndio foi descartada.
- **FPM, nomes.** O arquivo não traz código IBGE. A correspondência é exata (sem acentos e apóstrofos) ou por uma das 34 correspondências revisadas em `ALIASES_FPM`, incluindo as renomeações Açu → Assú e Presidente Juscelino → Serra Caiada. Nome sem correspondência interrompe a publicação.
- **Excluído do FPM:** linhas de FUNDEB (inclusive impostos estaduais redistribuídos), royalties, ITR, IOF-Ouro e CIDE.

## Ausências

Ausência é nula com motivo, nunca zero:
- Boa Esperança do Norte-MT (`5101837`): instalada após 2023, sem PIB, INSS nem FPM no ano.
- Fernando de Noronha-PE (`2605459`): distrito estadual, sem FPM.

## Limites

Valores nominais, sem ajuste pela inflação. O PIB mede produção no território, não renda dos moradores; a razão entre fluxos e PIB indica peso relativo, não dependência ou efeito. A quantidade do INSS conta créditos, não pessoas. O grupo “assistencial e legislação específica” soma BPC/LOAS e benefícios especiais, sem separação.
