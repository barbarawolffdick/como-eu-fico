# Auditoria de locais de votação

Varre os painéis HTML em `dados-municipios/*/municipios_*/*/painel_*.html` e examina cada linha da tabela `data-unidade="locais"`. Não altera arquivos originais.

```bash
python3 scripts/auditar_locais.py
```

Produz:
- `data/quality/inconsistencias_locais.csv`: uma linha por regra violada e local
- `data/quality/resumo_locais.json`: totais nacionais e por tipo de inconsistência

Regras: `validos > aptos`, `lula > validos`, `flavio > validos`, `lula + flavio > validos`, ausência de valores numéricos e painéis sem tabela de locais. Um mesmo local pode aparecer em mais de uma regra. O programa sai com código 1 quando identifica alertas (o relatório é gerado mesmo assim).

**Escopo:** checagem aritmética de dados já publicados nos HTMLs. Ela não verifica a procedência dos votos nem detecta erros plausíveis internamente. O próximo passo é reconciliar com a votação oficial do TSE por seção/candidato e revisar o pipeline gerador. Valores dos demais candidatos não estão incluídos nesta verificação.
