# Mapa da presença federal no cotidiano — Pesquisa verificável v1

**Data:** 12/10/2026. **Unidade de análise:** município. **Série-alvo:** meses de 2023-01 a 2026-09, sem inventar observações onde a fonte tem outra periodicidade. **Eleição:** 2026, referência fixa, nunca consequência causal presumida.

Este mapa organiza possibilidades de experiência do cidadão, não organogramas de ministérios. `CONFIRMADA` significa que a **fonte ou estrutura de dados** foi verificada na documentação pública; não significa cobertura histórica, qualidade de registros, acesso em massa nem efeito causal já demonstrados.

## Fontes e medidas encontradas

| ID | Dimensão percebida | Política/base | Evidência documentada | Frequência / granularidade aparente | Estágio da pesquisa | Limitação central |
|---|---|---|---|---|---|---|
| RENDA-01 | Renda da família | Novo Bolsa Família — Portal da Transparência | Mês competência, mês referência, município SIAFI, parcela e valor | Por parcela/beneficiário, referência mensal | Fonte e dicionário confirmados | Código municipal da fonte **é SIAFI, não IBGE**. Exige ponte oficial; registros pessoais não devem alimentar a camada pública |
| RENDA-02 | Proteção da renda | BPC — Portal da Transparência | Arquivos de benefícios ao cidadão e consulta por município/mês | Atualização mensal declarada | Fonte confirmada, esquema por validar | Beneficiário, disponibilização e pagamento podem ser medidas diferentes |
| EDU-01 | Comida na escola | PNAE — FNDE | Repasses a entidades executoras; dados de alunos/escolas e repasses financeiros mensais no catálogo FNDE | Mensal para repasses; entidade executora pode ser prefeitura ou secretaria estadual | Fonte confirmada | Repasse a ente **não comprova merenda servida**; alocar repasses estaduais a municípios requer outra evidência |
| EDU-02 | Transporte escolar | PNATE — FNDE | Portal divulga estimativas, repasses e alunos rurais contemplados | Dados mensais anunciados no portal | Fonte confirmada, esquema por validar | Estimativa não equivale a execução, e aluno considerado não é automaticamente atendido |
| EDU-03 | Materiais escolares | PNLD — FNDE | Fornecimento de livros, distribuição, adesão de redes | Por entrega/ciclo, não assumir mensal | Fonte confirmada, esquema por validar | Distribuição contabilizada não equivale a uso individual |
| SAUDE-01 | Postos e hospitais próximos | CNES — Ministério da Saúde | Relação de estabelecimentos cadastrados, atualização de catálogo diária | Estoque cadastral em snapshots | Dataset confirmado | Cadastro de estabelecimento **não demonstra atendimento nem financiamento federal exclusivo** |
| MORADIA-01 | Casa entregue | Minha Casa Minha Vida — Ministério das Cidades (OGU) | Arquivo contém `cod_ibge`, `qtd_uh`, `qtd_uh_entregues`, `val_contratado_total`, `val_desembolsado` e situação do empreendimento | Data de referência e de contrato/empreendimento; não é uma série mensal de entregas | Arquivo e cabeçalho confirmados | Código municipal mostrado tem seis dígitos; requer mapeamento territorial verificado. Snapshot não permite datar entregas retroativamente |
| FIN-01 | Recursos públicos na cidade | Recursos transferidos — Portal da Transparência | CSV de recursos transferidos; atualização diária declarada | Pagamentos/transferências em registros administrativos | Catálogo confirmado, esquema por validar | Não confundir transferência intergovernamental com benefício pago ao cidadão; evitar dupla contagem |
| INFRA-01 | Obras e infraestrutura escolar | Novo PAC e infraestrutura escolar — FNDE | Informações de obras, finalidade, execução física e repasses | Por obra, eventos e atualizações | Catálogo confirmado, esquema por validar | Valor contratado não é obra concluída |

## Evidências oficiais consultadas

1. **CGU — arquivos por tema e periodicidade:** https://portaldatransparencia.gov.br/download-de-dados/
2. **CGU — Novo Bolsa Família, dicionário:** https://portaldatransparencia.gov.br/dicionario-de-dados/novo-bolsa-familia
3. **CGU — Novo Bolsa Família, downloads:** https://portaldatransparencia.gov.br/download-de-dados/novo-bolsa-familia
4. **CGU — BPC / API por município/mês:** https://api.portaldatransparencia.gov.br/swagger-ui/index.html
5. **FNDE — Dados Abertos (PNAE, PNATE, PNLD, obras, PDDE):** https://www.gov.br/fnde/pt-br/acesso-a-informacao/dados-abertos
6. **FNDE — PNAE e transferências a executores:** https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/programas/pnae
7. **Ministério da Saúde — CNES:** https://dadosabertos.saude.gov.br/dataset/cnes-cadastro-nacional-de-estabelecimentos-de-saude
8. **Ministério das Cidades — MCMV, campos reais do CSV:** https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/habitacao/programa-minha-casa-minha-vida/arquivos/dados_abertos_ogu_202503.csv/view
9. **CGU — recursos transferidos no catálogo:** https://portaldatransparencia.gov.br/download-de-dados

## Perguntas editoriais concretas (a validar com dados)

**Renda:** Como evoluiu o valor das parcelas do Bolsa Família disponibilizadas aos residentes de um município, mês a mês? Quantas famílias únicas são representadas, considerando a regra oficial de beneficiário? O crescimento de despesa acompanha o alcance ou o valor médio?

**Educação:** Quanto foi transferido ao executor municipal do PNAE em cada mês? Quantos estudantes compõem a base utilizada para o cálculo? Existem evidências adicionais para mostrar escolas ou refeições efetivamente atendidas?

**Saúde:** Quantos estabelecimentos cadastrados estão no município numa data específica? Quais tipos de atendimento constam da fonte? Quais bases adicionais permitem identificar produção de serviços ou financiamento federal efetivo?

**Moradia:** Quantas unidades aparecem como entregues no snapshot oficial? Como distinguir contratado, desembolsado e entregue? Há data de entrega verificável e séries históricas de snapshots comparáveis?

**Cidade:** Quais fluxos da União chegam a entes e executores locais? Quais pertencem a programas identificáveis e quais representam repasses gerais? Como impedir a soma duplicada de diferentes bases?

## Decisões técnicas antes da primeira ingestão

1. **Ponte territorial:** CGU usa SIAFI em Bolsa Família; MCMV apresenta `cod_ibge` de seis dígitos; TSE usa códigos eleitorais. Não juntar por simples igualdade a `codigo_ibge` sete dígitos nem por nome aproximado.
2. **Privacidade:** só armazenar ou publicar agregações municipais necessárias ao produto; não enviar registros nominais de benefícios para visualizações públicas.
3. **Calendário:** preservar competência, referência, desembolso, publicação e extração como datas distintas. Atualização mensal do catálogo não prova cobertura mensal contínua de 2023–2026.
4. **Taxonomia de evidências:** financiamento, alcance, entrega, resultado e impacto causal são níveis diferentes. A dimensão editorial pode cruzar fontes sem misturá-las fisicamente.
5. **Avaliação:** fonte documentada ≠ acesso programático validado ≠ série completa ≠ indicador publicável.

## Validações experimentais ainda pendentes

- Baixar **um mês real** do Novo Bolsa Família para verificar o cabeçalho, a chave SIAFI e os tipos de valor; procurar tabela oficial SIAFI–IBGE.
- Baixar **um mês real** do PNAE para verificar se município de execução e ente destinatário são campos distintos; documentar as parcelas e mudanças de calendário.
- Inspecionar histórico do CNES, existência de snapshots reprodutíveis e município dos estabelecimentos.
- Validar esquema, período e cobertura do arquivo MCMV e a semântica exata das unidades entregues.
- Investigar fontes de atendimentos em saúde e de serviços prestados, não apenas de estabelecimentos cadastrados.

Este documento **não autoriza afirmar efeitos da política sobre votos de 2026**. É um mapa operacional das evidências que faltam para examinar essa relação.
