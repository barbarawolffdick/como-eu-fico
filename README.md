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

## Consulta Next.js sem FastAPI remoto

A busca, o detalhe municipal e o ranking em `/explorar` agora usam snapshots JSON versionados em `data/public/`. Não exigem URL do FastAPI no v0. Os snapshots são derivados do SQLite existente pelo workflow `Atualizar dados web`, após validação de 5.571 municípios, e atualizados automaticamente quando `data/app/como_eu_fico.sqlite` é publicado na `main`.

**Limitação atual:** o SQLite publicado no GitHub pode estar atrasado em relação ao arquivo do Mac. O indicador por habitante só será liberado quando a versão publicada tiver população IBGE nos 5.571 municípios. A interface não deve apresentar cobertura de beneficiários como se fosse valor por habitante.

## Frontend Next.js para v0

A raiz do repositório agora é também uma aplicação **Next.js App Router**, com `package.json`, `app/page.tsx` e `app/api/[...path]/route.ts`. O código Python em `app/server.py` permanece independente e conserva o acesso oficial ao SQLite.

**Desenvolvimento local com dados reais:** execute o FastAPI em `127.0.0.1:8001` como documentado acima. Em outro terminal na raiz:

```bash
npm install
cp .env.example .env.local
npm run dev
```

Abra `http://localhost:3000`. A rota Next.js `/api/municipios` encaminha solicitações à API Python indicada por `FASTAPI_BASE_URL`; nomes, valores e votos vêm somente do SQLite real.

**No v0:** importe a branch `main` do GitHub e execute como projeto Next.js. A interface visual renderiza sem banco. Para buscas e resultados reais, configure `FASTAPI_BASE_URL` com uma URL HTTP(S) **que o servidor Next.js do v0 consiga alcançar**. `http://127.0.0.1:8001` do Mac não é acessível dentro do v0. Não há mock de dados reais e não existe hospedagem configurada. Sem essa URL, as consultas mostram uma mensagem explícita de API não configurada.

Assim, podemos editar e visualizar a interface no v0 **sem migrar ou duplicar** os pipelines TSE/CGU/IBGE. O app completo com consultas permanece funcional localmente com FastAPI + SQLite + Next.js.

## MVP local — execução oficial

A aplicação funcional é **FastAPI + SQLite**. A interface web já está servida pelo próprio FastAPI em `app/server.py`. Não se trata de um app React/Next.js e o v0 não consegue inicializar diretamente esse backend nem substituir o SQLite real.

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

A página web exibe a população quando disponível e informa quando ainda não foi carregada. Publicação/hospedagem permanecem fora do escopo.
