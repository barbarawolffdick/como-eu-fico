# Banco de dados do Como Eu Fico (MVP)

O aplicativo tem **um banco operacional SQLite** em `data/app/como_eu_fico.sqlite`, criado por `app/database.py`. Ele é **derivado** das fontes independentes e auditadas, sem alterar os dados originais.

## Estrutura do app

- `municipios`: código IBGE de sete dígitos, nome/UF quando presentes no snapshot; campos reservados para população e ano IBGE, ainda não carregados sem fonte verificada.
- `votos_presidenciais`: primeiro turno presidencial de 2026, candidato, votos e metadados TSE originais por município.
- `bolsa_familia`: parcelas e valores em centavos por município, mês de competência e mês de referência.
- `bolsa_familia_mensal`: consulta pronta para o produto com agregação por competência.
- `origem_dados`: identificação dos arquivos usados na montagem do banco.

O banco não deve inventar população, votos ou valores inexistentes. Os arquivos municipais do TSE devem ter `validacao.json` com os três controles PASS definidos no pipeline eleitoral. A carga verifica a composição dos votos e a reconciliação das parcelas por competência no SQLite CGU.

## Criar o banco com os arquivos já existentes

O snapshot TSE **ainda não foi localizado versionado em GitHub**; o backup consolidado do Bolsa Família está no Mac. A partir da raiz do repositório, **após disponibilizar os dois**:

```bash
python3 -m unittest discover -s tests -p 'test_banco_app.py' -v
python3 app/database.py --tse data/curated/eleicoes_2026_t1 --bolsa /CAMINHO/REAL/beneficios_ate_202608.sqlite --saida data/app/como_eu_fico.sqlite
```

O segundo comando **cria o banco somente se o destino ainda não existir**. A fonte CGU é aberta em modo leitura. Não refazer o processamento nacional de 20 meses.

## Próximo desenvolvimento do produto

1. Confirmar os arquivos reais do snapshot TSE e do SQLite CGU e executar **uma única carga** do banco.
2. Ligar a busca municipal e as consultas da aplicação a `municipios`, `votos_presidenciais` e `bolsa_familia_mensal`.
3. Incorporar nome e população IBGE a partir de fonte verificada; não usar população fictícia.
4. Definir armazenamento/deploy persistente para o banco e a aplicação web.

O SQLite gerado não está incluído neste PR porque os **dados reais necessários não estão disponíveis no repositório**. Isso não equivale a dizer que o banco foi povoado.
