# Mapeamento de municípios — IBGE

Etapa 1 do projeto Como Eu Fico. Mantém os arquivos originais em `dados-municipios/` inalterados.

## Execução

Requer Python 3.10+ e acesso à internet na primeira execução.

```bash
python3 scripts/mapear_municipios.py
```

Para atualizar explicitamente a consulta oficial:

```bash
python3 scripts/mapear_municipios.py --refresh-ibge
```

## Fonte

API oficial de localidades do IBGE: https://servicodados.ibge.gov.br/api/v1/localidades/municipios

A correspondência TSE/IBGE também está publicada em:
https://dadosabertos.tse.jus.br/dataset/codigos-oficiais-de-uf-e-municipios-segundo-o-tse-e-o-ibge

**Limite atual:** o script faz correspondência por UF + nome municipal normalizado, validado contra o IBGE. Ainda não confere os códigos de município do cadastro eleitoral do TSE porque os CSVs originais consultados não trazem esse identificador. Portanto, não trataremos correspondência por nome como validação cruzada entre códigos oficiais.

## Saídas

- `data/reference/ibge_municipios_raw.json`: snapshot bruto da API, preservado para auditoria
- `data/reference/municipios_ibge.csv`: cadastro oficial simplificado
- `data/reference/municipios_mapeados.csv`: código IBGE por registro eleitoral
- `data/quality/municipios_nao_correspondidos.csv`: pendências, sem tentativa de aproximação
- `data/quality/resumo_mapeamento.json`: métricas da execução

Os arquivos CSV são gravados em UTF-8 e separados por vírgula; nomes e códigos são strings. O script encerra com erro se não encontrar arquivos ou se houver pendências.

A pasta `Exterior` é intencionalmente excluída, pois suas localidades eleitorais não são municípios brasileiros. O Distrito Federal requer conferência de granularidade: Brasília é a referência municipal do IBGE; resultados por regiões administrativas não devem ser interpretados como municípios.

**Antes de usar em reportagens:** conferir abrangência, total de municípios únicos e resultados oficiais do TSE; não assumir que uma correspondência técnica valida os resultados eleitorais de origem.
