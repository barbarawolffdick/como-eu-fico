# Indicadores socioeconômicos — primeira integração

A primeira variável é **população residente estimada em 1º de julho de 2026**, série municipal do IBGE, SIDRA, tabela 6579 (variável 9324). É um indicador demográfico de referência, **não equivale a eleitores aptos ou votantes**. Fonte: https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-population.html e https://sidra.ibge.gov.br/tabela/6579

## Fonte eleitoral

O arquivo `data/curated/eleicoes_2026_t1/municipios.csv` já validado é lido, jamais alterado. A coluna de junção é `codigo_ibge` de sete caracteres. Dados ausentes, duplicados, não numéricos ou fora de 2026 interrompem a publicação.

## Execução

```bash
python3 -m unittest discover -s tests -p 'test_integrar_ibge_populacao.py' -v
python3 scripts/integrar_ibge_populacao.py
```

Saídas (nova pasta, não sobrescreve snapshot existente):
- `data/curated/ibge_populacao_2026/municipios_populacao_2026.csv`
- `data/curated/ibge_populacao_2026/sidra_6579_2026_raw.json` (resposta da API preservada)
- `data/curated/ibge_populacao_2026/validacao.json` (fonte, cobertura, hash)

O script só publica se os 5.571 códigos IBGE coincidirem exatamente e se a validação eleitoral anterior estiver em PASS. O formato é exclusivamente CSV+JSON para evitar bibliotecas adicionais. Para reproduzir sem internet, informar `--raw caminho.json`.

**Não comparar diretamente população estimada com votos para inferir causalidade**. A integração apenas estabelece uma referência populacional municipal para cálculos descritivos posteriores.

A primeira execução oficial ainda está pendente; não presumir cobertura antes de conferir a saída do Mac.
