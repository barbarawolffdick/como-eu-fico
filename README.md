# Como Eu Fico

Projeto de análise eleitoral e indicadores públicos por município brasileiro.

## Fonte de dados atual

- **Votação:** arquivos oficiais TSE 2026, primeiro turno, cargo Presidente.
- **Território:** tabela oficial de correspondência dos códigos TSE–IBGE e cadastro de municípios do IBGE.
- **Chave de integração:** `codigo_ibge` (sete dígitos).
- **Cobertura validada:** 5.571 municípios, 497.897 seções, nenhuma divergência de composição de votos.
- **Pendente:** 6.588 divergências entre códigos de locais de votação. Não produzir agregações por local como se estivessem conciliadas.

Nenhum cálculo do pipeline atual usa os antigos resumos eleitorais em `dados-municipios/`.

## Onde estão os dados

| Diretório | Significado |
|---|---|
| `data/raw/tse/2026/` | ZIPs originais do TSE; não editar |
| `data/reference/` | Cadastro do IBGE e tabela TSE–IBGE |
| `data/tse_oficial/eleicoes_2026.sqlite` | Banco de ingestão e auditoria |
| `data/tse_oficial/codigos_oficiais/` | Exportações municipais auditadas |
| `data/curated/eleicoes_2026_t1/` | **Snapshot canônico para o projeto** |
| `data/quality/` | Resultados históricos de verificações |

## Publicar o snapshot canônico

Depois de gerar e conferir os CSVs oficiais:

```bash
python3 -m unittest discover -s tests -p 'test_publicar_base_municipal.py' -v
python3 scripts/publicar_base_municipal.py
```

Saída: `data/curated/eleicoes_2026_t1/` contendo `municipios.csv`, `candidatos_municipios.csv`, `validacao.json` e `manifesto.json`, com hashes SHA-256. Os CSVs são somente municipais e foram conferidos contra os totais de votos nominais. A pasta de destino não pode existir antes da execução.

## Inventário da limpeza

```bash
python3 scripts/inventariar_legado.py
```

O comando gera `inventario-limpeza.json` sem excluir nada. Antes de apagar ou mover qualquer caminho legado, confirmar a situação dos arquivos rastreados e não rastreados no Mac e a existência de outros consumidores do repositório.

Veja também `methodology/codigos-oficiais-tse-ibge.md`.
