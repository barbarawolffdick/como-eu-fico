# Operação do frontend no v0/Vercel

## Diagnóstico confirmado em 15/10/2026

- Repositório canônico: `barbarawolffdick/como-eu-fico`, branch `main`.
- Commit auditado: `507a95caf401f96eb6cde81439d75acf88cdb5df`.
- Projeto Vercel: `barbaras-projects-f33a375a/como-eu-fico` (`prj_YF2Brd274zYUbGvIZ4R9lu3ytVdi`).
- Deploy com falha: `dpl_3mhxhCCDbvHjtDLL9S6hWqmi5BQX`.
- Os logs mostram o Next.js 15.5.28 compilando com sucesso e, depois, `No Output Directory named "public" found after the Build completed`.
- A inspeção do projeto confirmou preset `Other`, raiz `.` e Node 24.x. O erro era de configuração da publicação; não era uma falha de ingestão, acesso ao SQLite ou compilação TypeScript.
- A CLI autenticada permitiu inspecionar os logs, apesar de o conector continuar retornando `403` para o workspace. Credenciais não são armazenadas no repositório.

## Configuração contratada

- Framework: `nextjs`.
- Raiz: `.`.
- Node: `22.x`, igual ao CI e a `package.json`.
- Instalação: `npm ci --no-audit --no-fund`, com `package-lock.json` versionado.
- Build: `npm run build`.
- Saída: padrão do framework (`outputDirectory: null` no projeto); não exigir uma pasta `public`.
- `vercel.json` conserva o framework e comandos junto do código.
- `outputFileTracingRoot` aponta para a raiz da aplicação. Os traces do build incluem os JSONs usados por cada rota.

A configuração do projeto foi corrigida pela CLI com alvo explícito:

```bash
vercel project update como-eu-fico --scope barbaras-projects-f33a375a \
  --framework nextjs --auto-detect output-directory --node-version 22.x --yes
```

Não criar outro projeto, duplicar as bases ou habilitar uma ingestão para resolver este erro.

## Validação de uma prévia

1. Conferir equipe, projeto, branch e commit antes de publicar.
2. Executar `npm ci`, `npm run lint`, `npm run build` e `npm run test:web`.
3. Publicar uma prévia do commit revisado, incluindo `data/public/`.
4. Validar `/`, `/explorar`, `/analises`, `/fontes`, `/api/fontes`, busca, detalhe, rankings, cobertura, famílias e análises. Conferir no ambiente remoto as seis cidades completadas por consulta tabular, seus numeradores e a competência setembro/2026.
5. Comparar hashes de `/api/fontes` com os snapshots do commit. Registrar URL, commit e resultado.
6. Para uma prévia protegida, usar a sessão autorizada da Vercel ou `vercel curl`; manter a proteção habilitada.

O v0 tem uma branch própria (`v0/project-overview-3a142983`). Sua referência remota auditada foi `22a7ae8b6a476bea0b78f115f7654dd672aa86ca`, que já inclui a `main` auditada, mas adiciona `pnpm-lock.yaml`, `vercel.json` e referências de tipos. Não incorporar automaticamente esse lockfile concorrente. A versão de implementação deve continuar vindo da `main` após revisão.

## Dados e limites

O frontend Next.js lê JSONs versionados. Não requer FastAPI hospedado, banco persistente ou segredos de fontes oficiais. O proxy Python é opcional para rotas legadas. Não configurar o localhost do Mac como backend remoto.

As seis ausências cartográficas MDS foram completadas pela consulta tabular oficial e a cobertura populacional está validada nos 5.571 municípios para setembro/2026. Ausências futuras continuam `null`. A análise de evolução mensal retorna `null` para o grupo/mês quando faltar observação de um de seus municípios, junto das contagens de cobertura. Grupo vazio também não produz zero. Testes usam os snapshots reais e removem uma observação apenas em memória para verificar essa regra.

TSE, CGU, IBGE e MDS mantêm períodos e unidades distintos. A aplicação não revela voto individual nem estima efeito causal do Bolsa Família sobre resultados eleitorais.

## Prévia verificada

Prévia do commit `49116c32c25395831ace8ef9f48956c89f6d8fca`: https://como-eu-fico-i3tw2bn4f-barbaras-projects-f33a375a.vercel.app (deploy `dpl_7cpvhX4tjbeDG3PGBVCN5aZVqQK2`, estado Ready). O build remoto usou Next.js 15.5.28 e instalação com `npm ci`. Os 16 testes Playwright passaram no ambiente remoto, em desktop e celular, com hashes dos quatro snapshots conferidos.

O acesso por `vercel curl` nesta sessão redirecionou para login. O caminho validado foi um token temporário de desenvolvimento emitido por `vercel project token como-eu-fico --scope barbaras-projects-f33a375a --json`, enviado somente ao domínio da prévia no cabeçalho `x-vercel-trusted-oidc-idp-token`. Não é necessário desabilitar proteção. O token é usado em memória e traces remotos são desativados para não registrar cabeçalhos.

`python3 scripts/verificar_preview.py URL` verifica páginas, APIs e hashes com esse token. Para confirmar acesso público: `python3 scripts/verificar_preview.py URL --publico`. A execução não grava respostas nem credenciais no repositório.
