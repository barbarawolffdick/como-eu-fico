# Etapa 2 — consolidação eleitoral municipal

A consolidação dos 27 arquivos `dados-municipios/*/resumo_municipios_*.csv` produz um CSV nacional, com **uma linha por município** e código IBGE validado na etapa 1. Nenhum arquivo original é modificado.

## Uso

```bash
python3 scripts/mapear_municipios.py
python3 scripts/consolidar_eleicoes.py
```

## Arquivos produzidos

- `data/processed/eleicoes_2026_municipios.csv`: dados municipais padronizados, CSV UTF-8 separado por vírgula
- `data/quality/inconsistencias_eleitorais.csv`: inconsistências por regra e registro de origem
- `data/quality/resumo_eleitoral.json`: quantidade de linhas, municípios faltantes e problemas

Os percentuais são recalculados com base nos votos válidos ou eleitores aptos, conforme o indicador, com duas casas decimais na saída. As comparações com percentuais originais toleram diferença de 0,02 ponto percentual, para não sinalizar arredondamentos normais. Votos de outros candidatos = votos válidos − votos Lula − votos Flávio.

**Importante:** o ano e o turno são metadados definidos para esta coleção, e ainda precisam ser confirmados com a procedência da fonte. Esta etapa **não certifica** os votos frente ao TSE. O programa não deve ser usado como confirmação de resultados eleitorais oficiais. A validação externa com os arquivos originais do TSE constitui etapa posterior.

O script termina com código de saída 1 se identificar inconsistências, municípios ausentes ou quantidade inesperada de CSVs. O relatório permanece gravado para depuração.
