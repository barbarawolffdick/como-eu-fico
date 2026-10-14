# Como verificar o estado atual — não é um snapshot

**Este arquivo não registra o estado atual do projeto.** Seu objetivo é impedir que um novo assistente trate um relatório histórico como fato contemporâneo.

## Procedimento de reconstrução de contexto

1. Abrir https://github.com/barbarawolffdick/como-eu-fico e ler o README **atual**.
2. Listar branches e pull requests abertos/fechados e identificar qual versão do código é a relevante para a tarefa. Não presumir que um PR citado em conversa antiga segue aberto.
3. Identificar stack e ponto de entrada do produto, scripts de ingestão, camada curada, schemas e testes a partir da árvore atual. Não presumir que um arquivo existe ou não existe sem verificar.
4. Ler o contrato editorial e o catálogo de fontes **na revisão relevante**, considerando que documentos anteriores podem ter sido superados.
5. Para cada fonte, verificar fonte oficial, granularidade, período realmente disponível, local de armazenamento, hashes/manifestos e **última evidência de auditoria reproduzível**.
6. Distinguir relatórios históricos de auditoria de uma execução recente. Uma marca `PASS` atesta somente os testes e o dataset daquela execução.
7. Conferir quais dados ou backups existem no repositório, em arquivos compartilhados na conversa e somente no computador/Colab do usuário; não declarar disponíveis os que não foram acessados.
8. Antes de novos cruzamentos, conferir município de referência, versão territorial, candidaturas/turno eleitoral e consistência de totais.

## Onde encontrar evidências

- Documentos editoriais: `docs/` e `methodology/`.
- Pipelines e auditorias: `scripts/` e `tests/`.
- Relatórios de qualidade, manifestos e artefatos publicados: localizar pela árvore atual do repositório.
- Evidência de mudanças: histórico Git, commits e PRs.
- Bases SQLite e arquivos brutos podem existir **apenas fora do GitHub**. Solicite somente o arquivo necessário, se realmente faltar.

## Como responder a “onde estamos?”

Produzir um diagnóstico curto, datado e **gerado naquele momento**, separando:
- **Confirmado por inspeção** (com caminhos, commits e testes consultados).
- **Informado pelo usuário / relatório histórico** (sem fingir reprodução).
- **Pendente ou não acessível**.
- **Próxima entrega concreta**.

Não copiar números de uma versão anterior deste arquivo como se fossem atuais. Se o usuário precisar congelar uma auditoria, registrar um relatório datado e identificável **separado** destas instruções.

## Referências históricas (não estado atual)

As auditorias sobre TSE, Bolsa Família e IBGE devem ser encontradas nas respectivas metodologias e registros de validação. Esses arquivos indicam o que foi examinado em determinado momento, mas **não constituem memória permanente da versão vigente**.
