# Sistema de design

Implementado na aplicação Next.js, sem biblioteca de interface adicional. Preserva o verde, os fundos claros e a tipografia editorial da experiência municipal. Atomic Design orienta a responsabilidade: fundamentos → peças reutilizáveis → composição da funcionalidade. Não há pastas para preencher categorias.

## Fonte de verdade

- `app/styles/tokens.css`: cores semânticas, tipografia, espaçamento, bordas, dimensões, sombras, camadas e movimento. Altere aqui para mudar o conjunto.
- `app/styles/components.css`: base acessível e aparência compartilhada.
- `app/styles/screens.css`: arranjos responsivos e composições específicas das telas; consome os tokens.
- `app/globals.css`: importa essas camadas nessa ordem.

Use `--color-text-muted`, `--color-action`, `--color-negative` e outros nomes de intenção. Não crie paletas por página. Cores de cidade A/B identificam lados da comparação; cores de aumento/redução indicam direção, sem afirmar que o resultado é bom ou ruim. Seta e texto acompanham a cor. Os tokens de texto foram escolhidos para contraste AA nos fundos correspondentes.

Use `--space-*` para espaçamento, `--size-*` para dimensões funcionais e a escala `--font-size-*` para texto. A legenda mínima é 12px na configuração padrão do navegador; o corpo é 16px. Breakpoints de composição são 48em e 64em. Dimensões relativas, frações de grid e percentuais de dados não exigem novos tokens. Barras mantêm largura calculada por dados; a posição do tooltip depende da janela. Essas medidas não pertencem à escala visual.

## Peças disponíveis

Importe diretamente de `app/components/ui/`:

| Peça | Quando usar |
| --- | --- |
| `Button`, `ActionLink` (`button.tsx`) | Ação usa botão; navegação usa link. Variantes `primary`, `secondary`, `quiet`; tamanhos `default`, `compact`, `icon`. Ícones sem texto precisam de nome acessível. |
| `Card`, `CardLink` (`card.tsx`) | Conteúdo agrupado ou card inteiro navegável. Tons `default`, `muted`, `accent`, `warm`. `as` permite artigo, seção, aside ou div conforme a semântica. Não aninhe controles em `CardLink`. |
| `SelectField` (`select-field.tsx`) | Select nativo com label associado; `hint` e `error` vinculados por descrição acessível. Mantém atributos nativos, inclusive `disabled`. |
| `Feedback` (`feedback.tsx`) | `loading`, `error`, `empty`, `notice`. Erro anuncia alerta; carregamento anuncia status. Componha uma ação em `action`, quando houver saída ou nova tentativa. |
| `DataBar` (`data-bar.tsx`) | Uma magnitude, com limites seguros. Passe `label` quando precisar ser anunciada; sem label é decorativa e deve ter o valor escrito ao lado. |
| `ChangeIndicator` (`change-indicator.tsx`) | Variação percentual: `badge` para destaque, `inline` em listas. `null` é indisponibilidade, zero é estabilidade. |
| `TermHelp` (`term-help.tsx`) | Explicação complementar com mouse, toque e teclado. Escape fecha; a explicação essencial continua no texto da tela. |

`TermHelp` usa modal para conteúdos longos (mais de 160 caracteres), ou quando recebe `presentation="dialog"`. Textos curtos continuam como tooltip em portal fora dos contêineres. O modal usa `<dialog>`, limita largura/altura à janela, contém o foco, oferece botão de fechar e devolve o foco ao acionador. Não dependa de hover para abrir explicações extensas. `HelpDialog` pode ser importado diretamente quando o formato modal for parte da interação.

Exemplo:

```tsx
import { Card } from "@/app/components/ui/card";
import { ActionLink } from "@/app/components/ui/button";

<Card as="section" tone="muted" aria-labelledby="dados-titulo">
  <h2 id="dados-titulo">Conheça os dados da cidade</h2>
  <p>Confira o período e a fonte de cada indicador.</p>
  <ActionLink href="/fontes">Sobre os dados →</ActionLink>
</Card>
```

Tabelas continuam HTML nativo: envolva em `.table-scroll`, aplique `.data-table` e use `.data-table--wide` quando as colunas precisarem de rolagem local. Use cabeçalhos e caption ou nome acessível quando necessário. Não crie componentes de tabela com configurações complexas. `.kicker`, `.hint`, `.footnote` e `.sr-only` são utilitários tipográficos compartilhados.

## Visualização de dados

Gráficos usam a família `--color-viz-*` (18/10/2026). Os tokens `--color-chart*` continuam valendo para as barras de indicador simples (`DataBar`), mas têm pouca saturação e não servem para distinguir categorias.

- **Categorias** (`--color-viz-1` a `--color-viz-4`, nesta ordem): verde, âmbar, azul e terracota. A cor acompanha a entidade em todas as páginas (por exemplo, pessoas em verde e prefeitura em azul no fluxo do dinheiro federal). Nunca colorir por posição no ranking. Mais de quatro categorias viram “outros”, rótulos diretos ou tabela.
- **Magnitude** de uma série (`--color-viz-seq-1` a `--color-viz-seq-5`): mais escuro é mais. Texto sobre `seq-4` e `seq-5` usa `--color-text-inverse`; sobre os demais, `--color-text`.
- **Fundo de trilha e “restante”**: `--color-viz-track`.
- **Destaque da cidade** em gráficos com muitos pontos: `--color-text`, com contorno `--color-surface`.
- **Voto**: candidatos não recebem cores partidárias nem cores por posição; segmentos na mesma cor, separados por espaço e com nome escrito.
- `--color-viz-2` (âmbar) tem contraste abaixo de 3:1 sobre branco: sempre com rótulo visível ou tabela.

## Composição e estados

Busca municipal, seções da cidade, indicadores de saúde, comparação e filtros continuam próximos das funcionalidades. Reutilize ou amplie uma peça existente antes de extrair outra. Conteúdo e cor diferentes não são novas responsabilidades. Uma composição só vira componente compartilhado se houver repetição relevante.

Preserve dados e regras: ausência não vira zero; falha de consulta oferece recuperação; carregamento tem status; comparação exige períodos compatíveis; seleção usa atributos nativos ou `aria-pressed`/`aria-selected` conforme o controle. Não duplique essa lógica dentro das peças visuais.

Foco visível, controles nativos, link para pular ao conteúdo, labels e movimento reduzido fazem parte da base. Não remova outlines sem substituição. As tabelas extensas rolam dentro do seu contêiner; o restante da página se reorganiza no celular.

## Aplicação e manutenção

Os padrões já são usados na entrada, cidade (panorama e temas), exploração nacional, comparação, análises e fontes, inclusive mensagens de falha e carregamento. Foram consolidados botões/links de ação, cards, selects, barras, indicadores de variação, tabelas e mensagens antes dispersos; `TermHelp` tem uma única implementação.

Antes de concluir uma mudança:

1. Procure a peça existente e utilize tokens; deixe apenas a composição nos estilos da tela.
2. Verifique teclado, foco, nomes acessíveis, estados pertinentes e legibilidade no celular.
3. Execute `npm run lint`, `npm run build` e `npm run test:web`. O teste web usa a aplicação compilada, em desktop e Pixel 7, e salva capturas em `test-results/`.

`npm run check:design` (também incluído no lint) bloqueia cores literais e tamanhos tipográficos locais no CSS, além de botões e selects nativos fora das implementações compartilhadas. É uma proteção focada, não substitui revisão de semântica, contraste e composição no navegador. Não crie páginas de catálogo nem novas dependências para necessidades futuras.

## Ritmo visual da página municipal

A revisão de 15/10/2026 usa três colunas iguais no panorama. Cada cartão compartilha quatro linhas de grid: cabeçalho, medida principal, leitura e rodapé. O subgrid mantém números e ações alinhados mesmo quando um título quebra ou os votos são expandidos. Abaixo de 64em, os cartões seguem o fluxo vertical, sem reservar espaços vazios para cartões vizinhos. O resumo eleitoral mantém três nomes e percentuais; as contagens de votos continuam no detalhe eleitoral.

Os cartões municipais usam o mesmo espaçamento interno e o mesmo intervalo entre colunas. Listas financeiras extensas, despesas e histórico do Bolsa Família ocupam a largura da grade; em telas estreitas, suas subdivisões voltam a uma coluna. Valores monetários completos usam a escala fluida `--font-size-money`. O panorama abrevia milhões/bilhões e mantém o valor completo na leitura e no nome acessível.

`ritmo-visual.spec.ts` verifica ausência de rolagem horizontal, valores monetários completos em uma linha e alinhamento de números/ações, inclusive após expansão dos votos. Cobre 320, 390, 768 e 1440px. Capturas e revisão visual complementam essas medidas; não substituem pesquisa de compreensão com cidadãos.
