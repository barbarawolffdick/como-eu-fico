# Avaliação de fonte — receitas das prefeituras (Siconfi, DCA)

**Data:** 17/10/2026. **ID proposto:** FISCAL-01 — De onde vem o dinheiro da prefeitura. **Estado:** avaliada com consultas reais; **não integrada**.

**Veredito:** fonte **adequada para integração**. Publica o ano de 2025 (o mesmo dos fluxos da página), cobre na prática todos os municípios, usa o código IBGE e separa receitas próprias, transferências da União, do estado e do FUNDEB. A conciliação com o FPM do Tesouro revelou um erro no nosso pipeline (seção própria abaixo).

## Origem

- API pública do Tesouro Nacional: `https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca?an_exercicio={ano}&no_anexo=DCA-Anexo%20I-C&id_ente={codigo_ibge}`.
- Declaração de Contas Anuais (DCA), anexo I-C: receitas orçamentárias realizadas por conta do ementário, com três colunas: “Receitas Brutas Realizadas”, “Deduções – FUNDEB” e “Outras Deduções da Receita”. Cada linha traz `cod_ibge`, UF, instituição declarante e população.
- Os dados são **declarados pelas prefeituras**; o Tesouro recebe e publica, sem auditar cada valor.

## Controles executados

| Controle | Resultado |
|---|---|
| Ano disponível | 2025 e 2024 publicados para Juazeiro do Norte (168 e 179 contas). |
| Cobertura | Amostra aleatória de 60 municípios: 60 com DCA de 2025 e de 2024. A contagem exata fica para o pipeline. |
| Conciliação com o FNS | SUS federal fundo a fundo 2025: R$ 132,9 mi no Siconfi × R$ 132,1 mi no FNS (diferença de 0,6%, compatível com estornos e competência). |
| Conciliação com o Tesouro (FPM) | FPM líquido do FUNDEB no Siconfi: **R$ 179,87 mi**. No arquivo mensal do Tesouro: R$ 155,85 mi (linha `FPM`) + R$ 24,02 mi (linha `FPM 1%`, cotas extraordinárias de julho, setembro e dezembro) = R$ 179,87 mi. Fecha ao centavo. |

## Erro encontrado no nosso pipeline

`scripts/publicar_dinheiro_federal.py` soma só o item `FPM/FPM` dos arquivos do Tesouro e **ignora o item `FPM 1%`** (as cotas adicionais de 1% previstas na Constituição, pagas em julho, setembro e dezembro, sem retenção para o FUNDEB). Em 2025, para Juazeiro, o FPM publicado fica **13% abaixo** do valor real. Afeta os snapshots de 2023 e 2025 e a página do PR 13. Correção: incluir o item `FPM 1%` e conferir com o Siconfi.

## Juazeiro do Norte, 2025 (receita líquida das deduções para o FUNDEB)

Usar a receita **líquida** evita contar duas vezes o dinheiro que a prefeitura entrega ao FUNDEB e recebe de volta.

| Origem | R$ milhões | De cada R$ 100 |
|---|---|---|
| Governo federal (FPM, SUS, complementação da União ao FUNDEB, FNDE e outros) | 493,2 | 41 |
| Impostos e taxas da própria cidade (ISS, IPTU, ITBI, IR retido, taxas) | 213,2 | 18 |
| FUNDEB (fundo estadual formado por impostos de estado e municípios) | 164,2 | 14 |
| Governo estadual (ICMS, IPVA, SUS, convênios) | 115,8 | 10 |
| Previdência própria dos servidores (contribuições e rendimentos) | 101,0 | 8 |
| Outras (iluminação pública, aplicações, multas, operação de crédito e demais) | 106,9 | 9 |
| **Total** | **1.194,4** | 100 |

Destaques: a **complementação da União ao FUNDEB** (R$ 144,2 mi) é um fluxo federal grande que a página ainda não mostra. O ISS (R$ 94,6 mi) é o principal imposto próprio, compatível com uma economia de serviços.

## Cuidados para a integração

1. **Classificação por códigos do ementário**, não por nomes de contas. As contas de primeiro nível usadas: `1.1` (impostos e taxas), `1.7.1` e `2.4.1` (União), `1.7.2` e `2.4.2` (estado), `1.7.5` (FUNDEB), `1.2.1` e `1.3.2.1.04` (previdência própria).
2. **Previdência própria** (RPPS) não é dinheiro para serviços: separar, para não inflar a “receita própria”.
3. **Operações de crédito** (empréstimos) são dinheiro que entra, mas não é receita no sentido de autonomia: mostrar à parte ou dentro de “outras”, com rótulo.
4. **Intraorçamentárias** (R$ 48,5 mi em Juazeiro) ficam fora: são pagamentos da prefeitura para ela mesma.
5. **Declaração tardia ou retificada:** registrar a data da extração e tratar município sem DCA como ausente, nunca zero.
6. **Comparação com os fluxos da página:** o FPM e o SUS do Siconfi devem conciliar com Tesouro e FNS; divergência acima de uma tolerância vira aviso no pipeline.

## Pendências

- Contar exatamente quantos municípios entregaram a DCA de 2025 (endpoint de extrato de entregas ou carga completa).
- Verificar a licença de uso declarada no portal do Tesouro (os demais conjuntos do Tesouro usam ODbL).
- Decidir a apresentação: “De cada R$ 100 que a prefeitura recebeu” como grade de 100 ou treemap, no padrão das demais seções.
