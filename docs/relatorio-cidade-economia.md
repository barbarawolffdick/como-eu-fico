# Relatório da cidade — do dinheiro federal à economia local (copy v0)

**Data:** 18/10/2026. **Estado:** proposta editorial, **somente texto**. Não cria indicadores, não autoriza ingestões e não altera a página atual. Segue o [contrato editorial e de dados](contrato-editorial-dados-v1.md) e o [protocolo de evidências](../methodology/protocolo-evidencias.md).

**Pergunta do relatório:** *De onde vem o dinheiro que circula na minha cidade, e o que a minha cidade produz?*

**Recorte:** primeiro o caminho **União → município** (sem estado, por enquanto); depois, **o que esse dinheiro vira em saúde e educação**; por fim, a **economia local** (agro, indústria, serviços, setor público, trabalho e renda).

## Como ler este documento

- `{chaves}` são campos preenchidos pelos dados. Cada campo indica a fonte.
- Os números de **Juazeiro do Norte (CE)** que aparecem como exemplo vêm dos snapshots já publicados (`saude_municipal.json`, `financiamento_saude.json`) e das avaliações feitas no repositório ([Siconfi](../research/avaliacao-siconfi-receitas-municipais.md), [Censo 2022](../research/avaliacao-censo-2022-trabalho.md)). Onde não há número verificado, o exemplo fica em branco: **não inventamos valores**.
- Cada seção tem um **estado**:
  - **Publicado** — já está em `data/public/`.
  - **Avaliado** — fonte testada com consultas reais, ainda não integrada.
  - **A avaliar** — fonte conhecida, ainda não testada pelo projeto.

## Princípios de redação

Lições de iniciativas de dados abertos municipais na Europa e na América Latina (TerriData na Colômbia, SINIM no Chile, Consulta Amigable do MEF no Peru, Presupuesto Abierto na Argentina, Pordata Municípios em Portugal, Where Does My Money Go / OpenSpending no Reino Unido):

1. **Títulos são perguntas que o morador faria.** “De onde vem o dinheiro da prefeitura?”, não “Receitas orçamentárias realizadas”.
2. **Uma escala só: “de cada R$ 100”.** Proporções são entendidas; R$ 1,19 bilhão não é. O valor absoluto aparece como apoio, nunca como manchete.
3. **Toda manchete tem comparação.** Sozinho, um número não significa nada. Comparar com a região imediata, o estado e o Brasil, nessa ordem.
4. **Primeiro a frase, depois o gráfico.** A frase diz o que o gráfico mostra. Quem lê só os títulos e as frases entende o relatório.
5. **Ano e fonte em cada cartão.** A economia de 2023 não é a de 2025. O cartão diz o ano, mesmo que seja antigo.
6. **“O que este dado não diz”** em cada seção. É o que mais gera confiança e o que as outras iniciativas mais esquecem.
7. **Sem adjetivos de julgamento.** Nunca “dependente”, “ineficiente”, “rica”. Diga “pesa mais que no estado” ou “está entre as 10% mais altas do Brasil”.
8. **Ausência não é zero.** “Sem dado para {ano}” sempre, nunca um zero ou um gráfico vazio.
9. **Não somar o que não se soma.** Benefício pago a pessoas, transferência à prefeitura, gasto federal direto e crédito são coisas diferentes. Aparecem lado a lado, nunca como “total investido pela União”.

---

# Parte 1 — Do governo federal à cidade

## 1. Abertura — {Cidade} em uma página

**Estado:** Publicado (população, voto); demais campos dependem das seções abaixo.

> **{Cidade} ({UF})**
> {população} moradores · região imediata de {região imediata}
>
> Aqui você vê de onde vem o dinheiro que circula na cidade, quanto passa pela prefeitura e o que a economia local produz. Os números vêm de fontes oficiais e cada um mostra o ano a que se refere.

**Os números para começar** (cartões, cada um com link para sua seção):

| Cartão | Copy | Fonte |
|---|---|---|
| Economia | A cidade produziu **{PIB}** em {ano}. **{setor principal}** é a maior parte. | IBGE, PIB dos Municípios |
| Pessoas | **{R$ direto às pessoas}** em benefícios federais chegaram a moradores em {ano}. | INSS, CGU (Bolsa Família) |
| Prefeitura | De cada R$ 100 que a prefeitura recebeu, **R$ {x}** vieram do governo federal. | Siconfi (DCA) |
| Saúde | De cada R$ 100 que a cidade gastou em saúde, **R$ {x}** vieram do SUS federal. | SIOPS |
| Educação | {n} alunos em {n} escolas; nota {IDEB} no IDEB dos anos iniciais. | INEP *(a avaliar)* |
| Trabalho | De cada 100 pessoas trabalhando, **{n}** não têm carteira nem CNPJ. | Censo 2022 |
| Voto | {candidato} teve **{%}** dos votos em 2026, 1º turno. | TSE |

**Exemplo — Juazeiro do Norte:** Prefeitura: “De cada R$ 100 que a prefeitura recebeu em 2025, **R$ 41** vieram do governo federal.” Trabalho: “De cada 100 pessoas trabalhando em 2022, **49** não tinham carteira nem CNPJ.” Saúde: “De cada R$ 100 que a cidade gastou em saúde em 2025, **R$ 25** vieram de repasses do SUS federal.”

## 2. Os quatro caminhos do dinheiro federal

**Estado:** texto explicativo, sem dado próprio.

**Título:** Como o dinheiro federal chega a {Cidade}?

> O governo federal não manda “uma verba” para a cidade. O dinheiro chega por quatro caminhos diferentes, que não devem ser somados como se fossem uma coisa só.

| Caminho | Copy curta | Exemplos |
|---|---|---|
| **1. Direto às pessoas** | Vai para a conta de quem mora aqui. A prefeitura não decide como é gasto. | Aposentadorias e pensões do INSS, BPC, Bolsa Família, seguro-desemprego, abono salarial, Pé-de-Meia |
| **2. Para a prefeitura** | Entra no caixa da prefeitura. Parte é de uso livre, parte só pode ir para saúde ou educação. | FPM, SUS fundo a fundo, merenda (PNAE), transporte escolar (PNATE), complementação da União ao FUNDEB, emendas parlamentares |
| **3. Gasto federal na cidade** | A própria União gasta aqui, sem passar pela prefeitura. | Obras do Novo PAC, Minha Casa Minha Vida, universidades e institutos federais, salários de servidores federais |
| **4. Crédito** | Empréstimo, não doação: precisa ser pago. | Crédito rural (Pronaf), financiamento habitacional, BNDES |

**O que esta seção não diz:** quanto cada caminho “vale” no total. Os caminhos têm fontes, anos e regras diferentes e alguns se sobrepõem (um repasse do SUS pode pagar um médico do Mais Médicos, que já é contado em outra fonte).

## 3. Caminho 1 — Dinheiro direto às pessoas

**Estado:** INSS e Bolsa Família **Publicado**; BPC separado, seguro-desemprego e abono **A avaliar**.

**Título:** Quanto dinheiro federal chega direto aos moradores?

> Em {ano}, **{valor}** em benefícios federais foram pagos a pessoas por meio de {Cidade}. É como se cada morador recebesse **R$ {valor por habitante} por mês**, em média. No estado, a média é R$ {UF}.

**Divisão (de cada R$ 100 pagos a pessoas):**

- Aposentadorias e pensões do INSS: R$ {x}
- BPC e benefícios assistenciais: R$ {x}
- Bolsa Família: R$ {x}
- Seguro-desemprego e abono salarial: R$ {x} *(a avaliar)*

**Frase de leitura:**
> Esse dinheiro é gasto principalmente no comércio e nos serviços da cidade. Em lugares com poucos empregos formais, ele pode ser uma das maiores fontes de renda que circula.

**Alcance (Bolsa Família):**
> **{n} de cada 100 moradores** vivem em famílias que recebem o Bolsa Família ({competência}). No Brasil, são {n}.

**O que esta seção não diz:**
- O INSS é contado na cidade da **agência que paga**, não onde a pessoa mora. Em cidades-polo, o valor inclui moradores de cidades vizinhas. Por isso, comparações justas são feitas pela região imediata.
- “Pago” não quer dizer que o dinheiro foi gasto na cidade.

## 4. Caminho 2 — Dinheiro para a prefeitura

**Estado:** FPM, SUS (FNS) e emendas **Publicado**; complementação do FUNDEB, FNDE e visão completa **Avaliado** (Siconfi).

**Título:** Quanto do dinheiro da prefeitura vem do governo federal?

> Em {ano}, a prefeitura de {Cidade} recebeu **{receita total}**. De cada **R$ 100**, **R$ {x}** vieram do governo federal.

**Grade de 100 quadrados — de onde vem cada R$ 100 da prefeitura:**

| Origem | Copy do rótulo | Exemplo Juazeiro do Norte, 2025 |
|---|---|---|
| Governo federal | FPM, SUS, educação e outros repasses da União | R$ 41 |
| Impostos da própria cidade | ISS, IPTU, ITBI e taxas | R$ 18 |
| FUNDEB | Fundo da educação formado por impostos do estado e dos municípios | R$ 14 |
| Governo estadual | Parte do ICMS e do IPVA, repasses de saúde e convênios | R$ 10 |
| Previdência dos servidores | Contribuições e rendimentos do fundo próprio | R$ 8 |
| Outras | Iluminação pública, aplicações, multas, empréstimos e outras | R$ 9 |

*Fonte: Siconfi, Declaração de Contas Anuais, receita líquida das deduções para o FUNDEB. Exemplo: total de R$ 1,19 bilhão.*

**Abrindo o dinheiro federal — o que é livre e o que é carimbado:**

> Nem todo dinheiro federal pode ser usado como a prefeitura quiser.

| Tipo | Copy | Itens |
|---|---|---|
| **Livre** | A prefeitura decide onde gastar, respeitando os mínimos da Constituição. | FPM, ITR |
| **Carimbado** | Só pode ir para uma área definida em lei. | SUS (saúde), FNDE e complementação do FUNDEB (educação) |
| **Negociado** | Depende de um parlamentar ou de um convênio. Varia muito de um ano para outro. | Emendas parlamentares, convênios, transferências especiais |

**Destaque (quando aplicável):**
> A **complementação da União ao FUNDEB** trouxe **{valor}** para a educação de {Cidade} em {ano}. É dinheiro federal que vai para escolas e professores, mesmo que o nome pareça estadual.

*Exemplo Juazeiro do Norte, 2025: R$ 144,2 milhões.*

**Emendas:**
> Em {ano}, parlamentares destinaram **{valor}** pagos a favorecidos de {Cidade}. **{partido}** foi o partido do autor que mais pagou.

**O que esta seção não diz:**
- Os valores são **declarados pela prefeitura** ao Tesouro, que publica sem auditar cada linha. Conferimos FPM e SUS com outras fontes oficiais.
- Receber mais dinheiro federal não quer dizer que a cidade é mais ou menos bem administrada. Cidades menores e mais pobres recebem, por lei, mais FPM por habitante.
- Emenda paga a um favorecido da cidade não prova que o recurso foi aplicado aqui.

> **E o que esse dinheiro vira?** O SUS e os repasses de educação aparecem em detalhe na Parte 2.

## 5. Caminho 3 — Gasto federal direto na cidade

**Estado:** **A avaliar** (MCMV e obras foram mapeados em [mapa da presença federal](../research/mapa-presenca-federal-v1.md), sem integração).

**Título:** O que o governo federal construiu ou mantém aqui?

> Além do dinheiro que passa pela prefeitura, a União gasta diretamente na cidade: obras, moradias, universidades e servidores federais.

| Cartão | Copy | Fonte |
|---|---|---|
| Moradia | **{n} moradias** do Minha Casa Minha Vida aparecem como entregues; **{n}** ainda estão em obra. | Ministério das Cidades |
| Obras | **{n} obras** do Novo PAC na cidade: {n} concluídas, {n} em andamento, {n} paradas. | Novo PAC / Obrasgov |
| Ensino federal | {Cidade} tem {campus da universidade / instituto federal}. | MEC |
| Servidores federais | **{n} servidores federais** trabalham aqui. | Portal da Transparência / RAIS |

**O que esta seção não diz:** valor contratado não é obra pronta. Mostramos sempre o estágio (contratado, pago, entregue).

## 6. Caminho 4 — Crédito

**Estado:** **A avaliar.**

**Título:** Quanto crédito com apoio federal chegou aqui?

> Em {ano}, produtores de {Cidade} contrataram **{valor}** em crédito rural, sendo **{valor}** pelo Pronaf, a linha para agricultura familiar. Crédito é empréstimo: precisa ser pago e não se soma às transferências.

*Fonte: Banco Central, Matriz de Dados do Crédito Rural (Sicor), por município.*

## 7. A volta — quanto de imposto federal sai daqui?

**Estado:** **A avaliar**, com alto risco de leitura errada. Recomendação: só publicar se a fonte permitir atribuição honesta.

**Título:** E quanto a cidade manda para o governo federal?

> Esta é a pergunta que todo mundo faz. A resposta honesta é difícil: os impostos federais são registrados onde a **empresa tem sede**, não onde o produto foi feito ou comprado. Uma fábrica em {Cidade} com sede em São Paulo paga “em São Paulo”.

**Regra editorial:** não publicar “a cidade recebe mais do que paga” nem o contrário com dados de arrecadação por município. Se publicado, o cartão precisa da ressalva acima, em destaque, junto do número.

## 8. Para onde vai o dinheiro da prefeitura

**Estado:** **A avaliar** (Siconfi, DCA, despesa por função; RGF para pessoal).

**Título:** Em que a prefeitura gasta?

> De cada **R$ 100** que a prefeitura gastou em {ano}:

- Educação: R$ {x} — a lei exige pelo menos R$ 25 dos impostos
- Saúde: R$ {x} — a lei exige pelo menos R$ 15 dos impostos
- Administração: R$ {x}
- Previdência dos servidores: R$ {x}
- Urbanismo, saneamento e transporte: R$ {x}
- Assistência social: R$ {x}
- Outros: R$ {x}

> **Pessoal:** a prefeitura usa **{x}%** da receita para pagar salários. O limite da Lei de Responsabilidade Fiscal é 54%.

**O que esta seção não diz:** os mínimos legais de saúde e educação são calculados sobre os impostos, não sobre toda a receita. A conta oficial do mínimo vem de outros sistemas (SIOPS para saúde, SIOPE para educação) e pode ser diferente da divisão acima. A Parte 2 abre essas duas áreas.

---

# Parte 2 — Do dinheiro ao serviço: saúde e educação

Saúde e educação são as duas áreas em que o dinheiro federal tem carimbo: só pode ser usado nelas. São também as que o morador sente no dia a dia. Por isso ganham parte própria, seguindo os [níveis de evidência](contrato-editorial-dados-v1.md#7-níveis-de-evidência-para-a-experiência-do-cidadão) do contrato: **financiamento → estrutura → alcance → resultado**. Cada cartão diz em que nível está.

## 9. Saúde — do repasse federal ao posto de saúde

**Estado:** quase tudo **Publicado** ([saúde nacional](../methodology/saude-nacional.md), [financiamento e estrutura](../methodology/financiamento-saude.md)). Falta o nível de resultado (atendimentos, vacinação, mortalidade), **A avaliar**.

**Título:** O que o dinheiro federal faz pela saúde de {Cidade}?

### 9.1 Quanto chegou (financiamento)

> Em {ano}, o Ministério da Saúde depositou **{valor}** no fundo de saúde de {Cidade}. Em relação a {ano anterior}, foi **{x}% {a mais / a menos}**, sem descontar a inflação.

> De janeiro a {mês} de {ano corrente}, já chegaram **{valor}**, ou **R$ {x} por morador**.

*Exemplo Juazeiro do Norte: R$ 132,1 milhões em 2025, 11,8% a mais que em 2024 (R$ 118,2 milhões). De janeiro a julho de 2026, R$ 73,5 milhões, ou R$ 239 por morador.*

**Para quê (de cada R$ 100 do SUS federal):**

| Área | Copy do rótulo | Juazeiro, 2025 |
|---|---|---|
| Hospitais e especialistas | Consultas com especialistas, exames, cirurgias e internações (“média e alta complexidade”) | R$ 43 |
| Atenção primária | Postos de saúde, equipes de saúde da família, agentes comunitários | R$ 42 |
| Gestão do SUS | Organização da rede, sistemas e apoio à gestão | R$ 9 |
| Vigilância | Vacinação, combate a dengue e outras doenças, vigilância sanitária | R$ 6 |
| Remédios | Assistência farmacêutica | menos de R$ 1 |

> **Emendas:** **{x}%** desse dinheiro veio de emendas parlamentares. *Juazeiro: 1,9% em 2025; 6,6% de janeiro a julho de 2026.*

### 9.2 Quem paga a saúde da cidade (financiamento)

> Em {ano}, a prefeitura gastou **{valor}** em saúde. De cada **R$ 100**:

| Origem | Juazeiro, 2025 |
|---|---|
| Impostos e transferências de impostos (a parte que a lei obriga a cidade a pôr na saúde) | R$ 58 |
| **Repasses do SUS federal** | **R$ 25** |
| Recursos livres da prefeitura | R$ 14 |
| Repasses do SUS estadual | R$ 3 |
| Outros e convênios | menos de R$ 1 |

*Fonte: SIOPS, despesas liquidadas de 2025 (R$ 311,2 milhões em Juazeiro).*

> **Frase de leitura:** a maior parte da saúde é paga com impostos. Mas boa parte desses impostos é o FPM, que também vem da União. Por isso o peso federal real é maior que os R$ {x} da linha do SUS. *(Não somar as linhas: o FPM está dentro de “impostos e transferências”, sem separação na fonte.)*

### 9.3 O que existe na cidade (estrutura)

| Cartão | Copy | Juazeiro |
|---|---|---|
| Postos | **{n} Unidades Básicas de Saúde** e {n} postos atendem pelo SUS. | 51 UBS |
| Locais SUS | **{n} locais** com atendimento ambulatorial SUS. | 156 |
| Leitos | **{n} leitos SUS**, dos quais **{n} de UTI**, em {n} hospitais ({mês/ano}). | 500 leitos, 58 de UTI, 8 hospitais (ago/2026) |
| Exames | {n} locais fazem **{exame}** pelo SUS. | Ressonância: 2 locais; mamografia: 7; tomografia: 6 |

> **Cidade-polo (quando aplicável):** {hospital}, de gestão estadual, tem **{n} dos {n} leitos SUS** da cidade. Hospitais regionais costumam receber também moradores de cidades vizinhas; o cadastro não informa onde os pacientes moram. *Juazeiro: o Hospital Regional do Cariri tem 234 dos 500 leitos SUS e 50 das 58 UTIs.*

### 9.4 Quem atende (alcance)

| Cartão | Copy | Juazeiro |
|---|---|---|
| Equipes | **{n} equipes de Saúde da Família** reconhecidas pelo Ministério; **{n}** recebem dinheiro federal. | 80 reconhecidas, 77 com apoio federal (parcela out/2026) |
| Outras equipes | {n} equipes de atenção primária e {n} equipes multiprofissionais (psicólogos, fisioterapeutas, nutricionistas e outros). | 8 e 7 |
| Mais Médicos | **{n} vagas** do Mais Médicos ocupadas. | 23 (09/10/2026) |

### 9.5 O que mudou na saúde das pessoas (resultado)

**Estado:** **A avaliar.** Candidatos, todos do Ministério da Saúde: cobertura vacinal infantil (SI-PNI), mortalidade infantil (SIM e Sinasc), pré-natal adequado (Sinasc), internações por condições sensíveis à atenção primária (SIH).

> Em {ano}, **{x} de cada 100 bebês** de {Cidade} tomaram todas as vacinas do primeiro ano. A meta do Ministério é {x}.

> A mortalidade infantil foi de **{x} por mil nascidos vivos**. No estado, {x}.

**O que esta seção não diz:**
- Dinheiro, prédio e equipe cadastrados não provam atendimento. Atendimento não prova melhora na saúde.
- Leitos e exames ficam onde está o hospital, não onde mora o paciente.
- Mais vagas do Mais Médicos não quer dizer mais médicos no total: o programa é uma parte dos médicos do SUS.
- Em cidades pequenas, mortalidade infantil varia muito de um ano para outro com poucos casos. Mostrar média de três anos.

## 10. Educação — do repasse federal à sala de aula

**Estado:** **A avaliar**, com uma exceção: a complementação da União ao FUNDEB está **Avaliada** (Siconfi). As fontes do FNDE estão no [mapa da presença federal](../research/mapa-presenca-federal-v1.md) (PNAE, PNATE, PNLD, obras), sem integração. É a maior lacuna do relatório.

**Título:** O que o dinheiro federal faz pela educação de {Cidade}?

### 10.1 Quanto chegou (financiamento)

> Em {ano}, a educação de {Cidade} recebeu **{valor}** do governo federal:

| Linha | Copy do rótulo | Fonte | Juazeiro, 2025 |
|---|---|---|---|
| Complementação da União ao FUNDEB | Dinheiro extra para cidades onde o valor por aluno fica abaixo do mínimo nacional | Siconfi / FNDE | R$ 144,2 milhões |
| Salário-educação | Contribuição das empresas, repartida pelo número de alunos | FNDE | {valor} |
| Merenda (PNAE) | Valor por aluno por dia letivo para comprar alimentos. Parte deve vir da agricultura familiar | FNDE | {valor} |
| Transporte escolar (PNATE) | Ajuda para levar alunos da zona rural | FNDE | {valor} |
| Dinheiro direto na escola (PDDE) | Vai direto para a escola fazer pequenos reparos e compras | FNDE | {valor} |
| Obras e creches | Construção de escolas e creches | FNDE / Novo PAC | {valor} |

> **Destaque:** a complementação da União ao FUNDEB é de longe o maior repasse federal à educação em muitas cidades. *Juazeiro: R$ 144,2 milhões em 2025, mais que todo o SUS federal da cidade no mesmo ano (R$ 132,1 milhões).*

> **Merenda e agricultura local:** **{x}%** do dinheiro federal da merenda comprou alimentos da agricultura familiar. A lei exige pelo menos 30%. *(Liga a educação à Parte 3, agropecuária.)*

### 10.2 Quem paga a educação da cidade (financiamento)

> De cada **R$ 100** que a prefeitura gastou em educação em {ano}, **R$ {x}** vieram do FUNDEB, **R$ {x}** de impostos próprios e **R$ {x}** de programas federais. A cidade aplicou **{x}%** dos impostos em educação; a Constituição exige 25%.

*Fonte: SIOPE (FNDE).*

### 10.3 O que existe na cidade (estrutura)

| Cartão | Copy | Fonte |
|---|---|---|
| Escolas | **{n} escolas**: {n} municipais, {n} estaduais, {n} federais e {n} particulares. | INEP, Censo Escolar |
| Alunos | **{n} alunos** na rede pública; {x} de cada 10 na rede municipal. | INEP, Censo Escolar |
| Creche | **{n} crianças** de 0 a 3 anos em creche. | INEP, Censo Escolar |
| Infraestrutura | De cada 10 escolas públicas, **{n}** têm internet para os alunos, **{n}** têm biblioteca e **{n}** têm quadra. | INEP, Censo Escolar |
| Ensino federal | {campus de universidade / instituto federal}, com {n} alunos. | INEP, Censo da Educação Superior |

### 10.4 Quem é atendido (alcance)

| Cartão | Copy | Fonte |
|---|---|---|
| Merenda | **{n} alunos** recebem merenda com dinheiro do PNAE. | FNDE |
| Transporte | **{n} alunos** da zona rural contam com o transporte escolar. | FNDE |
| Pé-de-Meia | **{n} estudantes** do ensino médio recebem o incentivo do Pé-de-Meia. | MEC |

### 10.5 O que os alunos aprendem (resultado)

> Na rede pública de {Cidade}, o IDEB dos anos iniciais (1º ao 5º ano) foi **{x}** em {ano}. No estado, {x}; no Brasil, {x}.

> **{x} de cada 100 alunos** estão dois anos ou mais atrasados para a idade (distorção idade-série).

> **Alfabetização:** {x}% das crianças alfabetizadas ao fim do 2º ano. *(Indicador Criança Alfabetizada, INEP.)*

> **Adultos:** em 2022, **{x}%** das pessoas de 15 anos ou mais não sabiam ler e escrever. *(Censo 2022.)*

**O que esta seção não diz:**
- O ensino fundamental é dividido entre prefeitura e estado. O IDEB da “rede pública” mistura as duas. Mostrar a rede municipal separada sempre que a fonte permitir.
- O dinheiro do FNDE para a merenda é complemento: não paga toda a merenda. Repasse não prova refeição servida.
- O IDEB depende de muitos fatores além da escola (renda, escolaridade dos pais). Uma nota maior não prova que um programa funcionou.

# Parte 3 — A economia da cidade

## 11. O que a cidade produz

**Estado:** PIB total **Publicado** (2023 observado, 2025 estimado e rotulado); divisão por setor **A avaliar** (mesma fonte do IBGE, outras variáveis).

**Título:** De onde vem a riqueza produzida em {Cidade}?

> Em {ano}, a economia de {Cidade} produziu **{PIB}**. De cada **R$ 100** produzidos aqui:

| Setor | Copy do rótulo |
|---|---|
| **Agropecuária** | Lavouras, criação de animais, pesca e extração vegetal |
| **Indústria** | Fábricas, construção, mineração, energia e água |
| **Serviços** | Comércio, transporte, bancos, saúde e educação privadas, turismo |
| **Administração pública** | Prefeitura, governos estadual e federal, escolas e postos públicos, previdência |
| **Impostos sobre produtos** | Parte do valor que vira imposto, não é de nenhum setor |

**Frases de leitura (escolhidas por regra, nunca à mão):**

- Se agropecuária ≥ R$ 30 de cada R$ 100: *“O campo é o motor da economia de {Cidade}: R$ {x} de cada R$ 100 vêm da agropecuária, contra R$ {x} no Brasil.”*
- Se indústria ≥ R$ 35: *“{Cidade} é uma cidade industrial: R$ {x} de cada R$ 100 vêm da indústria.”*
- Se administração pública ≥ R$ 35: *“O setor público é a maior atividade econômica de {Cidade}: R$ {x} de cada R$ 100 vêm de prefeitura, escolas, postos e outros órgãos públicos.”*
- Caso contrário: *“Como a maior parte do Brasil, {Cidade} vive principalmente de comércio e serviços.”*

> **Por que a administração pública aparece como setor?** Professores, médicos de postos e servidores produzem serviços. O IBGE mede esse trabalho pelo que custa (principalmente salários). Em muitas cidades pequenas, é a maior atividade da economia.

**PIB por habitante:**
> Dividido pelos moradores, o PIB de {Cidade} é **R$ {x} por pessoa**, {acima/abaixo} da média do estado (R$ {x}).

**O que esta seção não diz:**
- **PIB não é renda dos moradores.** Uma refinaria ou usina pode deixar o PIB por habitante muito alto sem que a população seja rica. A renda está na seção 16.
- O PIB municipal sai com dois anos de atraso. Quando estimado, o cartão mostra **“estimativa”** e o método.

## 12. Agropecuária — o que o campo produz

**Estado:** **A avaliar** (IBGE: Produção Agrícola Municipal, Pesquisa da Pecuária Municipal, Produção da Extração Vegetal e da Silvicultura; Censo Agropecuário 2017; Banco Central, Sicor).

**Título:** O que se planta e se cria em {Cidade}?

> Em {ano}, as lavouras de {Cidade} produziram **{valor da produção}**. As principais foram:
>
> 1. {cultura 1} — {quantidade} · {valor} ({x}% do valor das lavouras)
> 2. {cultura 2} — …
> 3. {cultura 3} — …

> O rebanho tinha **{n} cabeças de gado**, {n} de {outro rebanho} e produziu {n} litros de leite.

> **Quem produz:** o último Censo Agropecuário (2017) contou **{n} estabelecimentos rurais**; **{n} de cada 10** eram de agricultura familiar.

> **Crédito:** {valor} em crédito rural em {ano}, {x}% pelo Pronaf.

**O que esta seção não diz:** o valor da produção agrícola não é o mesmo que a agropecuária no PIB (a seção 11 desconta insumos). O Censo Agropecuário é de 2017; o cartão mostra o ano.

## 13. Indústria — o que se fabrica e se extrai

**Estado:** **A avaliar** (RAIS por atividade; royalties de mineração e petróleo: ANM e ANP).

**Título:** Que indústrias existem em {Cidade}?

> As indústrias de {Cidade} empregavam **{n} pessoas com carteira** em {ano}. As atividades que mais empregam são {atividade 1}, {atividade 2} e {atividade 3}.

**Royalties (só aparece se houver):**
> {Cidade} recebeu **{valor}** em royalties de {mineração/petróleo} em {ano}. É uma compensação pela extração de recursos naturais do território, paga pela União conforme a produção, e pode variar muito com o preço internacional.

**O que esta seção não diz:** a RAIS conta empregos onde o estabelecimento está registrado. Grandes empresas podem registrar empregados numa unidade diferente de onde trabalham.

## 14. Comércio e serviços

**Estado:** **A avaliar** (RAIS; Receita Federal, CNPJ; ISS via Siconfi, **Avaliado**).

**Título:** Quem vende e presta serviços em {Cidade}?

> {Cidade} tem **{n} empresas ativas**, sendo **{n} MEIs** (microempreendedores individuais). Os setores com mais empregos com carteira são {setor 1}, {setor 2} e {setor 3}.

> **O imposto que mostra a economia:** a prefeitura arrecadou **{ISS}** de ISS, o imposto sobre serviços, e **{IPTU}** de IPTU, o imposto sobre imóveis. *Exemplo Juazeiro do Norte, 2025: ISS de R$ 94,6 milhões, o principal imposto próprio, compatível com uma economia de serviços.*

**Cidade-polo (quando aplicável):**
> {Cidade} é polo da região de {região imediata}: atende moradores de {n} cidades vizinhas em comércio, saúde e educação.

## 15. Trabalho — quem trabalha e como

**Estado:** **Avaliado** (Censo 2022, tabela 10261; RAIS 2025).

**Título:** Como as pessoas de {Cidade} trabalham?

> Em 2022, **{n} pessoas** estavam trabalhando em {Cidade}. De cada **100**:

| Grupo | Copy | Juazeiro do Norte, 2022 |
|---|---|---|
| Com carteira assinada | Empregados do setor privado e domésticos com carteira | 32 |
| Setor público | Servidores, militares e funcionários de estatais | 11 |
| Com CNPJ | Empregadores e quem trabalha por conta própria com empresa aberta | 8 |
| **Informais** | Sem carteira e sem CNPJ, incluindo quem ajuda a família sem salário | **49** |

> A informalidade em {Cidade} é de **{x}%**. No estado, {x}%; no Brasil, {x}%.
> *Exemplo Juazeiro do Norte: 48,8%; Ceará, 48,3%; Brasil, 36,3%.*

**Quem emprega com carteira (RAIS):**
> Dos empregos formais, **{x} de cada 10** estão no setor público. No Brasil, são {x}.

**O que esta seção não diz:**
- É uma fotografia de 2022. Para o movimento recente, usamos admissões e demissões com carteira (Novo Caged), que não incluem servidores nem informais.
- “Informal” é a definição oficial do IBGE, não um julgamento sobre o trabalho de ninguém.

## 16. Renda — quanto as famílias têm para viver

**Estado:** **A avaliar** (Censo 2022, rendimento; RAIS, massa salarial; benefícios já publicados).

**Título:** Quanto as famílias de {Cidade} têm para viver?

> Em 2022, metade dos moradores de {Cidade} vivia com até **R$ {mediana} por pessoa por mês** na família. No Brasil, eram R$ {x}.

**De onde vem a renda que circula:**
> Comparando fontes diferentes, em {ano}:
> - salários de empregos com carteira: **{massa salarial RAIS}**
> - benefícios do INSS pagos aqui: **{valor}**
> - Bolsa Família: **{valor}**

> Para cada **R$ 100** pagos em salários com carteira, **R$ {x}** chegaram em benefícios federais.

**O que esta seção não diz:** essa comparação deixa de fora a renda informal e os lucros, que não têm fonte municipal confiável. Não é “a renda da cidade”; é o peso relativo de duas fontes que conseguimos medir.

## 17. Síntese — o motor da economia de {Cidade}

**Estado:** depende das seções 4, 9, 11 e 15. Regras de classificação **públicas e fixas**, revisadas antes de publicar.

**Título:** Em resumo: como funciona a economia de {Cidade}?

> **{Frase-síntese}**

Modelos de frase-síntese (escolhidos por regra, a partir das seções anteriores):

- *“{Cidade} produz principalmente no campo. A agropecuária gera R$ {x} de cada R$ 100, e a maior parte dos empregos com carteira está em {setor}. A prefeitura depende do governo federal para R$ {x} de cada R$ 100 que recebe.”*
- *“{Cidade} é um polo de comércio e serviços. O ISS é o principal imposto da prefeitura e {x} de cada 100 trabalhadores estão em serviços. Metade dos trabalhadores é informal.”*
- *“{Cidade} é polo de saúde e de serviços da região de {região imediata}: concentra {n} dos {n} leitos SUS da região, e o ISS é o principal imposto da prefeitura.”*
- *“Em {Cidade}, o setor público e as transferências sustentam boa parte da economia: a administração pública gera R$ {x} de cada R$ 100 do PIB, e R$ {x} de cada R$ 100 da prefeitura vêm da União.”*

**Comparar com cidades parecidas:**
> Cidades da região de {região imediata} com tamanho parecido: {cidade A}, {cidade B}, {cidade C}. [Comparar lado a lado]

**Regra editorial:** a síntese descreve a estrutura, nunca a qualidade da gestão nem o que os moradores pensam. Proibido: “dependente”, “pobre”, “eficiente”, “vive do governo”.

## 18. Este relatório e o voto

**Estado:** Publicado (voto); cruzamentos regionais já existentes na página de dinheiro federal.

> Em 2026, {candidato} teve **{%}** dos votos em {Cidade}. Ao lado dos dados da economia, o voto ajuda a perguntar se cidades com perfis econômicos diferentes votaram de forma diferente.

> **Atenção:** o resultado da cidade não diz por que cada pessoa votou. Que o dinheiro federal pese mais numa cidade e um candidato tenha mais votos ali não prova que uma coisa causou a outra.

## 19. Fontes, datas e glossário

**Copy do rodapé:**
> Todos os números vêm de fontes oficiais públicas, com o ano de cada um. Quando uma fonte não tem dado para a cidade, mostramos “sem dado”, nunca zero. [Ver fontes e metodologia]

**Glossário mínimo (tooltip em cada termo):**

| Termo | Definição em uma frase |
|---|---|
| FPM | Parte do Imposto de Renda e do IPI que a Constituição manda a União dividir com os municípios. |
| FUNDEB | Fundo que junta impostos do estado e dos municípios e redistribui para a educação básica, com complemento da União. |
| SUS fundo a fundo | Dinheiro do Ministério da Saúde depositado no fundo municipal de saúde. |
| ISS | Imposto da prefeitura sobre serviços (oficinas, escolas particulares, clínicas, bancos). |
| IPTU | Imposto da prefeitura sobre imóveis urbanos. |
| PIB | Valor de tudo o que foi produzido na cidade em um ano, descontados os insumos. |
| Valor adicionado | A parte do PIB gerada por um setor (agro, indústria, serviços ou administração pública). |
| Informal | Quem trabalha sem carteira assinada e sem CNPJ, pela definição do IBGE. |
| Emenda parlamentar | Parte do orçamento federal que deputados e senadores indicam para um lugar ou entidade. |
| Região imediata | Grupo de cidades vizinhas ligadas a uma cidade-polo, definido pelo IBGE. |
| Atenção primária | A porta de entrada do SUS: postos, equipes de saúde da família e agentes comunitários. |
| Média e alta complexidade | Especialistas, exames, cirurgias e internações. |
| UBS | Unidade Básica de Saúde, o “posto de saúde”. |
| SIOPS / SIOPE | Sistemas em que a prefeitura declara quanto gastou em saúde e em educação. |
| Censo Escolar | Levantamento anual do INEP sobre escolas, alunos e professores. |
| IDEB | Nota de 0 a 10 que junta aprendizado (prova do SAEB) e aprovação dos alunos. |

---

## Mapa de fontes e prioridade

| # | Seção | Fonte | Estado | Prioridade |
|---|---|---|---|---|
| 3 | Direto às pessoas | INSS (Previdência), Bolsa Família (MDS, CGU) | Publicado | — |
| 4 | Prefeitura: FPM, SUS, emendas | Tesouro, FNS, CGU | Publicado | — |
| 9.1–9.4 | Saúde: financiamento, estrutura, equipes | FNS, SIOPS, CNES, APS, Mais Médicos | Publicado | — |
| 4 | Prefeitura: visão completa (de cada R$ 100) | Siconfi, DCA Anexo I-C | Avaliado | **1** |
| 11 | PIB por setor | IBGE, PIB dos Municípios (tabela 5938, valor adicionado por setor) | A avaliar (mesma tabela já usada) | **2** |
| 10.1 | Educação: complementação da União ao FUNDEB | Siconfi (junto com a prioridade 1) / FNDE | Avaliado | **1** |
| 10.1, 10.4 | Educação: PNAE, PNATE, PDDE, salário-educação | FNDE, dados abertos | A avaliar (fonte confirmada no mapa) | **4** |
| 10.3, 10.5 | Educação: escolas, alunos, IDEB | INEP, Censo Escolar e IDEB | A avaliar | **4** |
| 15 | Trabalho e informalidade | Censo 2022, tabela 10261 | Avaliado | **3** |
| 13–15 | Emprego formal por setor | RAIS 2025 | Avaliado (microdados grandes) | 5 |
| 9.5 | Saúde: vacinação, mortalidade infantil, pré-natal | SI-PNI, SIM, Sinasc | A avaliar | 5 |
| 10.2 | Educação: gasto e mínimo de 25% | SIOPE | A avaliar | 6 |
| 12 | Agropecuária | IBGE PAM, PPM, PEVS; Censo Agro 2017 | A avaliar | 6 |
| 6, 12 | Crédito rural | Banco Central, Sicor | A avaliar | 6 |
| 8 | Despesa por função, pessoal | Siconfi, DCA e RGF | A avaliar | 7 |
| 16 | Renda | Censo 2022, rendimento | A avaliar | 8 |
| 3 | BPC separado, seguro-desemprego, abono | CGU, MTE | A avaliar | 9 |
| 5 | MCMV, Novo PAC | Ministério das Cidades, Obrasgov | A avaliar | 10 |
| 13 | Royalties | ANM (CFEM), ANP | A avaliar | 11 |
| 14 | Empresas e MEI | Receita Federal, CNPJ | A avaliar | 12 |
| 7 | Arrecadação federal por município | Receita Federal | A avaliar, alto risco | por último |

**Critério da prioridade:** primeiro o que já foi avaliado ou usa uma fonte já integrada (Siconfi, tabela 5938, Censo 2022), porque as seções 4, 11 e 15 sozinhas já respondem às duas perguntas do relatório: *de onde vem o dinheiro* e *o que a cidade produz*. A saúde (seção 9) já está publicada e só precisa ser reescrita nesta voz. A educação (seção 10) é a maior lacuna: depois do FUNDEB, que sai junto com o Siconfi, FNDE e INEP vêm logo em seguida. As demais aprofundam.

Cada fonte passa pelas [condições para ser implementável](catalogo-fontes-v0.md#condições-para-promover-uma-fonte-a-implementável) antes de entrar no site.
