# Primeira auditoria do Novo Bolsa Família

Fonte: [CGU — Novo Bolsa Família](https://portaldatransparencia.gov.br/download-de-dados/novo-bolsa-familia) e [dicionário de campos](https://portaldatransparencia.gov.br/dicionario-de-dados/novo-bolsa-familia).

**Recorte inicial: janeiro de 2025 a setembro de 2026 (21 competências mensais), condicionado à disponibilidade oficial.** A eleição presidencial de 2026 é a referência analítica, não um dado mensal.

**Fase atual: validador pronto, NÃO há amostra oficial processada nem base histórica construída.**

O Portal descreve arquivos mensais e os campos `MÊS COMPETÊNCIA`, `MÊS REFERÊNCIA`, `CÓDIGO MUNICÍPIO SIAFI` e `VALOR PARCELA`. A origem informa o Novo Bolsa Família disponível desde março de 2023. A disponibilidade de cada mês e a defasagem devem ser conferidas ao baixar.

## Rodar com um ZIP real

1. Abra https://portaldatransparencia.gov.br/download-de-dados/novo-bolsa-familia
2. Escolha, por exemplo, **janeiro de 2025** e baixe o ZIP oficial. **Não faça upload público do CSV**: pode conter CPF, NIS e nomes.
3. Rode o validador localmente, substituindo o caminho:

```bash
python3 -m unittest discover -s tests -p 'test_auditar_amostra_bolsa_familia.py' -v
python3 scripts/auditar_amostra_bolsa_familia.py "/caminho/para/arquivo.zip" --mes 202501
```

O arquivo agregado local `data/quality/bolsa_familia_amostra.json` não contém CPFs, NIS nem nomes. Guarda totais monetários em **centavos inteiros**, contagem de **parcelas** (não de famílias), mês da folha, competências encontradas, municípios SIAFI, erros amostrais e SHA-256 do arquivo original. A auditoria exige **mês de competência** igual ao período informado, mas preserva cada mês de referência original e aceita referências anteriores. Bloqueia valores não numéricos.

O script não utiliza e não altera a base eleitoral. Ainda não converte códigos SIAFI em IBGE. O artefato não é uma base publicada; é somente a primeira verificação empírica.

**Atenção:** parcelas disponibilizadas não equivalem necessariamente a saques ou valores efetivamente recebidos. Contagem de parcelas não é contagem de famílias. O relatório não deve ser enviado para análise eleitoral antes da correspondência territorial oficial e de verificações adicionais.

## Primeira amostra processada no Google Colab (202501)

Arquivo original informado pelo Colab: ZIP com CRC aprovado, SHA-256 `e4fa571d52a60e5dc8a7e961d96f7e7aef49fb1703c9350824860482384e8762`. CSV municipal recebido e conferido: **19.337 grupos**, **20.500.422 parcelas**, soma de **R$ 13.735.770.330,00**, **5.570 municípios SIAFI** reportados pelo processamento inicial. A competência foi `202501` em todos os registros, e o mês de referência varia entre `202308` e `202501`. Os valores representam parcelas listadas na fonte, não famílias únicas nem saques efetivos. A correspondência SIAFI–IBGE ainda não foi validada. Os testes automatizados do script corrigido ainda exigem execução no ambiente de desenvolvimento.
