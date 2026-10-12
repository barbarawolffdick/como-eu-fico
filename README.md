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

## Retirar dados eleitorais secundários do Git (sem excluir do Mac)

O diretório `dados-municipios/` contém 17.205 arquivos rastreados na auditoria de 12/10/2026. Não é consumido pelo pipeline TSE–IBGE e está no `.gitignore`.

```bash
python3 scripts/desvincular_dados_antigos.py
python3 scripts/desvincular_dados_antigos.py --apply
git diff --cached --stat
git commit -m "chore: desvincula resumos eleitorais antigos"
git push
```

A opção `--apply` executa `git rm --cached`: remove apenas os registros do índice Git e **mantém as cópias locais**. Requer branch `chore/consolidar-base-eleitoral` e árvore de trabalho limpa. A operação não deve ser repetida se já não houver arquivos rastreados. Esses arquivos serão excluídos do repositório numa futura integração do PR, mas continuam disponíveis localmente no Mac que executou o comando.

Os scripts antigos de leitura e reconciliação dos resumos foram removidos desta branch. Para reproduzir o novo pipeline, consulte os scripts oficiais TSE–IBGE.

## Inventário da limpeza

```bash
python3 scripts/inventariar_legado.py
```

O comando gera `inventario-limpeza.json` sem excluir nada. Antes de apagar ou mover qualquer caminho legado, confirmar a situação dos arquivos rastreados e não rastreados no Mac e a existência de outros consumidores do repositório.

Veja também `methodology/codigos-oficiais-tse-ibge.md`.
