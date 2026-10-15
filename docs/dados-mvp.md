# Banco de dados do Como Eu Fico (MVP)

> Este documento descreve a montagem histórica do backend Python. Para o estado operacional atual, consulte o README e `docs/deploy-vercel.md`: Next.js usa `data/public/`, com população publicada nos 5.571 municípios. As pendências de carga abaixo registram uma etapa anterior.

O aplicativo tem **um banco operacional SQLite** em `data/app/como_eu_fico.sqlite`, criado por `app/database.py`. Ele é **derivado** das fontes independentes e auditadas, sem alterar os dados originais.

## Estrutura do app

- `municipios`: código IBGE de sete dígitos, nome/UF quando presentes no snapshot; campos reservados para população e ano IBGE, ainda não carregados sem fonte verificada.
- `votos_presidenciais`: primeiro turno presidencial de 2026, candidato, votos e metadados TSE originais por município.
- `bolsa_familia`: parcelas e valores em centavos por município, mês de competência e mês de referência.
- `bolsa_familia_mensal`: consulta pronta para o produto com agregação por competência.
- `origem_dados`: identificação dos arquivos usados na montagem do banco.

O banco não deve inventar população, votos ou valores inexistentes. Os arquivos municipais do TSE devem ter `validacao.json` com os três controles PASS definidos no pipeline eleitoral. A carga verifica a composição dos votos e a reconciliação das parcelas por competência no SQLite CGU.

## Criar o banco com os arquivos já existentes

O banco pode ser criado **com a CGU imediatamente**, e passa a incluir os votos quando o snapshot TSE for disponibilizado. Da raiz do repositório:

```bash
python3 -m unittest discover -s tests -p 'test_banco_app.py' -v
python3 app/database.py --tse data/curated/eleicoes_2026_t1 --bolsa /CAMINHO/REAL/beneficios_ate_202608.sqlite --saida data/app/como_eu_fico.sqlite
```

O segundo comando **cria o banco somente se o destino ainda não existir**. A fonte CGU é aberta em modo leitura. Não refazer o processamento nacional de 20 meses.

## Próximo desenvolvimento do produto

1. Usar o backup real CGU já verificado para carregar o banco do app; conferir 20 competências e 420.697 agregados. Obter o snapshot municipal validado TSE para carregar votos sem refazer ingestão nacional.
2. A aplicação `app/server.py` disponibiliza busca municipal, votos e série CGU em API e página web. Executar com `pip install fastapi uvicorn` e `uvicorn app.server:app`; apontar `COMO_EU_FICO_DB` para o banco do aplicativo.
3. Incorporar nome e população IBGE a partir de fonte verificada; não usar população fictícia.
4. Definir armazenamento/deploy persistente para o banco e a aplicação web.

O SQLite consolidado real da CGU foi localizado entre os arquivos da conversa e usado para gerar o banco operacional local, com 5.571 municípios, 20 competências e 420.697 registros. O binário não foi commitado no GitHub, porque o conector de edição de arquivos não aceita SQLite. O snapshot municipal do TSE e a população IBGE ainda precisam ser carregados. Nenhum voto/população foi inventado.
