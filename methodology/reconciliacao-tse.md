# Fase 3 — Reconciliação independente com o TSE

## Fontes
Conjunto oficial [Resultados — 2026](https://dadosabertos.tse.jus.br/dataset/resultados-2026). O script consulta os metadados em CKAN, sem inventar nomes de arquivos ou URLs. A seleção busca o recurso nacional **Presidente — Votação por seção eleitoral** e os recursos de **Detalhe da apuração**.

## Descobrir recursos (sem baixar arquivos grandes)
```bash
python3 scripts/baixar_tse_2026.py
```
Cria `data/raw/tse/2026/manifest.json`, com URL, identificador e metadados do catálogo.

## Baixar
```bash
python3 scripts/baixar_tse_2026.py --download
```
Registra tamanho e SHA-256 dos downloads. Os arquivos podem ser grandes. Não versionar bases brutas grandes nem publicar dados sem revisão.

## Estado e limites
**Etapa inicial de implementação, ainda sem execução validada.** Após a coleta, precisamos inspecionar os cabeçalhos reais dos CSVs, identificar cargo, turno, candidatos e geografia; implementar a reconstrução municipal e conferir município por município. O cruzamento de seções com escolas/locais exige correspondência histórica confiável. Nenhuma divergência deve ser interpretada como falha da apuração eleitoral sem verificar o pipeline local e os registros oficiais.

Os resultados atuais do Como Eu Fico permanecem provisórios.
