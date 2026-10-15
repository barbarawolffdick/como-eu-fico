# Bolsa Família: moradores, famílias e médias monetárias

Atualização de 15/10/2026, solicitada em conversa. A apresentação distingue:

- **Cobertura na cidade:** pessoas que vivem em famílias beneficiárias / população municipal estimada. Inclui o titular e os demais integrantes. Não é a fração de uma família ou uma contagem de pagamentos individuais. O percentual publicado usa setembro/2026 e população IBGE 2026.
- **Valor por pessoa da família beneficiária:** valor CGU por competência / pessoas MDS **da mesma competência**. Não usa toda a população municipal. Não representa pagamento separado a cada integrante.
- **Valor médio registrado por família:** mesmo valor CGU / famílias beneficiárias MDS da mesma competência. Não usa quantidade de parcelas ou pressupõe que todos receberam exatamente a média.
- **Pessoas por família:** razão das duas contagens MDS no mesmo mês, quando ambas existem. É uma média municipal, não tamanho de cada família.

O titular é a pessoa responsável pelo recebimento para a família, conforme as [informações do MDS](https://www.gov.br/mds/pt-br/acoes-e-programas/bolsa-familia/conheca-as-regras). As bases agregadas publicadas não permitem deduplicar titulares a partir de parcelas. Valores registrados na CGU não comprovam saque e podem refletir a composição dos registros da competência. A interface preserva essa distinção.

## Compatibilidade temporal e territorial

O dinheiro publicado vai até agosto/2026, enquanto a cobertura populacional mais recente usa setembro/2026. Não se divide dinheiro de agosto por pessoas de setembro. A série tabular VIS DATA 3 foi validada para agosto e setembro em 13 cidades de controle/exemplo, incluindo Lavras e Rio de Janeiro. Cada linha verifica código IBGE, nome, UF, competência, contagem inteira não negativa e reconciliação das três faixas de renda com o total de pessoas. Setembro também reconcilia com a fotografia nacional publicada.

`data/public/pessoas_mds_mensal.json` identifica o histórico como **PARCIAL**, com cobertura, competências, URLs, hashes e datas. Ele não substitui `pessoas_mds.json`, que continua com cobertura nacional. `python -m scripts.publicar_pessoas_mds_mensal` reproduz somente esse recorte tabular, reutilizando caches verificados. Não reprocessa TSE ou CGU.

`/api/beneficiarios/{IBGE7}` combina essas contagens com o snapshot de famílias. Para outras cidades, consulta individualmente a série tabular MDS, com cache de até 24 horas. Só aceita a origem oficial, valida os registros e reconcilia setembro com a fotografia nacional antes de liberar os dados históricos. A resposta informa a origem e o hash. Se falhar a validação, descarta os números consultados e mantém apenas as contagens de famílias já publicadas. O acesso é público, sem registros pessoais ou segredos.

A comparação usa o último mês CGU comum às duas cidades. Cada média exige o denominador desse mês; uma lacuna não é substituída pelo último mês MDS disponível. Ausência, denominador zero ou erro não geram barras ou diferenças numéricas. É possível escolher pessoa da família, família ou total municipal, independentemente da unidade da saúde. A URL preserva a opção `bolsa=pessoa|familia|total`.

## Votos e explicações

Os três candidatos com mais votos aparecem inicialmente; “Ver mais candidatos” expande a relação. O total usado nos percentuais continua incluindo todos os candidatos, antes e depois da expansão. Empates e ausências continuam explícitos.

Explicações longas abrem em diálogo modal nativo, com foco contido, fechamento por Escape/botão, restauração do foco e rolagem própria. Tooltips curtos são renderizados fora do fluxo da página por portal, para evitar cortes e alterações de largura. Datas, unidades e explicações essenciais continuam visíveis.
