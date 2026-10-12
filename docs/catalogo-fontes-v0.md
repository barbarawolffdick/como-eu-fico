# Catálogo inicial de fontes — etapa 1 (pesquisa documental)

**Data da pesquisa:** 2026-10-12. **Estado:** inventário de possibilidades, não confirmação de séries baixadas nem de cobertura 2023–2026. A escolha de indicadores exige pesquisa específica na etapa 2.

| Fonte | Presença potencial na vida cotidiana | Evidência inicial | Pendências antes da ingestão |
|---|---|---|---|
| **TSE — Resultados 2026** | Referência eleitoral do projeto | Resultados por município, zona e seção; base municipal já validada localmente | Vigência e revisão dos dados; locais de votação ainda pendentes |
| **IBGE — códigos municipais** | Referência territorial comum | Cadastro de códigos municipais de sete dígitos | Registrar vigência territorial ao longo da série |
| **CGU — Bolsa Família por município** | Transferência direta de renda | API pública documenta consulta de parcelas do programa por município | Confirmar significado de “disponibilizado” vs “sacado”, período, volume, limites de API e agregações |
| **CGU — BPC por município** | Proteção social | API documenta consultas de beneficiários por município e mês/ano | Conferir unidade de observação, competência, pagamento e atualização |
| **Tesouro / Siconfi** | Serviços públicos municipais financiados ou cofinanciados | Candidato a fonte contábil; **ainda não validado nesta etapa** | Investigar cobertura por exercício, transferências intergovernamentais e estágios; não confundir receita municipal com pagamento direto a cidadãos |
| **Saúde, educação, habitação e infraestrutura** | Atendimento e entregas concretas | Dimensões do mapa editorial, **não bases selecionadas** | Descobrir fontes, granularidade, indicadores de acesso/entrega e participação federal demonstrável |

## Hipóteses de perguntas (não resultados)

- Quais benefícios e serviços federais ou cofinanciados têm evidência pública municipal?
- Como variou mês a mês o pagamento de determinado benefício entre 2023 e setembro de 2026?
- O aumento de um valor pago corresponde a mais beneficiários, mudança do benefício médio ou ambos?
- Há entregas verificáveis, além de recursos movimentados?
- Como apresentar essas séries ao lado do resultado eleitoral municipal de 2026 sem fazer inferências individuais ou causais?

## Condições para promover uma fonte a IMPLEMENTÁVEL

1. URL oficial e licença/restrições de uso verificadas.
2. Dicionário de dados, descrição do período de referência e unidade da métrica.
3. Identificador municipal mapeável a `codigo_ibge`.
4. Frequência real, cobertura histórica e mecanismo de atualização conhecidos.
5. Política para valores ausentes, supressão, revisões retroativas e riscos de duplicação.
6. Exemplo verificável, teste de integridade e documentação de limitações.

**Não iniciar integração de uma fonte apenas por existir endpoint ou arquivo CSV.**

## Referências

- TSE: https://dadosabertos.tse.jus.br/dataset/resultados-2026
- IBGE: https://www.ibge.gov.br/explica/codigos-dos-municipios.php
- Portal da Transparência — documentação da API: https://api.portaldatransparencia.gov.br/swagger-ui/index.html

> Este catálogo não atribui automaticamente financiamento, prestação de serviço, resultado ou impacto ao governo federal. Cada observação deverá carregar a classificação de evidência e sua fonte.
