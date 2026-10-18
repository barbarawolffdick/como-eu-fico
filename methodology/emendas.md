# Emendas parlamentares por município

Gerado por `scripts/publicar_emendas.py` em `data/public/emendas_{ano}.json`.

## Fonte

- **CGU, Portal da Transparência**: `EmendasParlamentares_PorFavorecido.csv`, pagamentos mês a mês por favorecido. Entram as linhas com `Ano/Mês` no ano publicado. Isso inclui restos a pagar de emendas de anos anteriores.
- **Câmara dos Deputados** (`/deputados?idLegislatura=`, `/deputados/{id}/historico`) e **Senado** (`/senador/lista/legislatura/`, `/senador/{codigo}/filiacoes`), para o partido. Consultamos a legislatura do ano e as duas anteriores.

## Regras

- O município é o do **favorecido**: prefeitura, fundo municipal ou entidade sediada ali. Não é necessariamente onde o recurso foi aplicado.
- A ligação ao código IBGE usa nome e UF exatos, depois de normalizar acentos. Nomes antigos foram revisados à mão (`ALIASES`). Nunca usamos semelhança: o que não casa fica listado em `validacao.municipios_sem_correspondencia`.
- **Saúde** é o que foi recebido por favorecidos cujo nome contém "fundo" e "saúde". Esse total confere com o Fundo Nacional de Saúde em Juazeiro do Norte (R$ 2.557.192 em 2025).
- **Partido** é o do autor no ano de origem da emenda que mais pagou ao município. O ano de origem vem dos quatro primeiros dígitos do código da emenda. `partido_atual` aparece só quando mudou depois.
- Emendas de bancada, comissão ou relator não têm partido.
- Autores sem correspondência exata e única de nome ficam sem partido. A lista está em `validacao`.
- Suplentes que herdaram emendas aparecem pelo próprio nome. O sufixo "(EX-PARLAMENTAR …)" é removido.
- Município sem linha significa que nenhuma emenda foi paga a favorecidos dele no ano. Não é zero medido.
