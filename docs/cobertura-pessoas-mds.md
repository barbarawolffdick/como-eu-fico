# Cobertura municipal de pessoas em famílias beneficiárias (MDS)

## Medida

**Indicador:** percentual da população municipal que integra famílias beneficiárias do Bolsa Família.

- Numerador: contagem de **pessoas** (não famílias/titulares/parcelas) obtida na fonte MDS VIS DATA 3.
- Denominador: população estimada pelo IBGE em **2026**.
- Cálculo: 100 × pessoas em famílias beneficiárias / habitantes do município.
- Competência MDS: **agosto de 2026**. É uma fotografia, não média anual.
- O resultado não informa como beneficiários votaram, nem efeito causal do programa sobre a eleição.

## Fontes e extração

Fonte: [MDS — VIS DATA 3](https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php), indicador **Pessoas beneficiárias do Programa Bolsa Família — por faixa de renda per capita (a partir de mar/2023)**.

Três categorias monetárias de renda per capita são apresentadas separadamente pelo MDS: situação de pobreza segundo faixa do programa; baixa renda; renda acima de meio salário mínimo. As categorias são somadas município a município para reconstruir pessoas integrantes de famílias beneficiárias no período. As três consultas precisam ter exatamente a mesma data e conjunto geográfico antes da soma. O processo não multiplica famílias por seu tamanho médio.

O serviço cartográfico MDS retorna somente municípios com geometrias disponíveis, não a totalidade do cadastro IBGE. A correspondência principal usa nome normalizado + UF, com unicidade obrigatória; **não há pareamento fuzzy**. Onze variantes toponímicas foram reconciliadas por correspondência explícita, código IBGE, nome esperado, UF e fonte documentada em `data/referencia/correspondencia_mds_ibge_2026.json` (inclusive renomeações oficiais). As correspondências só são aplicadas quando aparecem na resposta real do MDS e não colidem com um município já reconhecido. Divergências ou ausência de geometria resultam em `null`, nunca zero. O snapshot derivado registra as ausências, nomes não correspondidos, data de extração, urls das consultas e SHA-256 das três respostas.

Script: `python -m scripts.publicar_pessoas_mds`. Arquivo publicado automaticamente em `data/public/pessoas_mds.json` pelo workflow `Publicar cobertura pessoas MDS`.

Os totais municipais cobertos podem divergir do total nacional devido à indisponibilidade geográfica. Portanto, o total nacional não deve ser apresentado como soma completa do indicador municipal publicado.

**Limite temporal:** os municípios referem-se a agosto de 2026; a população é estimativa anual de 2026. Não distribuir a contagem mensal em outros períodos ou inferir variação de pessoas sem outra extração mensal comparável.

## Auditoria territorial concluída — 15/10/2026

- Cadastro de referência: **5.571 municípios** IBGE.
- GeoJSON municipal MDS: **5.565 feições territoriais** na competência agosto/2026.
- Primeira integração: 5.554 municípios com cobertura, 11 variantes toponímicas e seis ausências cartográficas.
- Reconciliação explícita: **11 aliases** autorizados no catálogo versionado, mantendo código IBGE e URL da evidência.
- Resultado após reconciliação: **5.565 municípios com cobertura (99,9%)**. Os seis restantes não estão no GeoJSON MDS consultado, e ficam como dado indisponível, não 0%.

### Seis municípios não representados no GeoJSON MDS

| Código IBGE | Município | UF |
|---|---|---|
| 1504752 | Mojuí dos Campos | PA |
| 4212650 | Pescaria Brava | SC |
| 4220000 | Balneário Rincão | SC |
| 4314548 | Pinto Bandeira | RS |
| 5006275 | Paraíso das Águas | MS |
| 5101837 | Boa Esperança do Norte | MT |

A tabela nacional do MDS informa 5.571 unidades, mas os polígonos municipais retornados pelo serviço geográfico cobrem 5.565. A consulta de indicadores no VIS DATA 3 devolveu apenas Top 10, sem paginação ampliável. Uma consulta adicional ao serviço tabular do MDS reconheceu os códigos municipais de todos os seis municípios, mas, com a variável testada, **não devolveu contagens numéricas**. Assim, a existência territorial foi corroborada; o numerador de pessoas para os seis continua indisponível na extração validada. Portanto, **não deduzir cobertura zero ou completar seis municípios por médias estaduais ou familiares**. O preenchimento futuro exige uma fonte tabular oficial por código municipal, com as três faixas, mesma competência e rastreabilidade.

### Garantia automatizada

O workflow `Testes do MVP` executa `tests/test_cobertura_http.py` contra o Next.js compilado, usando o snapshot publicado: valida município com cobertura, município ausente, fórmula, ordenação do ranking, filtros eleitorais, UF, períodos e erros. Também valida as correspondências explícitas com `tests/test_correspondencia_pessoas_mds.py`. A compilação e as páginas `/`, `/explorar` e `/analises` são verificadas pelo mesmo workflow.

A integração com a prévia do v0 ainda precisa ser verificada no projeto conectado. O CI valida a aplicação do repositório, não autentica ou atualiza automaticamente uma sessão do v0.
