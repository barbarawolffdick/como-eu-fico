# Etapa: correspondência oficial TSE–IBGE e diagnósticos independentes

O TSE publica uma tabela de correspondência dos códigos TSE e IBGE, em seu catálogo de dados abertos:
https://dadosabertos.tse.jus.br/dataset/codigos-oficiais-de-uf-e-municipios-segundo-o-tse-e-o-ibge

A primeira implementação é **conservadora**, em duas partes:

1. `scripts/inspecionar_correspondencia_tse_ibge.py` faz download do ZIP oficial, registra SHA-256, lista arquivos/colunas e uma amostra. **Ainda não aplica a correspondência**, até confirmar o esquema observado.
2. `scripts/diagnosticar_base_tse.py` lê o SQLite nacional existente em modo somente leitura, identifica de forma **independente** problemas de composição eleitoral e de local de votação. A saída de diagnóstico é `data/tse_oficial/diagnostico_independente.json`. Não libera publicação e não modifica o banco.

## Testes e execução

```bash
python3 -m unittest discover -s tests -p 'test_diagnostico_tse_ibge.py' -v
python3 scripts/inspecionar_correspondencia_tse_ibge.py
python3 scripts/diagnosticar_base_tse.py
```

**Não reexecutar** `construir_base_tse_ibge.py` sobre o banco existente; esta etapa usa o SQLite já produzido. Não alterar manualmente os 13 municípios nem dispensar os alertas dos locais. A comparação dos códigos oficiais será implementada quando tivermos o inventário real do arquivo TSE e seus cabeçalhos.

A existência da tabela oficial está confirmada, mas sua edição catalogada é de 2025; a cobertura dos códigos utilizados na eleição de 2026 ainda deverá ser testada.
