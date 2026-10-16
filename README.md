# Como Eu Fico

Projeto de conscientização política através de dados, conectando o voto da cidade à evolução das políticas públicas e às condições de vida da população.

**Entenda como sua cidade vota e o que muda na vida de quem mora nela.** Acompanhe recursos, serviços e benefícios públicos ao longo do tempo, com dados para formar sua própria opinião.

## Direção editorial e contrato de dados

O **Como Eu Fico** tem a cidade como centro da experiência e o resultado eleitoral como referência permanente. O objetivo de longo prazo é investigar como a presidência impacta — ou não — a vida das pessoas e como linhas políticas se relacionam com a percepção de valor das políticas públicas, sem antecipar conclusões que os dados ainda precisam sustentar.

O produto se organiza em três camadas:

| Camada | O que o cidadão deve encontrar |
|---|---|
| Voto | Como a cidade votou, com distribuição de votos, percentuais e contexto eleitoral. O placar eleitoral deve permanecer no panorama municipal e acompanhar as análises pertinentes. |
| Vida cotidiana | Evolução de recursos, benefícios, estrutura, serviços e resultados observáveis, conforme a disponibilidade e a definição de cada fonte. |
| Relações e percepções | Análises sobre convergências e diferenças entre voto, políticas públicas e percepção de valor. A investigação de percepção depende de evidências próprias, como pesquisas, ainda a integrar e validar. |

As principais jornadas são:

- **Entender minha cidade:** como votou, quais políticas estão presentes e o que mudou.
- **Acompanhar uma gestão:** o que aconteceu durante o mandato em diferentes áreas e territórios.
- **Investigar uma relação:** se cidades com perfis eleitorais diferentes tiveram trajetórias diferentes.
- **Conferir uma afirmação:** qual dado sustenta uma leitura, em qual período e com quais limites.

A evolução das políticas, serviços, benefícios e entregas com participação federal é acompanhada na frequência efetivamente disponível em cada fonte. O primeiro turno presidencial de 2026 é a referência fixa das análises iniciais. Evolução durante um mandato, responsabilidade de cada esfera de governo e impacto demonstrado são conceitos distintos: uma associação não demonstra causalidade. Votos agregados não revelam motivações individuais nem medem diretamente a percepção de valor.

- [Contrato editorial e de dados v1 — direção de produto atualizada em 15/10/2026](docs/contrato-editorial-dados-v1.md)
- [Protocolo de evidências e interpretação](methodology/protocolo-evidencias.md)
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

- `/`: apresentação do produto, busca municipal, variação regional de famílias beneficiárias e ranking de alcance populacional do Bolsa Família.
- `/cidade/{codigo_ibge}`: panorama municipal com placar eleitoral, recursos federais de saúde e alcance do Bolsa Família; aprofundamento por tema e fontes. Links antigos `/?municipio={codigo_ibge}` redirecionam para esse endereço.
- `/comparar`: duas cidades lado a lado em voto, dinheiro federal para saúde, vagas ocupadas do Mais Médicos, alcance e valores do Bolsa Família. As buscas, a inversão e o modo total/por habitante ficam preservados no link (`a`, `b`, `modo`).
- `/explorar`: exploração por Bolsa Família, Saúde e Voto, com filtros de região, estado e resultado eleitoral, ordenação, paginação e seleção de duas cidades para comparar. Veja as [regras da exploração nacional](docs/explorar-brasil.md).
- `/analises`: comparações territoriais descritivas.
- `/fontes` e `/api/fontes`: períodos, unidades, ausências, URLs e hashes SHA-256 dos snapshots em uso.

O [sistema de design](docs/design-system.md) é compartilhado por todas essas telas: tokens semânticos, controles, cards, tabelas, mensagens e indicadores. Consulte-o antes de criar ou alterar componentes. `npm run lint` também verifica os padrões da interface.

A navegação principal aparece no topo de todas as páginas. Na cidade, o menu de temas acompanha a rolagem na ordem Panorama, Saúde, Bolsa Família, Eleição 2026 e Fontes. Busca e troca de cidade aceitam teclado. A entrada usa somente snapshots publicados: a variação regional compara as somas de famílias nos municípios com observações nos dois períodos e informa cobertura incompleta; o ranking apresenta os cinco maiores percentuais de moradores em famílias beneficiárias entre cidades com dado disponível, independentemente do resultado eleitoral. Veja a [arquitetura da experiência municipal](docs/experiencia-municipal.md).

A [comparação entre cidades](docs/comparacao-cidades.md) começa com São Paulo e Rio de Janeiro como exemplo substituível e valores monetários por habitante. A página municipal oferece acesso com a cidade atual já selecionada. Valores do Bolsa Família usam o último mês comum às duas séries; diferenças e barras comparativas só aparecem quando os períodos e as referências necessárias são compatíveis. Ausência não vira zero.

**Cobertura publicada:** população IBGE 2026 nos 5.571 municípios; pessoas em famílias beneficiárias MDS nos 5.571 municípios, competência setembro de 2026. As seis ausências cartográficas foram completadas por consulta tabular oficial e o total reconciliado com o Brasil. Ausências futuras continuam indisponíveis, nunca zero. Famílias MDS têm observações em janeiro/2025 e agosto/2026. A série CGU vai de janeiro/2025 a agosto/2026, com cobertura histórica variável por município; os rankings financeiros usam janeiro–agosto/2026.

**Leitura rápida dos snapshots.** `npm run build` e `npm run dev` executam antes `npm run dados:derivar` (`scripts/fragmentar_snapshots.mjs`), que gera `data/derivados/` a partir de `data/public/`: fragmentos por UF de detalhes, saúde e financiamento, índice de busca sem acentos, projeção enxuta para a exploração e manifesto com SHA-256 e cabeçalhos de cada snapshot. Os derivados não são versionados nem editados; `data/public/` continua sendo a única fonte. Cada arquivo é interpretado uma vez por processo (`lib/snapshots.ts`), e as respostas da API levam `Cache-Control` para a CDN, renovada a cada deploy. Depois de republicar um snapshot com o `npm run dev` aberto, execute `npm run dados:derivar` e reinicie o servidor.

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

## Saúde na página da cidade — cobertura nacional

A seção Saúde está disponível para os 5.571 municípios do cadastro. `/api/saude/{codigo_ibge}` consulta `data/public/saude_municipal.json` e entrega somente os indicadores da cidade selecionada. Cobertura por indicador é distinta de cobertura da consulta:

- FNS: repasses líquidos de Atenção Primária, janeiro–julho/2026, validados para 5.569 fundos municipais. Brasília e Fernando de Noronha permanecem sem repasse municipal validado no recorte. Fundos estaduais/distrital ficam separados; não somamos saldos bancários nem rateamos recursos estaduais.
- APS: equipes homologadas e financiadas nos 5.571 municípios, parcela outubro/2026, cadastro CNES agosto/2026.
- Mais Médicos: consolidado de 09/10/2026 para os 5.571 municípios. Mede **vagas ocupadas no provimento federal**, incluindo instituições vinculadas. Registros estaduais e DSEI não são atribuídos às cidades. Zeros expressos pela fonte são preservados; ausência permanece nula.

Fonte, data e limites aparecem em cada cartão. Veja a [metodologia nacional](methodology/saude-nacional.md). A aplicação serve o snapshot validado; não consulta fontes oficiais ao abrir uma cidade. Não há projeção nem inferência causal.

Para reproduzir:

```bash
pip install -r requirements-dados.txt
python -m scripts.publicar_saude_nacional
python -m unittest discover -s tests -p 'test_saude*.py' -v
```

O cache `data/raw/saude/nacional/` preserva os arquivos brutos e metadados com SHA-256. A coleta usa uma planilha FNS, a lista de parcelas, um relatório nacional APS e um ZIP agregado do Mais Médicos; não realiza milhares de consultas municipais. `--atualizar` renova respostas; sem a opção, a execução retoma os arquivos já verificados. A publicação é atômica após os controles das três fontes. Nenhuma ingestão TSE/CGU é reexecutada.

O snapshot e a [metodologia do piloto](methodology/saude-piloto.md) foram preservados como histórico, sem uso nas rotas públicas atuais.

## Financiamento e rede municipal de saúde

A página da cidade apresenta o total federal fundo a fundo de todas as áreas, valor por habitante, grupos/finalidades, emendas identificadas dentro do total e evolução nominal entre os anos completos de 2024 e 2025. O parcial de 2026 (até julho) fica separado. Despesas SIOPS de 2025 são apresentadas por fonte e por fase (liquidadas/pagas), sem serem tratadas como receitas. CNES acrescenta unidades, UBS/postos, hospitais/leitos e equipamentos, com datas e recortes próprios. Valores da AgSUS sediada em Brasília não integram os repasses municipais, mesmo quando a planilha os classifica como municipais.

Reprodução: `python -m scripts.publicar_financiamento_saude`, com `requirements-dados.txt`. O cache `data/raw/saude/expansao/` permite reutilizar as fontes verificadas; `--atualizar` renova a coleta. O novo snapshot é `data/public/financiamento_saude.json`; veja [método, fontes e limites](methodology/financiamento-saude.md). Não exige novas ingestões eleitorais ou do Bolsa Família.
