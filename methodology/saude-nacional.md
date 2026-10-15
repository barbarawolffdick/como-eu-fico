# Saúde nas páginas de todas as cidades

Versão de 15/10/2026. O snapshot `data/public/saude_municipal.json`, esquema 2, substitui o piloto nas rotas públicas. Cadastro territorial: os mesmos 5.571 códigos IBGE já usados pelo produto, incluindo Brasília e Fernando de Noronha. Consulta municipal completa não significa que todo indicador esteja disponível em cada território.

## Fontes e períodos conferidos

O [catálogo FNS](https://portalfns.saude.gov.br/downloads/) foi reconferido em 15/10/2026: a publicação de 2026 permanece acumulada até julho. Reutilizamos a planilha oficial do piloto, sem repetir ingestões TSE ou CGU. O [portal do Mais Médicos](https://dadosabertos.saude.gov.br/dataset/provimento-federal-programa-mais-medicos) informa atualização do consolidado em 09/10/2026. Data de atualização do catálogo e referência interna dos dados são verificadas separadamente.

| Indicador | Fonte observada | Referência | Cobertura com dado |
| --- | --- | --- | --- |
| Repasse líquido ao fundo municipal, Atenção Primária | Planilha FNS `Repasse-FAF-com-POPULACAO-2026-acumulado-ate-julho.xlsx` | Janeiro a julho de 2026 | 5.569 |
| eSF, eAP e eMulti homologadas/financiadas | Relatório completo nacional APS, `unidadeGeografica=MUNICIPIO` | Parcela 202610; CNES 202608 | 5.571 |
| Vagas ocupadas no provimento federal | ZIP oficial `ppf_mais_medicos.csv.zip`, campo `total_ocupadas` | 09/10/2026 | 5.571 |

As janelas acima são diferentes e aparecem junto a cada indicador. Não calculamos variações nem razões entre períodos incompatíveis. A parcela mais recente não comprova fechamento do mês.

## Transformações e território

**FNS:** aplicam-se as regras financeiras [documentadas no piloto](saude-piloto.md): filtrar `GRUPO=ATENÇÃO PRIMÁRIA`; separar `TP_REPASSE`; converter reais para centavos com Decimal; validar datas, códigos, UF, granularidade e soma dos componentes. As 59.447 linhas de atenção primária são conciliadas, preservando números de linhas. Nunca somar saldo bancário nem o valor do relatório APS ao FNS.

Brasília (`5300108`) e Fernando de Noronha (`2605459`) não têm repasse na esfera municipal validado neste recorte. O valor municipal fica nulo, nunca zero. A planilha contém repasses classificados como estaduais em Brasília, exibidos separadamente como fundo distrital. Não concluímos ausência de financiamento nem rateamos fundos estaduais entre municípios. Para Fernando de Noronha não atribuimos orçamento estadual sem evidência de destinação.

**APS:** uma única resposta nacional traz 5.571 pagamentos, um por código municipal. A transformação confere o município e a UF contra o cadastro e mantém a parcela distinta da competência CNES. Mais de um processo por município interrompe a publicação, sem somar equipes potencialmente sobrepostas. Campos ausentes permanecem nulos; zero literal da fonte é mantido. Nenhuma quantidade mede atendimentos realizados.

**Mais Médicos:** usamos a exportação consolidada completa oferecida no catálogo, em vez da API paginada ou de milhares de consultas individuais. O ZIP contém um CSV agregado, sem nomes de profissionais ou dados clínicos. O [dicionário oficial](https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/MaisMedicos/Dicionario_de_dados_PPF_Mais_Medicos.pdf) define `total_ocupadas` como vagas de provimento federal ocupadas por profissionais em atividade, incluindo PMMB e instituições vinculadas. A interface mede **vagas ocupadas**, sem afirmar profissionais únicos ou todos os médicos do SUS.

O arquivo tem 5.631 linhas: 5.571 municipais, 34 DSEI e 26 estaduais. Somente `nivel=MUNICIPAL` entra nos cartões municipais. Os demais registros ficam listados na validação do snapshot com linha, tipo territorial, código e nome, sem soma ou rateio para cidades. Cada município deve ter exatamente uma linha; UF, código e data são validados. Datas mistas exigem reconciliação antes de publicar.

O consolidado traz 1.126 zeros municipais explícitos (incluindo Boa Esperança do Norte). São zeros observados no recorte do programa, não demonstração de ausência de médicos na cidade. Uma linha ausente ou um valor vazio continua indisponível. O consolidado atual substitui a fotografia histórica no cartão; não concatenamos medidas com nomes diferentes nem calculamos variação entre o piloto e a nova versão.

## Proveniência, atualização e publicação

Cada fonte tem URL oficial, SHA-256 dos bytes e momento de extração/reutilização. Linhas dos componentes FNS e do CSV Mais Médicos permitem voltar aos arquivos brutos. O cadastro usa prefixo IBGE de seis dígitos com unicidade obrigatória, sem pareamento por nome. A identificação municipal oficial do produto é preservada.

As respostas ficam no cache ignorado `data/raw/saude/nacional/`. Reexecutar sem `--atualizar` valida os hashes e retoma as fontes já obtidas. Falhas HTTP transitórias têm até três tentativas; uma fonte inválida impede a substituição do snapshot. A saída temporária só substitui o arquivo final após reconciliação territorial, contagens e somas. Mudança de período FNS requer atualizar a configuração e validar seu intervalo; não rotular automaticamente o arquivo como mês atual.

`/api/saude/{codigo_ibge}` devolve apenas a cidade solicitada. O snapshot é reutilizado em memória no servidor, sem carregar os dados nacionais no navegador ou depender das APIs de governo durante a visita. `/api/fontes` publica hashes, URLs e cobertura por indicador, sem repetir a proveniência milhares de vezes. O snapshot do piloto é mantido como arquivo histórico.

## Verificação

Testes usam linhas reais do consolidado (incluindo zero, DSEI e esfera estadual), respostas reais APS do piloto e o snapshot publicado. Verificam códigos e UF, duplicatas, separação territorial, ausência versus zero, equivalência do FNS/APS com o piloto e integridade da cobertura nacional. Navegação é testada em desktop e celular, incluindo cidade antes fora do piloto, Fernando de Noronha e Brasília. Nenhuma ingestão eleitoral ou do Bolsa Família faz parte desta atualização.

A cidade continua sendo a entrada do produto. Local de atendimento, residência dos atendidos e destinatário dos recursos são relações distintas. Nenhuma relação regional nova foi inferida. Os dados são observados, sem médias, projeções ou afirmações causais sobre eleições.
