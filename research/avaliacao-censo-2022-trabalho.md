# Avaliação de fonte — trabalho e informalidade (Censo 2022) e emprego formal (RAIS)

**Data:** 17/10/2026. **IDs propostos:** TRABALHO-01 (Censo 2022, formalidade) e TRABALHO-02 (RAIS, emprego formal por setor). **Estado:** avaliadas com consultas reais; **não integradas**.

**Veredito:** o Censo 2022 é **adequado para integração** e é a única fonte que mede a informalidade município a município, pela definição oficial do IBGE. A RAIS é o complemento para o emprego formal por setor, com o ano de 2025 publicado, mas exige processar microdados grandes.

## O que é “formal” (definição usada)

Segue a definição de informalidade do IBGE nas pesquisas domiciliares. São **informais**: empregados do setor privado sem carteira assinada, trabalhadores domésticos sem carteira, empregadores sem CNPJ, trabalhadores por conta própria sem CNPJ e trabalhadores familiares auxiliares. Os demais ocupados são formais: empregados com carteira, servidores estatutários, militares e empregadores ou trabalhadores por conta própria com CNPJ.

**Zona cinzenta:** empregados do setor público e de estatais **sem carteira e não estatutários** (contratos temporários, cargos comissionados) não entram na taxa de informalidade do IBGE. Em Juazeiro são 2.500 pessoas (2,1% dos ocupados). Devem aparecer como grupo próprio, não somados a nenhum dos lados.

## Censo 2022 — tabela 10261 (SIDRA)

- “Pessoas de 14 anos ou mais ocupadas na semana de referência, por posição na ocupação e categoria do emprego no trabalho principal, sexo e cor ou raça”.
- Níveis: Brasil, região, UF e **município** (N6). Ano único: 2022. Resultado da amostra (cerca de 10% dos domicílios); publicado em 09/10/2025.
- Categorias: com e sem carteira (privado, doméstico, setor público não estatutário, estatais), funcionário estatutário, militar, empregador com e sem CNPJ, conta própria com e sem CNPJ, trabalhador familiar auxiliar.
- Tabelas relacionadas para aprofundar: 10262 (mesma posição por seção de atividade) e 10264/10266 (contribuição para a previdência).

**Juazeiro do Norte, 2022 (117.749 ocupados)**

| Grupo | Pessoas | De cada 100 |
|---|---|---|
| Empregados com carteira (privado e doméstico) | 37.589 | 32 |
| Setor público, estatais e militares | 12.884 | 11 |
| Empregadores e conta própria com CNPJ | 9.811 | 8 |
| **Informais** (definição do IBGE) | 57.465 | **49** |

Somam 117.749. Comparação: informalidade de **48,8%** em Juazeiro, 48,3% no Ceará e 36,3% no Brasil. Setor público e militares: 10,4% dos ocupados em Juazeiro, 15,0% no Ceará e 13,2% no Brasil.

**Cuidados:** é uma fotografia de 2022, anterior aos fluxos de 2025 da página, e deve aparecer com o ano. Como resultado amostral, municípios pequenos têm incerteza maior; o IBGE publica as estimativas sem intervalo nesta tabela. Não é comparável ao Censo 2010 (idade mínima mudou de 10 para 14 anos).

## RAIS — emprego formal por setor

- Microdados do Ministério do Trabalho (`ftp.mtps.gov.br/pdet/microdados/RAIS/`): **2024 e 2025 publicados**, por região, em 7z (vínculos do Nordeste de 2024: 595 MB compactados; estabelecimentos: 141 MB).
- Cobre todos os vínculos formais, celetistas **e estatutários**, por município, setor (CNAE) e natureza jurídica; permite separar emprego público e privado e calcular massa salarial.
- A coleta mudou em 2024: a série comparável começa em 2023. A RAIS de 2024 introduziu “vínculos abandonados”, que devem ser excluídos.
- Não mede informalidade: só vê o lado formal. Usada junto com o Censo, mostra o tamanho do lado formal (Censo) e quem emprega formalmente (RAIS).
- O Novo Caged, mensal, mede admissões e desligamentos com carteira; não dá o estoque e praticamente exclui servidores estatutários. Não serve para medir dependência do emprego público.

## Pendências

1. Testar a carga da tabela 10261 para os 5.571 municípios e conciliar a soma das categorias com o total.
2. Processar uma região da RAIS 2025 para estimar tempo, memória e espaço; agregar por município × seção da CNAE × setor público/privado, sem guardar microdados no repositório.
3. Decidir a apresentação: pictograma de 100 trabalhadores (no padrão do Bolsa Família) com a definição visível, e emprego formal por setor com destaque para o setor público.
