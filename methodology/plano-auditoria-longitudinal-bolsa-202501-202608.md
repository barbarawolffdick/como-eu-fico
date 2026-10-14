# Segunda auditoria: cobertura e temporalidade

**Estado:** script e teste unitário adicionados ao PR #9; **a execução sobre o SQLite nacional ainda está pendente**. Não tomar as análises abaixo como uma auditoria nacional já concluída.

## Base conhecida (auditoria estrutural no Colab)

O relatório estrutural `auditoria_bolsa_familia_202501_202608.json` retornou cinco testes PASS, 20 competências, 387.119.228 parcelas e R$ 260.005.670.043,00 em valores registrados.

A contagem mensal de códigos municipais distintos foi de 5.570 entre 202501 e 202509, passando a 5.571 de 202510 a 202608. Essa contagem não demonstra, sozinha, que apenas o município de Boa Esperança do Norte (IBGE 5101837) foi acrescido ou que todos os municípios anteriores permaneceram constantes.

## Testes novos

`scripts/auditar_serie_bolsa_familia.py` opera **somente em leitura** no SQLite agregado e emite um JSON contendo:

1. Série mensal de valores, parcelas e municípios.
2. Decomposição de parcelas e valores por `mes_referencia` para cada `mes_competencia`, incluindo proporção de referências anteriores.
3. Municípios que entram ou saem do conjunto em cada par de competências sucessivas (por código IBGE).
4. Primeira competência com registros de Boa Esperança do Norte (`5101837`).
5. Grupos agregados com valor zero/negativo, além de verificações de consistência.

A diferença `mes_referencia < mes_competencia` é **classificação temporal**, não evidência suficiente de parcela paga retroativamente. O script não identifica famílias únicas, irregularidades individuais, nem atribui causalidade para alterações nas séries.

## Execução reproduzível (Colab)

No diretório raiz do projeto, usar a versão do branch que contém o novo script:

```bash
python -m unittest discover -s tests -p "test_auditar_serie_bolsa_familia.py" -v
python scripts/auditar_serie_bolsa_familia.py --db data/beneficios/beneficios.sqlite
```

Se a sessão não contiver `data/beneficios/beneficios.sqlite`, restaurar o backup local `beneficios_ate_202608.sqlite` e passar seu caminho em `--db`. Preservar o SQLite original inalterado.

O arquivo de saída é `auditoria_longitudinal_bolsa_202501_202608.json`. Versionar no GitHub somente após a execução e revisão. Em seguida, cotejar conjuntos IBGE/TSE e validar amostras contra fontes independentes.

## Interpretação preliminar

Jan/2025: 20.500.422 parcelas, R$ 13.735.770.330,00. Ago/2026: 18.809.420 parcelas, R$ 12.763.249.759,00. Essa comparação de extremos **não** representa tendência ajustada, populações beneficiárias únicas, nem variação causal de políticas públicas.

Set/2026 segue pendente na fonte e não deve ser representado por zero.
