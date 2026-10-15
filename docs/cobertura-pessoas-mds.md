# Cobertura municipal de pessoas em famílias beneficiárias (MDS)

## Medida

**Indicador:** percentual da população municipal que integra famílias beneficiárias do Bolsa Família.

- Numerador: contagem de **pessoas** (não famílias/titulares/parcelas) obtida na fonte MDS VIS DATA 3.
- Denominador: população estimada pelo IBGE em **2026**.
- Cálculo: 100 × pessoas em famílias beneficiárias / habitantes do município.
- Competência MDS validada: **setembro de 2026**. É uma fotografia, não média anual.
- O resultado não informa como beneficiários votaram, nem efeito causal do programa sobre a eleição.

## Fontes e extração

Fonte: [MDS — VIS DATA 3](https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php), indicador **Pessoas beneficiárias do Programa Bolsa Família — por faixa de renda per capita (a partir de mar/2023)**.

Três categorias monetárias de renda per capita são apresentadas separadamente pelo MDS: situação de pobreza segundo faixa do programa; baixa renda; renda acima de meio salário mínimo. As categorias são somadas município a município para reconstruir pessoas integrantes de famílias beneficiárias no período. As três consultas precisam ter exatamente a mesma data e conjunto geográfico antes da soma. O processo não multiplica famílias por seu tamanho médio.

O serviço cartográfico MDS retorna somente municípios com geometrias disponíveis, não a totalidade do cadastro IBGE. A publicação atual complementa as seis ausências com a série tabular oficial por código municipal, na mesma competência validada. A correspondência principal usa nome normalizado + UF, com unicidade obrigatória; **não há pareamento fuzzy**. Onze variantes toponímicas foram reconciliadas por correspondência explícita, código IBGE, nome esperado, UF e fonte documentada em `data/referencia/correspondencia_mds_ibge_2026.json` (inclusive renomeações oficiais). As correspondências só são aplicadas quando aparecem na resposta real do MDS e não colidem com um município já reconhecido. Divergências ou ausência de geometria resultam em `null`, nunca zero. O snapshot derivado registra as ausências, nomes não correspondidos, data de extração, urls das consultas e SHA-256 das três respostas.

Script: `python -m scripts.publicar_pessoas_mds`. Arquivo publicado automaticamente em `data/public/pessoas_mds.json` pelo workflow `Publicar cobertura pessoas MDS`.

Os totais municipais cobertos podem divergir do total nacional devido à indisponibilidade geográfica. Portanto, o total nacional não deve ser apresentado como soma completa do indicador municipal publicado.

**Limite temporal:** os municípios referem-se a setembro de 2026; a população é estimativa anual de 2026. Não distribuir a contagem mensal em outros períodos ou inferir variação de pessoas sem outra extração mensal comparável.

## Histórico da auditoria territorial — 15/10/2026

- Cadastro de referência: **5.571 municípios** IBGE.
- GeoJSON municipal MDS: **5.565 feições territoriais**. A coleta inicial solicitou agosto/2026, mas o conteúdo foi posteriormente reconciliado com setembro/2026; ver a correção temporal abaixo.
- Primeira integração: 5.554 municípios com cobertura, 11 variantes toponímicas e seis ausências cartográficas.
- Reconciliação explícita: **11 aliases** autorizados no catálogo versionado, mantendo código IBGE e URL da evidência.
- Resultado inicial após reconciliação de nomes: **5.565 municípios com cobertura (99,9%)**. As seis ausências do GeoJSON permaneceram indisponíveis até a validação tabular descrita abaixo.

### Seis municípios não representados no GeoJSON MDS

| Código IBGE | Município | UF |
|---|---|---|
| 1504752 | Mojuí dos Campos | PA |
| 4212650 | Pescaria Brava | SC |
| 4220000 | Balneário Rincão | SC |
| 4314548 | Pinto Bandeira | RS |
| 5006275 | Paraíso das Águas | MS |
| 5101837 | Boa Esperança do Norte | MT |

A tabela nacional do MDS informa 5.571 unidades, mas os polígonos municipais retornados pelo serviço geográfico cobrem 5.565. A consulta de indicadores no VIS DATA 3 devolveu apenas Top 10, sem paginação ampliável. Uma consulta adicional ao serviço tabular do MDS reconheceu os códigos municipais de todos os seis municípios, mas, com a variável testada, **não devolveu contagens numéricas**. Naquela etapa, a existência territorial foi corroborada, mas o numerador de pessoas para os seis continuava indisponível. Portanto, **não deduzir cobertura zero ou completar seis municípios por médias estaduais ou familiares**. Esse requisito foi satisfeito pela consulta tabular VIS DATA 3 por código municipal, descrita a seguir.

### Garantia automatizada

O workflow `Testes do MVP` executa `tests/test_cobertura_http.py` contra o Next.js compilado, usando o snapshot publicado: valida município com cobertura, município ausente, fórmula, ordenação do ranking, filtros eleitorais, UF, períodos e erros. Também valida as correspondências explícitas com `tests/test_correspondencia_pessoas_mds.py`. A compilação e as páginas `/`, `/explorar` e `/analises` são verificadas pelo mesmo workflow.

A aplicação do repositório é validada em produção Vercel por testes HTTP e de navegador. Uma sessão de edição do v0 pode ter estado próprio.


## Complementação e correção temporal — 15/10/2026

A página oficial `v.php?q[]=…` aceita `ag=m&codigo=IBGE7` e publica a série numérica no JSON do gráfico (`var strJsondados`), mesmo para cidades sem polígono. A resposta identifica código IBGE de seis dígitos, nome, UF, `mes_ano`, total de pessoas e as três faixas. A ponte com IBGE7 usa o prefixo de seis dígitos do cadastro versionado e verifica unicidade, nome e UF; não usa aproximação textual.

A coleta cartográfica original solicitou agosto e a resposta repetiu essa referência nos polígonos. Entretanto, os valores numéricos eram de **setembro/2026**. A consulta tabular datada identificou o erro: São Paulo, Manaus, Recife, Rio de Janeiro e Porto Alegre coincidem exatamente com setembro e diferem de agosto. A soma de cada faixa cartográfica, acrescida das seis cidades, coincide exatamente com a respectiva faixa Brasil de setembro. A soma de todos os municípios também fecha em **49.645.630 pessoas**. Por isso, corrigiu-se a competência do snapshot e da interface para **202609**, preservando os valores dos 5.565 municípios anteriores. A série CGU e as fotografias de famílias MDS conservam seus próprios períodos.

| Município | IBGE | Pessoas em setembro/2026 |
|---|---|---:|
| Mojuí dos Campos — PA | 1504752 | 11.878 |
| Pescaria Brava — SC | 4212650 | 1.603 |
| Balneário Rincão — SC | 4220000 | 2.971 |
| Pinto Bandeira — RS | 4314548 | 81 |
| Paraíso das Águas — MS | 5006275 | 533 |
| Boa Esperança do Norte — MT | 5101837 | 412 |

Controles nacionais por faixa: **42.935.234**, **6.710.313** e **83** pessoas. O resultado cobre **5.571/5.571 municípios**, sem estimativas ou preenchimento com zero. `data_extracao` conserva a data da coleta cartográfica; `data_validacao_tabular` registra a reconciliação. `periodo_solicitado_na_coleta_original` preserva o rótulo anterior. As URLs completas, hashes HTML, datas de extração, código original, valores das faixas e controles ficam em `complemento_tabular` no snapshot. Os arquivos brutos permanecem no cache ignorado `data/raw/mds/tabular-pessoas/`.

Para reproduzir somente a complementação, reutilizando os caches verificados: `python -m scripts.complementar_pessoas_mds`. A opção `--corrigir-periodo` autoriza explicitamente a migração do antigo rótulo 202608; sem ela, um período divergente bloqueia a publicação. `--atualizar` renova as consultas oficiais. O pipeline nacional `scripts.publicar_pessoas_mds.py` também exige esses controles antes da substituição atômica do arquivo. Sua execução no GitHub Actions agora é manual (`workflow_dispatch`), para não refazer a coleta em mudanças de código.

O teste `tests/test_complementar_pessoas_mds.py` usa linhas reais de agosto/setembro e protege identidade municipal, competência, faixas ausentes, hashes, preservação dos demais municípios e totais. Os testes de navegador verificam as seis páginas e preservam o comportamento de indisponibilidade para futuras ausências.
