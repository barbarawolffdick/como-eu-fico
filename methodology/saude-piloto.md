# SUS na página da cidade — piloto v1

**Histórico do piloto:** substituído na aplicação pela [cobertura nacional](saude-nacional.md). O snapshot original permanece preservado para auditoria.

Data: 15/10/2026. Escopo publicado: São Paulo/SP (`3550308`), Recife/PE (`2611606`), Sobral/CE (`2312908`), Dourados/MS (`5003702`) e Boa Esperança do Norte/MT (`5101837`). Amostra de engenharia, não amostra estatística nem representação do Brasil.

A cidade é a unidade de entrada, integração e apresentação. A sede de um fundo, a localização de um serviço e a residência dos usuários permanecem conceitos separados. Relações regionais futuras deverão aparecer na página municipal com evidência explícita, sem ratear orçamento estadual por população.

## Fontes e medidas

### FNS: financiamento municipal da atenção primária

- Catálogo: https://portalfns.saude.gov.br/downloads/
- Arquivo oficial: https://portalfns.saude.gov.br/wp-content/uploads/2026/08/Repasse-FAF-com-POPULACAO-2026-acumulado-ate-julho.xlsx
- Unidade original: linha de bloco, grupo, estratégia, destinatário e conta na planilha acumulada. O arquivo tem 116.164 linhas de dados, das quais 59.447 pertencem ao grupo `ATENÇÃO PRIMÁRIA`.
- Seleção: igualdade exata de `GRUPO` com `ATENÇÃO PRIMÁRIA`; código municipal conciliado; `TP_REPASSE=MUNICIPAL` para o indicador principal.
- Medida: soma de `VL_LIQUIDO`, convertida com Decimal para centavos inteiros e agrupada por bloco/estratégia. O snapshot preserva os números das linhas de origem. Há 79 linhas de atenção primária nas cinco cidades, incluindo destinatários municipais e estaduais.
- Período: acumulado janeiro–julho/2026, como declarado pelo catálogo. `DT_ULTIMA_LIBERACAO` não autoriza reconstruir uma série mensal do acumulado.
- `VL_SALDO_CONTA` é estoque bancário repetido por estratégias; **nunca é somado aos repasses**. As populações anexadas à planilha não são usadas como denominador do produto neste piloto.
- Linhas `ESTADUAL` são mantidas como contexto do fundo estadual registrado na cidade; não compõem o total municipal nem representam valores destinados exclusivamente aos moradores.
- Controles: códigos/UF, unicidade da granularidade financeira, datas de liberação dentro do período, precisão monetária, soma dos componentes e separação da esfera destinatária. Valores ausentes invalidam o total, sem substituição por zero.

Conferência da soma municipal em reais nominais: São Paulo 701.883.633,40; Recife 133.414.326,61; Sobral 30.244.915,58; Dourados 26.484.607,87; Boa Esperança do Norte 1.346.736,07. São somas reproduzidas da planilha oficial, não comprovação de despesa executada ou de atendimento.

### APS: equipes homologadas e financiadas

- Interface: https://relatorioaps.saude.gov.br/
- Documentação: https://sisaps.saude.gov.br/sistemas/siaps/docs/manual/relatorios-aps/
- Serviço público usado pela interface: `https://relatorioaps-prd.saude.gov.br/financiamento/pagamento`.
- Filtros: `coMunicipio` de seis dígitos, `unidadeGeografica=MUNICIPIO`, `tipoRelatorio=COMPLETO`, `nuParcelaInicio` igual a `nuParcelaFim`.
- A lista pública `/data/parcelas?ano=2026` retornou parcelas até `202610`. As cinco consultas dessa parcela informaram `nuCompCnes=202608`. Os dois períodos aparecem na interface, sem tratá-los como a mesma data.
- Medidas usadas: eSF (`qtEsfHomologado`, `qtEsfTotalPgto`), eAP (`qtEapHomologado`, `qtEapTotalPgto`) e eMulti (`qtEmultiHomologado`, `qtEmultiPagas`). Financiamento pode ser parcial. Não somar equipes ao longo de parcelas como unidades únicas nem interpretar a contagem como consultas realizadas.
- Rejeitar resposta com múltiplos registros/processos até que exista reconciliação específica. Não somar automaticamente campos potencialmente sobrepostos.
- O relatório financeiro APS não é adicionado ao acumulado FNS: são visões relacionadas do financiamento e podem se sobrepor.
- A parcela mais recente é uma observação publicada, sujeita a atualização; não afirmar fechamento integral do mês.

### Mais Médicos: profissionais ativos

- Catálogo: https://dadosabertos.saude.gov.br/dataset/provimento-federal-programa-mais-medicos
- API/dicionário: https://apidadosabertos.saude.gov.br/v1
- Endpoint agregado: `https://apidadosabertos.saude.gov.br/atencao-primaria/pmmb-serie-historica?ibge=CODIGO_SEIS&limit=1000&offset=0`.
- Preservar cada `dt_referencia` e a contagem oficial `total_prof_ativos`. A última observação é escolhida pela data real, não por posição na resposta. Não somar estoques de profissionais de datas diferentes. Datas irregulares não são uma série mensal completa.
- São Paulo, Recife, Sobral e Dourados retornaram observações até 05/10/2026. Boa Esperança do Norte retornou lista vazia: indicador indisponível, não zero.
- Não foram consultadas nem publicadas relações nominais, identificadores profissionais ou dados clínicos. A contagem não representa todos os médicos do SUS nem atendimentos.

## Território, proveniência e publicação

- Chave do produto: `codigo_ibge` de sete dígitos. A ponte da fonte de seis dígitos usa o prefixo do cadastro IBGE já publicado, com unicidade obrigatória. Nenhum pareamento aproximado por nome.
- Origens brutas independentes em `data/raw/saude/piloto/` (ignorado no Git). Cada consulta tem URL, data de extração e SHA-256. A planilha baixada também pode ser reutilizada por caminho explícito.
- Snapshot derivado: `data/public/saude_piloto.json`, natureza `observado`, status `PILOTO`. API: `/api/saude/{codigo_ibge}`. Páginas municipais usam o mesmo snapshot; não consultam serviços oficiais em cada visita.
- Fora das cinco cidades: informar escopo do piloto. Isso não demonstra ausência de recurso, equipe ou programa na cidade.
- Cartões exibem fonte, período e limitações. `/fontes` e `/api/fontes` incluem a quinta base, URLs e hashes. As competências dos demais domínios não mudam.
- Médias e projeções estão autorizadas como desenvolvimento futuro. Exigem janela, método, premissas e versão, apresentação separada dos observados e limites visíveis. Nenhuma projeção foi implementada neste piloto.
- Referência eleitoral preservada como comparação descritiva. Não inferir voto individual ou efeito causal de financiamento sobre eleição.

## Reprodução e testes

```bash
python -m pip install -r requirements-dados.txt
python scripts/publicar_saude_piloto.py --fns-arquivo /CAMINHO/PLANILHA_OFICIAL.xlsx
python -m unittest discover -s tests -p 'test_saude_piloto.py' -v
npm run lint
npm run build
npm run test:web
```

Sem `--fns-arquivo`, o script baixa o arquivo oficial uma vez. Reutiliza cache com verificação de hash; `--atualizar` solicita novas respostas. A saída só substitui o snapshot após todas as cinco cidades passarem pelos controles.

Os testes usam amostras reais do arquivo e das respostas oficiais. Alterações para simular ausência ou duplicação existem apenas em memória. Verificam separação de fundos, não soma de equipes/processos, referência CNES versus parcela, última observação de profissionais, ausência versus zero, respostas HTTP e navegação entre cidades em desktop/celular. Não executam ingestões TSE ou CGU.
