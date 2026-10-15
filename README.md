# Como Eu Fico

Projeto de análise eleitoral e indicadores públicos por município brasileiro.

## Direção editorial e contrato de dados

O **Como Eu Fico** mostra, no nível municipal, a presença das políticas, serviços, benefícios e entregas com participação federal na vida cotidiana. Acompanha sua evolução **mês a mês**, tendo o resultado da eleição presidencial de 2026 como referência fixa para análises descritivas; uma associação não demonstra causalidade.

- [Contrato editorial e de dados v1 (proposta)](docs/contrato-editorial-dados-v1.md)
- [Catálogo de fontes e questões em aberto](docs/catalogo-fontes-v0.md)

Cada domínio (eleições, benefícios, finanças, território e entregas) conserva dados independentes. Relacionamentos são efetuados em código, com chaves territoriais e regras temporais explícitas. Novas integrações dependem da revisão do contrato.

## Fonte de dados atual

- **Votação:** arquivos oficiais TSE 2026, primeiro turno, cargo Presidente.
- **Território:** tabela oficial de correspondência dos códigos TSE–IBGE e cadastro de municípios do IBGE.
- **Chave de integração:** `codigo_ibge` (sete dígitos).
- **Cobertura validada:** 5.571 municípios, 497.897 seções, nenhuma divergência de composição de votos.
- **Pendente:** 6.588 divergências entre códigos de locais de votação. Não produzir agregações por local como se estivessem conciliadas.

Nenhum cálculo do pipeline atual usa os antigos resumos eleitorais em `dados-municipios/`.

## Onde estão os dados

| Diretório | Significado |
|---|---|
| `data/raw/tse/2026/` | ZIPs originais do TSE; não editar |
| `data/reference/` | Cadastro do IBGE e tabela TSE–IBGE |
| `data/tse_oficial/eleicoes_2026.sqlite` | Banco de ingestão e auditoria |
| `data/tse_oficial/codigos_oficiais/` | Exportações municipais auditadas |
| `data/curated/eleicoes_2026_t1/` | **Snapshot canônico para o projeto** |
| `data/quality/` | Resultados históricos de verificações |

## Publicar o snapshot canônico

Depois de gerar e conferir os CSVs oficiais:

```bash
python3 -m unittest discover -s tests -p 'test_publicar_base_municipal.py' -v
python3 scripts/publicar_base_municipal.py
```

Saída: `data/curated/eleicoes_2026_t1/` contendo `municipios.csv`, `candidatos_municipios.csv`, `validacao.json` e `manifesto.json`, com hashes SHA-256. Os CSVs são somente municipais e foram conferidos contra os totais de votos nominais. A pasta de destino não pode existir antes da execução.

## Retirar dados eleitorais secundários do Git (sem excluir do Mac)

O diretório `dados-municipios/` contém 17.205 arquivos rastreados na auditoria de 12/10/2026. Não é consumido pelo pipeline TSE–IBGE e está no `.gitignore`.

```bash
python3 scripts/desvincular_dados_antigos.py
python3 scripts/desvincular_dados_antigos.py --apply
git diff --cached --stat
git commit -m "chore: desvincula resumos eleitorais antigos"
git push
```

A opção `--apply` executa `git rm --cached`: remove apenas os registros do índice Git e **mantém as cópias locais**. Requer branch `chore/consolidar-base-eleitoral` e árvore de trabalho limpa. A operação não deve ser repetida se já não houver arquivos rastreados. Esses arquivos serão excluídos do repositório numa futura integração do PR, mas continuam disponíveis localmente no Mac que executou o comando.

Os scripts antigos de leitura e reconciliação dos resumos foram removidos desta branch. Para reproduzir o novo pipeline, consulte os scripts oficiais TSE–IBGE.

## Inventário da limpeza

```bash
python3 scripts/inventariar_legado.py
```

O comando gera `inventario-limpeza.json` sem excluir nada. Antes de apagar ou mover qualquer caminho legado, confirmar a situação dos arquivos rastreados e não rastreados no Mac e a existência de outros consumidores do repositório.

Veja também `methodology/codigos-oficiais-tse-ibge.md`.

## Aplicação web — Next.js no v0/Vercel

A raiz é uma aplicação Next.js App Router. Busca, detalhe municipal, rankings, cobertura, análises e fontes consultam **somente os snapshots versionados em `data/public/`**. Não precisam de FastAPI remoto, SQLite, Git LFS ou variáveis de ambiente para funcionar na web.

```bash
# Node.js 22, como no CI e no deploy
npm ci
npm run lint
npm run build
npm run start
```

Abra `http://localhost:3000`. Para desenvolvimento: `npm run dev`.

- `/`: busca e detalhe municipal, votos e série CGU.
- `/explorar`: rankings financeiros e cobertura populacional, com filtros.
- `/analises`: comparações territoriais descritivas.
- `/fontes` e `/api/fontes`: períodos, unidades, ausências, URLs e hashes SHA-256 dos snapshots em uso.

**Cobertura publicada:** população IBGE 2026 nos 5.571 municípios; pessoas em famílias beneficiárias MDS em 5.565 municípios, competência agosto de 2026. Seis ausências ficam indisponíveis, nunca zero. Famílias MDS têm observações em janeiro/2025 e agosto/2026. A série CGU vai de janeiro/2025 a agosto/2026, com cobertura histórica variável por município; os rankings financeiros usam janeiro–agosto/2026.

Os JSONs de detalhe e rankings derivam do SQLite pelo workflow `Atualizar dados web`. Consultar a web não executa ingestões nem modifica fontes. `FASTAPI_BASE_URL` é opcional e serve apenas às rotas legadas do proxy; não apontar a Vercel para o localhost do Mac.

### Publicação e verificação

`vercel.json` fixa o preset **Next.js**, instalação com `npm ci` e build com `npm run build`. No projeto Vercel `barbaras-projects-f33a375a/como-eu-fico`, a raiz deve ser `.` e a branch de produção `main`. Manter o diretório de saída no padrão do Next.js; não usar o preset `Other` ou exigir uma pasta `public`. Ver [operação do deploy](docs/deploy-vercel.md).

O v0 deve sincronizar a versão desejada do GitHub. A branch `v0/project-overview-3a142983` pode conter mudanças próprias; não substituir a `main` por ela sem revisão. Os snapshots precisam acompanhar o código na prévia.

```bash
npx playwright install chromium
npm run test:web
```

Os testes abrem o app compilado na porta 3100, em desktop e celular, com os dados publicados. Exercitam busca, detalhe, ausência MDS, filtros, fontes e falhas de rede. A regressão da série incompleta remove uma observação real **somente em memória** e exige `null`. Para uma prévia acessível: `PLAYWRIGHT_BASE_URL=https://URL-DA-PREVIA npm run test:web` (com os mesmos snapshots). As simulações de falha de rede são restritas aos testes; nenhum dado fictício é publicado.

## Backend Python — pipeline e consultas locais

O backend **FastAPI + SQLite** em `app/server.py` permanece disponível para consultas locais e tarefas do pipeline. É independente do frontend Next.js descrito acima e não é necessário hospedá-lo para o MVP web.

O banco operacional `data/app/como_eu_fico.sqlite` está em **Git LFS**. É obrigatório baixar o conteúdo LFS real; o ponteiro de 133 bytes não é um banco SQLite. Nenhum processamento nacional de TSE ou Bolsa Família deve ser refeito.

Na raiz do repositório, no macOS:

```bash
git switch main
git pull --ff-only origin main
git lfs install
git lfs pull
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_integrar_fontes.py' -v
python -m unittest discover -s tests -p 'test_integrar_ibge_populacao.py' -v
python -m uvicorn app.server:app --host 127.0.0.1 --port 8001
```

Abra `http://127.0.0.1:8001/` (API em `/docs`). O terminal que executa uvicorn fica aberto. Se aparecer erro de porta ocupada, pare a instância anterior ou escolha outra porta.

Verificação inicial do banco, em **outro terminal** na raiz do repositório:

```bash
file data/app/como_eu_fico.sqlite
python3 -c "import sqlite3; c=sqlite3.connect('data/app/como_eu_fico.sqlite'); print(c.execute('PRAGMA integrity_check').fetchone()); print(c.execute('SELECT COUNT(*) FROM municipios').fetchone())"
curl -f http://127.0.0.1:8001/api/municipios?q=3550308
```

Se `file` indicar apenas texto ASCII ou ponteiro Git LFS, a etapa `git lfs pull` não foi concluída. Se o navegador apresentar falha, registre o traceback do processo uvicorn para identificar a causa real. O CI testa o código e sua importação; **não executa uma sessão FastAPI com o SQLite LFS real**.

### Integração da população municipal IBGE

A fonte contratada é a estimativa oficial de 1º de julho de 2026, IBGE SIDRA tabela 6579, variável 9324, prevista em [metodologia](methodology/ibge-populacao.md). O pipeline de extração já existe, e a carga do banco agora aceita diretamente o CSV produzido, usando seu `validacao.json` e hash SHA-256. Atualiza **somente** população e ano; não altera nome, UF, eleições nem Bolsa Família.

Após assegurar a presença local de `data/curated/eleicoes_2026_t1/` (os dados curated são deliberadamente ignorados pelo Git), execute uma única vez:

```bash
python scripts/integrar_ibge_populacao.py
python app/integrar_fontes.py --db data/app/como_eu_fico.sqlite --populacao data/curated/ibge_populacao_2026/municipios_populacao_2026.csv
python -c "import sqlite3; c=sqlite3.connect('data/app/como_eu_fico.sqlite'); print(c.execute('SELECT ano_populacao,COUNT(*) FROM municipios GROUP BY ano_populacao').fetchall())"
```

Se a extração SIDRA falhar por cobertura ou indisponibilidade, **não force a carga**. Se o CSV validado já existir, não execute o extrator de novo: execute apenas `app/integrar_fontes.py --populacao ...`. Depois de conferir a população em vários municípios e o resultado dos testes, versionar a atualização do SQLite via Git LFS.

A página web exibe a população quando disponível e informa quando ainda não foi carregada. O frontend publicado consulta os snapshots derivados, sem depender deste processo Python.

## Saúde na página da cidade — piloto

A consulta municipal inclui saúde para São Paulo, Recife, Sobral, Dourados e Boa Esperança do Norte. `/api/saude/{codigo_ibge}` consulta `data/public/saude_piloto.json`. Cidades fora da amostra são identificadas como fora do piloto, sem inferir inexistência de serviço.

- FNS: repasses líquidos do grupo Atenção Primária, janeiro–julho/2026. Fundos municipais e estaduais ficam separados; saldo em conta não é somado.
- APS: equipes homologadas e financiadas na parcela outubro/2026, com referência CNES agosto/2026.
- Mais Médicos: última observação agregada disponível em cada cidade. Ausências ficam indisponíveis, não zero.

Fonte, data e limites aparecem em cada cartão. A rastreabilidade e os critérios estão em [metodologia da saúde](methodology/saude-piloto.md). A aplicação não consulta APIs oficiais ao abrir uma cidade: serve o snapshot validado, como os demais domínios. Não há projeção nesta versão.

Para reproduzir: `pip install -r requirements-dados.txt` e `python scripts/publicar_saude_piloto.py`. O cache em `data/raw/saude/piloto/` preserva respostas brutas; `--atualizar` consulta novamente as fontes. `--fns-arquivo CAMINHO` reutiliza a planilha oficial já baixada. Nenhuma ingestão TSE/CGU é reexecutada.
