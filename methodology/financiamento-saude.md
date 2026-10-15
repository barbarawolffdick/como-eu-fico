# Financiamento federal e estrutura na página da cidade

Implementação autorizada em 15/10/2026. Complementa os indicadores nacionais de [atenção primária e provimento](saude-nacional.md), sem substituí-los. Snapshot: `data/public/financiamento_saude.json`; chave: IBGE de sete dígitos. A consulta continua na página municipal e em `/api/saude/{codigo_ibge}`.

## Perguntas e medidas

- **Quanto chegou?** Soma líquida de todas as áreas das transferências fundo a fundo ao destinatário municipal, na planilha FNS de janeiro–julho/2026. Não representa todo gasto federal no território, transferências de outras modalidades ou recursos recebidos pelo estado.
- **Para quê?** Grupos financeiros da fonte e blocos de manutenção/estruturação. As partes reconciliam com o total; não somar os dois detalhamentos entre si.
- **Quanto por habitante?** Mesmo numerador municipal de 2026 dividido pela população IBGE 2026 já publicada. Arredondamento final em centavos, meio para cima. Sem denominador positivo ou numerador validado, indicador nulo. Não representa pagamento individual nem valor mensal ou anual projetado.
- **Está aumentando?** Variação nominal entre janeiro–dezembro/2024 e janeiro–dezembro/2025. O acumulado parcial de 2026 aparece separado. A planilha acumulada não permite obter janeiro–julho/2025 pela data da última liberação. Não comparamos períodos incompatíveis, não corrigimos inflação e não anualizamos o parcial.
- **Quanto veio de emendas?** Soma das estratégias com prefixo literal `EMENDA - ` e sua participação no total municipal do mesmo arquivo. É um subconjunto já incluído no total e nas áreas. Sem linhas identificadas, o indicador fica indisponível; isso não comprova inexistência de emendas. Não atribuímos autores nem afirmamos cobertura de todas as modalidades de emenda.
- **Como foi financiado o gasto municipal?** Despesas SIOPS de 2025, liquidadas e pagas separadamente, por fonte de financiamento. O percentual federal identifica somente a fonte de transferências federais fundo a fundo no total liquidado do mesmo exercício. Não é percentual de receita recebida ou de todo financiamento federal. Convênios e outras fontes não são atribuídos exclusivamente à União.
- **Que estrutura está localizada aqui?** Estabelecimentos ativos com atendimento ambulatorial SUS informado; UBS e postos; leitos de internação e UTI SUS; equipamentos em uso na rede total e estabelecimentos com equipamento SUS. Cada medida mantém seu período, unidade e recorte.

## Fontes verificadas

O [catálogo FNS](https://portalfns.saude.gov.br/downloads/) continua com 2026 acumulado até julho, além dos arquivos anuais de 2024 e 2025. A planilha de 2026 já baixada foi reutilizada, preservando o hash. A exportação de 2024 é CSV UTF-8, com valores monetários em formato brasileiro; 2025 e 2026 são XLSX. Nenhuma ingestão nacional TSE/CGU foi executada.

O [SIOPS — dados abertos](https://portalfns.saude.gov.br/siops/siops-downloads/) oferece despesas municipais de 2025, 6º bimestre. O ZIP publicado em julho/2026 contém CSV de 6.697.852 linhas, sem necessidade de descompactá-lo em disco ou carregá-lo inteiro em memória. O arquivo é uma exportação de **despesas**. O [catálogo de consulta pública](https://dadosabertos.saude.gov.br/dataset/siops) e seus metadados foram conferidos; as consultas documentadas de receitas/indicadores retornaram HTTP 404 nesta coleta. Por isso, não foi publicado gráfico de receitas ou participação da União em receitas municipais. A composição apresentada é explicitamente a das despesas declaradas por fonte de financiamento.

O [CNES — estabelecimentos](https://dadosabertos.saude.gov.br/dataset/cnes-cadastro-nacional-de-estabelecimentos-de-saude) oferece ZIP nacional CSV, com atualização de catálogo em 15/10/2026. O arquivo não traz competência mensal; a interface informa o momento de consulta e esse limite. O [arquivo de hospitais e leitos de 2026](https://dadosabertos.saude.gov.br/dataset/hospitais-e-leitos) contém competências de janeiro a agosto; selecionamos agosto/2026, sem somar estoques mensais.

A [consulta de equipamentos do DATASUS](https://tabnet.datasus.gov.br/cgi/deftohtm.exe?cnes/cnv/equipobr.def), ligada na página oficial de [recursos físicos CNES](https://datasus.saude.gov.br/cnes-recursos-fisicos/), oferece agosto/2026 como competência mais recente na coleta. Duas tabulações nacionais: município por equipamento selecionado, conteúdos `Equipamentos_em_Uso` e `Estab_c/_Equip_SUS`. São seis tipos selecionados pelo próprio DATASUS: mamógrafo, raio X, tomógrafo, ressonância, ultrassom e equipo odontológico. Não constituem inventário de todos os equipamentos.

## Controles e território

**FNS:** código e UF conciliados; `ST_FAF=S`; esfera original preservada no bruto; unicidade por município/bloco/grupo/estratégia/destinatário/conta; centavos inteiros; liberação dentro do ano e intervalo declarado. Não somar saldos bancários, repetir a atenção primária no total ou somar emendas novamente. Uma linha de 2024 sem bloco é mantida em “Bloco não informado na fonte”, sem atribuir finalidade.

A planilha 2026 classifica oito linhas da **Agência para o Desenvolvimento da Atenção Primária à Saúde**, sediada em Brasília, como `MUNICIPAL`. A identificação do destinatário demonstra que não se trata de fundo municipal. Há também seis linhas estaduais para a mesma agência. As 14 linhas, totalizando R$ 9.308.544,00, são publicadas em `outros_destinatarios_sediados_na_cidade`, com as esferas originais preservadas. Os valores ficam fora dos totais municipal e estadual/distrital e do indicador por habitante. Outros destinatários municipais exigem identificação explícita de fundo, FMS, município ou prefeitura; nomes inesperados interrompem a publicação para revisão. Os nomes dos destinatários e as linhas financeiras permanecem rastreáveis.

**SIOPS:** selecionar apenas `Codigo=3.0.00.00.00.00` (corrente) ou `4.0.00.00.00.00` (capital), para `Despesas Liquidadas` e `Despesas Pagas`, sem somar filhos contábeis, dotações, empenhos ou restos a pagar como novos gastos. Categorias de fonte são classificadas explicitamente, preservando seus nomes oficiais; novas categorias interrompem a publicação. Município, UF, exercício, homologação e unicidade por fonte/subfunção/código/fase são validados. Homologação e transmissão são preservadas por cidade. As despesas podem usar saldos de exercícios anteriores e não são conciliadas automaticamente com repasses FNS. Brasília e Fernando de Noronha não são preenchidos com orçamento estadual ou zero quando faltam no arquivo municipal.

**Estabelecimentos:** CNES único; código e UF compatíveis; sem motivo de desativação e `CO_AMBULATORIAL_SUS=SIM`. UBS: tipo 02; postos: tipo 01. Conta todos os estabelecimentos do recorte e exibe até dez unidades, com limite explícito e ligação ao cadastro oficial. Gestão do estabelecimento não é confundida com propriedade ou origem federal do dinheiro. No DF, códigos administrativos locais com UF 53 são agregados ao território representado por Brasília (`5300108`) no cadastro IBGE do produto; os códigos originais e contagens dessa exceção ficam na validação. Isso é agregação de localização no DF, não conversão de recurso distrital em municipal.

**Leitos:** usar somente competência 202608, CNES único, código/UF e situação cadastral validados. `LEITOS_SUS` e `UTI_TOTAL_SUS` são apresentados separadamente. Zero explicitamente registrado é mantido; município sem linha permanece indisponível. Hospital e leito cadastrado não significam vaga livre ou atendimento exclusivo dos moradores da cidade. A lista de hospitais também é limitada a dez na interface, com contagem total explícita.

**Equipamentos:** parâmetros exatos do POST estatístico, resposta bruta e hash preservados. O POST somente consulta tabelas públicas. Exigir competência, colunas, códigos únicos e reconciliação de cada coluna com o total nacional. Categorias ignoradas não são atribuídas a cidades. Traços publicados ficam nulos, nunca preenchidos com zero. A primeira coluna conta equipamentos em uso da rede total, pública e privada; a segunda conta estabelecimentos com equipamento SUS. Não somar as colunas nem tratar estabelecimentos como quantidade de aparelhos. Não atribuir compras à União sem vínculo documental.

## Reprodução e publicação

```bash
pip install -r requirements-dados.txt
python -m scripts.publicar_financiamento_saude
python -m unittest discover -s tests -p 'test_saude*.py' -v
```

Cache: `data/raw/saude/expansao/`, ignorado pelo Git. Fontes HTTP e consultas Tabnet têm URL, SHA-256 e momento de extração/reutilização; Tabnet também tem método e parâmetros. Sem `--atualizar`, reutiliza as respostas verificadas. Saída temporária só substitui o snapshot após todos os controles. `/api/fontes` lista o novo snapshot, hashes, fontes e cobertura. O navegador recebe somente a cidade selecionada, não os arquivos nacionais.

As páginas mantêm dados observados, períodos e limites junto a cada medida. Não há projeção, estimativa de atendimento regional, residência de pacientes ou efeito causal sobre eleições. A documentação anterior do piloto é preservada para auditoria.
