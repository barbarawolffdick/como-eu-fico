# MVP — princípio de produto e critérios permanentes

## Produto mínimo utilizável

O primeiro produto publicável deve permitir que uma pessoa encontre um município brasileiro e veja, **na mesma experiência**, o resultado presidencial municipal e pelo menos um indicador real e auditado de fluxo federal, com contexto territorial.

Não desviar para um dashboard de benefícios sem votos. Não exigir a integração de todos os programas federais antes de oferecer uma interface navegável.

## Funcionalidades essenciais
- Localizar município pelo nome e UF, com identificador territorial inequívoco e URL compartilhável.
- Apresentar votos presidenciais com eleição, turno, candidatos, totais e percentuais corretos e rastreáveis.
- Apresentar série temporal de fluxo federal com rótulos precisos: programa, natureza, unidade, periodicidade, valores, quantidades, fonte e cobertura.
- Contextualizar territorialmente com dado oficial apropriado, explicitando o ano e a unidade.
- Permitir comparação descritiva, sem sugerir causalidade do benefício sobre o voto.
- Mostrar claramente ausências, períodos ainda não publicados, mudanças territoriais e ressalvas de qualidade.
- Oferecer visualização responsiva, acessível e legível.

## Critérios de aceite
- Nenhum número fictício apresentado como real.
- Cada dado público é reproduzível a partir de fonte e transformação declaradas.
- Relações entre dados preservam chaves, granularidades e totais sem multiplicação por JOIN.
- Domínios originais são independentes e não modificados pelas consultas do produto.
- Privacidade protegida; publicação restrita a dados públicos agregados adequados.
- Existe uma URL navegável (ou entrega executável definida pelo usuário), com funcionamento conferido.
- Lacunas e limitações são mostradas ao usuário final sem inferências indevidas.

## Como priorizar trabalho — não é uma fila fixa

A prioridade padrão é **desbloquear a menor fatia funcional que coloque votos e fluxo federal lado a lado**. Antes de fazer a próxima tarefa:

1. Inspecione o estado **atual** do repositório, dos dados e da implantação.
2. Identifique o menor bloqueio real para produzir essa fatia utilizável.
3. Proponha ou implemente a menor mudança testável que remova o bloqueio.
4. Verifique o resultado; informe o que foi entregue e o que falta.
5. Só depois incremente dimensões adicionais de fluxos federais, sempre sem perder a experiência eleitoral.

**Esta seção não afirma que o MVP está ou não está construído, nem fixa 2025/2026 como limite eterno de dados.** Essas informações pertencem aos registros técnicos versionados e às decisões atuais do usuário.
