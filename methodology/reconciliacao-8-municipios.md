# Reconciliação: oito municípios brasileiros

Escopo fixo: Cristópolis (BA), Piedade dos Gerais e Santa Cruz de Minas (MG), Cachoeira do Piriá (PA), Alvorada do Sul (PR), Cambuci, Piraí e Trajano de Moraes (RJ).

```bash
python3 -m unittest discover -s tests -p 'test_reconciliar_8_municipios.py' -v
python3 scripts/reconciliar_8_municipios.py
```

Saídas em `data/quality/`: `reconciliacao_8_municipios.csv` e `votaveis_8_municipios.json`.

O script confronta o CSV original consolidado com os arquivos nacionais oficiais do TSE por (UF, nome municipal normalizado) **somente após confirmar cobertura de seções e código eleitoral não ambíguo**. Não supõe igualdade entre código IBGE e código TSE. Interrompe diante de seleção inesperada, registros duplicados ou campos inválidos. Preserva arquivos originais.

As divergências de votos de Lula/Flávio só são calculadas quando a identificação do respectivo nome é inequívoca e todas as seções dos arquivos de votação e detalhamento coincidem. Os **votos válidos permanecem INCONCLUSIVOS** até validação da categoria de votos com a documentação oficial, e o script exporta catálogo de demais votáveis para permitir essa verificação sem inventar categorias.

Os testes usam fixtures sintéticas, não substituem conferência do resultado real.
