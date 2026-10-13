# Pipeline mensal Novo Bolsa Família — primeira implementação

**Escopo:** competências janeiro de 2025 a setembro de 2026. **Banco próprio:** `data/beneficios/beneficios.sqlite`. Nenhum acesso de escrita à base TSE.

## Estrutura
- `origem`: um registro por competência, com hashes SHA-256 do ZIP e da ponte do Tesouro, contagens, totais e endereço da fonte.
- `parcelas_municipais`: uma linha por competência, referência e código IBGE, com valor em centavos e número de parcelas.
- Fonte bruta: ZIP de cada mês, mantido fora do Git em `data/raw/cgu/bolsa_familia/`.
- Ponte territorial: CSV oficial do Tesouro, sem cabeçalho (`SIAFI;CNPJ;NOME;UF;IBGE`), mantido fora do Git em `data/reference/siafi_ibge_tabmun.csv`.

**Fonte do ZIP:** `https://portaldatransparencia.gov.br/download-de-dados/novo-bolsa-familia/AAAAMM`  
**Fonte da ponte:** `https://www.tesourotransparente.gov.br/ckan/dataset/abb968cb-3710-4f85-89cf-875c91b9c7f6/resource/eebb3bc6-9eea-4496-8bcf-304f33155282/download/tabmun.csv`

A ponte é uma publicação histórica do Tesouro; cobertura de cada mês é verificada pelo pipeline. O código preserva a data de competência do arquivo e o mês de referência dos registros: não presume que ambos sejam iguais.

## Primeiro teste no Colab (fevereiro de 2025)

Para executar **no Colab**, clone o projeto atualizado do branch do PR #9 (o repositório pode ser privado; nesse caso faça checkout no Mac autenticado ou envie os scripts ao Colab via Drive). Com os scripts acessíveis no diretório raiz do projeto:

```python
!python -m unittest discover -s tests -p 'test_ingerir_bolsa_familia.py' -v
!python scripts/ingerir_bolsa_familia.py --mes 202502
```

O programa baixa automaticamente o ZIP oficial e a ponte caso não existam no caminho local. Pode reutilizar ZIP já baixado com `--zip /caminho/arquivo.zip`. O CSV de 2 GB não é extraído no disco nem carregado inteiro em memória; é lido em streaming, sem reter identificadores individuais.

Para conferir janeiro no mesmo pipeline, executar com seu ZIP verificado no Colab e relatório previamente produzido:

```python
!python scripts/ingerir_bolsa_familia.py --mes 202501 --zip /caminho/202501_NovoBolsaFamilia.csv.zip --esperado /caminho/validacao_bolsa_202501.json
```

Janeiro precisa reproduzir **20.500.422 parcelas**, **1.373.577.033.000 centavos**, **5.570 municípios IBGE**. A contagem de referências distintas é superior a um mês. `quantidade_parcelas` **não equivale a famílias únicas**; valores disponíveis não comprovam saque ou recebimento individual.

## Garantias e pendências

- Falha se alguma linha tem competência diferente, valor inválido, código SIAFI sem correspondência ou ZIP com CRC incorreto.
- Falha se as somas antes e depois da agregação/SQLite divergem.
- Recusa importação de competência já existente. **Não** substitui silenciosamente snapshots.
- Banco SQLite não contém CPF, NIS ou nomes; o ZIP original ainda contém dados pessoais e deve ser protegido e não publicado.
- Implementação e testes sintéticos estão versionados, **mas ainda não foram executados neste ambiente**. Primeiro rodar os testes e um mês real antes de tratar a automação como validada.
- A lacuna entre 5.570 municípios no Bolsa Família e 5.571 na base TSE ainda não está diagnosticada; não preencher com zero sem evidência.
- A ingestão preserva a ponte SIAFI–IBGE separadamente (hash); é necessário registrar histórico de revisões e verificar estabilidade para uso em série.
- Não executar os 21 meses em paralelo nem iniciar nova ingestão enquanto a primeira real não passar.

## Próxima verificação

Testar fevereiro, registrar totais e códigos únicos, conferir a cardinalidade de cada arquivo e a presença territorial no cadastro IBGE. Depois criar atualização mês a mês com relatório por competência e verificação de cobertura histórica.
