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

O serviço cartográfico MDS retorna somente municípios com geometrias disponíveis, não a totalidade do cadastro IBGE. A correspondência municipal usa nome normalizado + UF, com unicidade obrigatória; **não há pareamento fuzzy**. Divergências ou ausência de geometria resultam em `null`, nunca zero. O snapshot derivado registra as ausências, nomes não correspondidos, data de extração, urls das consultas e SHA-256 das três respostas.

Script: `python -m scripts.publicar_pessoas_mds`. Arquivo publicado automaticamente em `data/public/pessoas_mds.json` pelo workflow `Publicar cobertura pessoas MDS`.

Os totais municipais cobertos podem divergir do total nacional devido à indisponibilidade geográfica. Portanto, o total nacional não deve ser apresentado como soma completa do indicador municipal publicado.

**Limite temporal:** os municípios referem-se a agosto de 2026; a população é estimativa anual de 2026. Não distribuir a contagem mensal em outros períodos ou inferir variação de pessoas sem outra extração mensal comparável.
