# Publicação municipal a partir dos códigos oficiais TSE–IBGE

Esta etapa usa o SQLite TSE já construído e o ZIP oficial da correspondência TSE–IBGE. Não consome nem restaura os resumos eleitorais de origem secundária.

## Executar

```bash
git fetch origin
git merge --ff-only origin/feat/reconciliacao-tse-2026
python3 -m unittest discover -s tests -p 'test_codigos_oficiais_tse_ibge.py' -v
python3 scripts/aplicar_codigos_oficiais_tse_ibge.py
```

O script não modifica `eleicoes_2026.sqlite`. Confere as correspondências por `SG_UF`, `CD_MUNICIPIO_TSE` e `CD_MUNICIPIO_IBGE`, inclusive códigos TSE com zeros iniciais. Valida cobertura contra o cadastro IBGE e recusa códigos conflitantes. Antes de gerar os CSVs, exige que as 497.897 seções (ou quantidade encontrada na base real) passem na conciliação eleitoral.

## Saídas

Em `data/tse_oficial/codigos_oficiais/`:

- `validacao.json`: cobertura TSE–IBGE, integridade eleitoral e status independente dos locais
- `pendencias_correspondencia.json`: códigos ou municípios que não puderam ser vinculados
- `municipios.csv`: totais de votos válidos e comparecimento por município, quando validado
- `candidatos_municipios.csv`: votos por candidato e município, quando validado
- `secoes.csv`: seções com o identificador de local informado no arquivo de apuração, para **inspeção**, não como localização conciliada

Divergências de `NR_LOCAL_VOTACAO` permanecem pendentes. **A validação municipal não significa que os locais estão conciliados.** Ainda não há publicação de `locais.csv`, precisamente para evitar agregar por um código de local de confiabilidade não confirmada.

Nunca sobrescrever o diretório de saída de uma execução anterior; mova-o ou informe `--out` apontando para um diretório novo.
