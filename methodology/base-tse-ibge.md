# Base eleitoral TSE + IBGE (sem uso dos relatórios antigos)

A fonte eleitoral única é o arquivo de votação presidencial por seção de 2026 do TSE e seu detalhamento de apuração, primeiro turno. A referência territorial é **somente** `data/reference/municipios_ibge.csv`, que deve ter sido gerada a partir da API oficial do IBGE; **não** é usado `municipios_mapeados.csv` nem `eleicoes_2026_municipios.csv`.

## Executar

```bash
python3 -m unittest discover -s tests -p 'test_base_tse_ibge.py' -v
python3 scripts/construir_base_tse_ibge.py
```

A saída fica em `data/tse_oficial/`: `eleicoes_2026.sqlite`, `validacao.json`, CSVs de seções, locais, municípios e candidatos (estes somente se todas as verificações passarem); CSVs de pendências de mapeamento e eleitorais.

**Política de bloqueio:** qualquer divergência de seção ou correspondência IBGE pendente bloqueia a exportação publicável. O SQLite intermediário permanece disponível para diagnóstico; jamais interpretar a existência do SQLite como aprovação dos dados. Cada execução exige diretório de saída vazio/novo; nada é sobrescrito.

**Limitações:** a correspondência territorial inicial usa UF + nome normalizado, não a tabela oficial de códigos cruzados TSE–IBGE. A verificação da tabela oficial de correspondências é etapa posterior, não deve ser presumida. O pipeline não usa arquivos estaduais que possam duplicar a base nacional nem dados do exterior. Na primeira execução nacional, ainda precisamos confirmar cobertura integral e validar formalmente os códigos especiais além de 95 e 96. O formato é SQLite+CSV, para evitar impor dependências não instaladas. Esta é uma implementação inicial ainda sem teste com os ZIPs reais.

**Importante:** não deletar bases antigas ou sobrescrever dados existentes nesta etapa. A decisão de não consumi-los pelo produto é diferente de apagar evidências preexistentes.
