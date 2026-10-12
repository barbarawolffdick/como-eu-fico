# Primeira auditoria do Novo Bolsa Família

Fonte: [CGU — Novo Bolsa Família](https://portaldatransparencia.gov.br/download-de-dados/novo-bolsa-familia) e [dicionário de campos](https://portaldatransparencia.gov.br/dicionario-de-dados/novo-bolsa-familia).

**Fase atual: validador pronto, NÃO há amostra oficial processada nem base histórica construída.**

O Portal descreve arquivos mensais e os campos `MÊS COMPETÊNCIA`, `MÊS REFERÊNCIA`, `CÓDIGO MUNICÍPIO SIAFI` e `VALOR PARCELA`. A origem informa o Novo Bolsa Família disponível desde março de 2023. A disponibilidade de cada mês e a defasagem devem ser conferidas ao baixar.

## Rodar com um ZIP real

1. Abra https://portaldatransparencia.gov.br/download-de-dados/novo-bolsa-familia
2. Escolha, por exemplo, **janeiro de 2024** e baixe o ZIP oficial. **Não faça upload público do CSV**: pode conter CPF, NIS e nomes.
3. Rode o validador localmente, substituindo o caminho:

```bash
python3 -m unittest discover -s tests -p 'test_auditar_amostra_bolsa_familia.py' -v
python3 scripts/auditar_amostra_bolsa_familia.py "/caminho/para/arquivo.zip" --mes 202401
```

O arquivo agregado local `data/quality/bolsa_familia_amostra.json` não contém CPFs, NIS nem nomes. Guarda totais monetários em **centavos inteiros**, contagem de **parcelas** (não de famílias), mês da folha, competências encontradas, municípios SIAFI, erros amostrais e SHA-256 do arquivo original. A auditoria exige mês da folha igual ao informado em todas as linhas e bloqueia valores não numéricos.

O script não utiliza e não altera a base eleitoral. Ainda não converte códigos SIAFI em IBGE. O artefato não é uma base publicada; é somente a primeira verificação empírica.

**Atenção:** parcelas disponibilizadas não equivalem necessariamente a saques ou valores efetivamente recebidos. Contagem de parcelas não é contagem de famílias. O relatório não deve ser enviado para análise eleitoral antes da correspondência territorial oficial e de verificações adicionais.
