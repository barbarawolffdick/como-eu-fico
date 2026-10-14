# Auditoria longitudinal do Bolsa Família

Período: 202501–202608. Resultado do relatório executado no Colab: PASS, sem alertas.

- 20 competências; 387.119.228 parcelas; R$ 260.005.670.043,00 em valores registrados.
- 5.571 municípios distintos. Única mudança de cobertura entre competências consecutivas: entrada do município IBGE 5101837 em 202510; nenhum saiu.
- Parcela com referência anterior à competência: janeiro/2025 120.400 (0,5873%); janeiro/2026 865.053 (4,4407%); agosto/2026 30.794 (0,1637%).
- Não foram detectados grupos municipais de soma zero ou negativa.

Limites: são parcelas, não famílias únicas. Referência anterior não comprova atraso. A auditoria territorial compara os próprios registros, não valida externamente o IBGE. A execução foi feita no Colab; o relatório foi compartilhado com a análise. Setembro/2026 não está incluído. Não inferir causalidade de variações mensais.

Próximo passo: camada analítica agregada por competência e código IBGE, com trilha de origem e recorte por referência preservados.