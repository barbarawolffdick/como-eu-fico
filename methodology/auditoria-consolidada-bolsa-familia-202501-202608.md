# Auditoria estrutural do Novo Bolsa Família — 202501 a 202608

**Origem:** relatório `auditoria_bolsa_familia_202501_202608.json` produzido a partir do SQLite agregado local `beneficios_ate_202608.sqlite` no Google Colab, fornecido pela pesquisadora em 14/10/2026.

**Escopo:** 20 competências, janeiro/2025 a agosto/2026; setembro/2026 não disponível na CGU na data da verificação. **Status: PASS para as cinco verificações estruturais**. Não equivale a auditoria independente de cada linha bruta nem a validação substantiva do programa.

## Resultados

| Verificação | Resultado |
|---|---|
| `PRAGMA integrity_check` | PASS / ok |
| Sequência exata de 20 competências | PASS |
| Somatório dos agregados comparado aos metadados mensais | PASS |
| Consistência básica dos registros (código IBGE com 7 caracteres, quantidade positiva e referência não posterior à competência) | PASS |
| Registros municipais com competência ausente na tabela de origem | PASS / zero |
| **Total de parcelas (não famílias únicas)** | **387.119.228** |
| **Valor total das parcelas registradas** | **R$ 260.005.670.043,00** |

### Resultados por competência

| Competência | Parcelas | Valor (centavos) | Municípios | SHA-256 ZIP CGU |
|---|---:|---:|---:|---|
| 202501 | 20500422 | 1373577033000 | 5570 | `e4fa571d52a60e5dc8a7e961d96f7e7aef49fb1703c9350824860482384e8762` |
| 202502 | 20473537 | 1371319758800 | 5570 | `820947cf3aae3a810fbac6d929cc6417079acddbfa1e1bd4521fcadd79ab3dbd` |
| 202503 | 20431725 | 1358607974300 | 5570 | `fca6f402d1b5333bd3d51d554c94729d34092b81949ea53c8f5dd0e2b0489d28` |
| 202504 | 20363840 | 1357378173800 | 5570 | `047904e34b0ee33f68a2e99a22874b46894ce7c1f8097568d7df238305c9ef29` |
| 202505 | 20357879 | 1355501974200 | 5570 | `477b0a7bebe7fdd3aa734abc0a0099b68f249d8761bf24491880fe67c54b2585` |
| 202506 | 19847421 | 1325510864600 | 5570 | `8a418fb59ce9da7ec84b5113faa60ab0b2492b2564f0925e6e85e9726231af1d` |
| 202507 | 18986128 | 1274941143700 | 5570 | `9deceebe008978aabacbb4fb06c431c421bdcf66e901a25408573bbd5991655a` |
| 202508 | 18777743 | 1261961282000 | 5570 | `f968ba6401ff4fec760c366beb8fdbb3ee7b759841e49a265ac90a48e6f7a4ec` |
| 202509 | 19104530 | 1280365699700 | 5570 | `6bd82865e6fba00b70404ae2bb47dfe735f4938c358e39534d1578c1ded3a2b5` |
| 202510 | 18599089 | 1252832708200 | 5571 | `9a07953812a702ab6ed4217804884764781df5ae3037e3cf479d6829aa53fb66` |
| 202511 | 18313365 | 1235335689700 | 5571 | `ad46d442b9c12696c1a60cbc46bb31cc088504bf798ad807902230c50202caa9` |
| 202512 | 18670749 | 1264589580800 | 5571 | `47e19bdcde4afb8346e16d798ad7b8cd0255e11d6bf6c6b11c9a454d6e378e65` |
| 202601 | 19480034 | 1297877364600 | 5571 | `31ecf240eecaa11ab0a2d62c13664800ea1da7228b9e86bbbde95b93a81b0cd3` |
| 202602 | 19307246 | 1293620469700 | 5571 | `accf15c76b4a2d262d49b0df1e47735f9bb6f8add01ccea47d8918f96468f24c` |
| 202603 | 18865079 | 1269860908200 | 5571 | `18a6547fca65d2e7118e6e0bdc6e5dc19a43649c4ad58b530150e60b4ef9b391` |
| 202604 | 18872817 | 1272194605500 | 5571 | `ebddb124ba9b67de27cc93a474cf2a9afc79b39e8b5fdbbf7cc83b64bacf42e8` |
| 202605 | 18993120 | 1282898590600 | 5571 | `bdce123f36f45e70f03274ad2c555c00596dfcdb709019a310383620cc040fe3` |
| 202606 | 19217521 | 1299252237300 | 5571 | `1f60057386589092e739cd4b1942a822da6e851ba7529bb178d55b30945be56a` |
| 202607 | 19147563 | 1296615969700 | 5571 | `d294cf361d07720c39df41c35685fb5b96aab3a3ffb8cc8d98d711d77d6e98ce` |
| 202608 | 18809420 | 1276324975900 | 5571 | `0e0efef8bd01517aa234ba85ee530b4d8d486fb4a0abc2dcc3b24a274c044b9a` |

**SHA-256 da tabela de correspondência SIAFI–IBGE (CSV do Tesouro):** `3651c930ca1ddfde0bb7b47130795f332330d4c66b3db70f49f3ca3494e4242d` em todas as competências. Esse hash identifica a tabela original, **não** a exceção territorial codificada no pipeline.

## Cobertura e interpretação

De janeiro a setembro de 2025, cada competência registra **5.570** municípios; a partir de outubro de 2025, **5.571**. O código SIAFI `MT/1182` foi identificado como **Boa Esperança do Norte**, IBGE `5101837`, e tratado por exceção explícita no código após falha da ingestão de outubro. A mudança de cobertura não deve ser interpretada automaticamente como expansão do benefício; requer análise da série territorial e comparabilidade.

`mes_competencia` não é a mesma coisa que `mes_referencia`; um arquivo mensal contém parcelas de diferentes referências. Contar parcelas não equivale a contar famílias únicas ou beneficiários únicos. Os valores não devem ser divulgados como montante necessariamente sacado. Dados originais nominativos não foram versionados.

## Limites e próximos testes

1. Auditar referências temporais: distribuição competência × referência, valores negativos/nulos/anômalos e seus efeitos na série.
2. Comparar a cobertura territorial efetiva com o cadastro IBGE vigente; confirmar como meses anteriores à aparição de Boa Esperança do Norte devem ser apresentados.
3. Comparar agregados oficiais independentes da CGU/MDS para amostras de competências.
4. Verificar duplicidade semântica entre parcelas (chave de agregação é única por construção, mas isso não prova ausência de linhas duplicadas na origem).
5. Reproduzir os testes em outro ambiente, registrar a versão exata do script e guardar o JSON original da auditoria junto à documentação.

**Observação de proveniência:** este documento transcreve e confere o relatório do Colab. A leitura direta do SQLite no ambiente ChatGPT não foi possível; portanto, as cinco verificações foram executadas no Colab, não reexecutadas aqui.
