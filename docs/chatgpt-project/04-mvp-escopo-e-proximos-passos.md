# MVP — definição e ordem de execução

## Resultado esperado
Uma aplicação web responsiva, publicável e navegável chamada **Como Eu Fico**. A pessoa escolhe um município (nome, UF, código IBGE) e vê **votos presidenciais de 2026 e fluxos federais juntos**, com uma série real do Bolsa Família e contextualização IBGE. Cada indicador mostra fonte, período, unidade e ressalvas relevantes.

## Experiência mínima
1. Busca de municípios com desambiguação por UF; URL compartilhável para a cidade.
2. Cabeçalho territorial: município, UF, contexto demográfico validado.
3. Resultado do **primeiro turno presidencial de 2026**, com candidatos, votos e proporções conforme fonte oficial.
4. Fluxo federal — Bolsa Família: número de **parcelas**, valores agregados em R$, série de 202501 a 202608, opção de período e contexto de Brasil conforme cálculo verificado. Sempre dizer 'parcelas', não 'famílias'.
5. Quadro comparativo descritivo: o que a série do fluxo mostra **ao lado** do voto, sem insinuar voto causado por benefício; informações metodológicas fáceis de consultar.
6. Estados de falta de dados, atraso de publicação e diferenças de cobertura (Boa Esperança do Norte 5101837 entra em 202510).

## Critérios de aceite
- Município recuperável pelo código IBGE e por busca.
- Nenhum dado de exemplo passa por dado real; números vêm dos datasets validados.
- Totais de Bolsa Família por competência preservados na camada derivada.
- Chaves de junção sem multiplicação indevida de votos/parcelas.
- Histórico eleitoral de primeiro turno correto e identificável.
- Responsivo, leve e navegável, com fontes e limitações claras.
- Não publicar CPF/NIS/nomes e não alterar bancos originais.
- Indicadores de saúde/educação não são necessários para primeira versão.

## Execução priorizada
**Passo 1 — inventário técnico:** identificar stack, arquivos efetivamente versionados, snapshots TSE disponíveis, presença/ausência do SQLite municipal e situação do PR #9. Selecionar deploy simples; evitar refazer pipelines já auditados.

**Passo 2 — contrato do dataset de interface:** definir arquivo(s) municipais pequenos para front-end, esquema `codigo_ibge`, `municipio`, `uf`, `candidatos_2026_t1`, `bolsa_familia_serie`, `populacao_referencia`; unidades, chaves, fontes, versão e estratégia para lacunas. Dados brutos ficam fora do site.

**Passo 3 — gerar dados públicos mínimos:** exportar o SQLite da CGU para agregados municipais por competência, validar totais, preparar snapshot eleitoral municipal e população IBGE verificada. Não misturar arquivos-fonte nem inferir famílias únicas.

**Passo 4 — construir interface:** busca, página municipal, resultado eleitoral, gráfico e tabela do Bolsa Família, comparações e fontes. Testar com municípios de tamanhos diferentes e com Boa Esperança do Norte.

**Passo 5 — lançar versão pública:** testes, acessibilidade, build, hospedagem e URL compartilhável. Registrar dataset e commit usado.

**Passo 6 — evoluir:** ampliar para BPC, Pé-de-Meia, PNAE, SUS e outras dimensões do fluxo federal, uma fonte validada de cada vez. Evitar ciclo infinito de ingestão antes de entregar o MVP.

## Proposta de primeiro prompt no novo projeto
“Leia todos os arquivos de continuidade do Como Eu Fico e inspecione o repositório público https://github.com/barbarawolffdick/como-eu-fico e seus PRs. Nosso objetivo imediato é publicar um MVP web municipal que mostre lado a lado os votos do primeiro turno presidencial de 2026, a série de fluxo federal do Bolsa Família (202501–202608) e dados de contexto do IBGE. Identifique os arquivos reais disponíveis, os bloqueios objetivos de dados/deploy e comece a implementação em passos pequenos, sem reprocessar as fontes já auditadas. Não confunda planejamento com execução. Registre commits e testes realizados.”
