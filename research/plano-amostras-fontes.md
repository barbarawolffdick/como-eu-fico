# Primeira rodada de validação empírica — plano executável

## Critério de escolha

As fontes não serão implementadas porque são mais fáceis; verificaremos inicialmente três mecanismos distintos da presença federal: **pagamento direto**, **financiamento de serviço cotidiano** e **entrega concreta**. A execução terá estágio separado de pesquisa, ingestão e publicação.

| Prova de conceito | O que extrair em um único município e período | Verificações obrigatórias | Resultado possível |
|---|---|---|---|
| Novo Bolsa Família (CGU) | mês competência, mês referência, valor das parcelas, código SIAFI | relação SIAFI–IBGE oficial; tipos de parcela; agregação com preservação dos totais; privacidade | Série municipal de valores **disponibilizados**, não renda efetivamente recebida sem evidência |
| PNAE (FNDE) | parcela de repasse, ente recebedor, mês, alunos considerados | município executor vs. secretaria estadual; não distribuir valores estaduais entre municípios arbitrariamente | Série de **repasses federais para alimentação escolar**, não refeições servidas |
| Minha Casa Minha Vida (MCid) | empreendimento, status, unidades entregues, desembolso e data de referência | códigos IBGE de seis dígitos; snapshots/versões; não inferir mês de entrega de um estoque | Quantidade **reportada como entregue** na data do arquivo, não evolução mensal sem histórico |

## Critério de saída da pesquisa

A prova de conceito avança à modelagem de uma base independente apenas se tivermos amostra real, dicionário de campos, chaves verificadas, período, política de ausentes, deduplicação e distinção entre valores financeiros, alcance e entregas.

**O que falta para responder à pergunta eleitoral:** só após construir séries confiáveis por município, cruzar os dados derivados aos resultados de 2026 por `codigo_ibge` e testar a comparabilidade temporal. As associações serão descritivas, não conclusões causais.

## Fontes

- https://portaldatransparencia.gov.br/dicionario-de-dados/novo-bolsa-familia
- https://portaldatransparencia.gov.br/download-de-dados/novo-bolsa-familia
- https://www.gov.br/fnde/pt-br/acesso-a-informacao/dados-abertos
- https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/habitacao/programa-minha-casa-minha-vida/arquivos/dados_abertos_ogu_202503.csv/view
