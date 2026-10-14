# Estado técnico e evidências — 14/10/2026

## Repositório e documentação
- Repositório público: https://github.com/barbarawolffdick/como-eu-fico
- `main`: README e contrato editorial `docs/contrato-editorial-dados-v1.md`, catálogo `docs/catalogo-fontes-v0.md`.
- PR de ingestão/auditoria Bolsa Família: https://github.com/barbarawolffdick/como-eu-fico/pull/9
- Branch: `feat/validar-amostra-bolsa-familia`; **não presumir merge**.
- A versão inicial do contrato contempla pesquisa desde 2023, mas a **primeira execução e o MVP** estão restritos a janeiro/2025–agosto/2026 pela disponibilidade real dos arquivos. O projeto planejou até setembro/2026; setembro não estava publicado na CGU quando tentaram baixar. Não representá-lo como zero.

## TSE — voto presidencial
- Fonte: primeiro turno presidencial TSE 2026.
- Relato de validação do pipeline: **5.571 municípios**, **497.897 seções**, sem divergência de composição municipal de votos.
- **6.588 divergências em códigos de locais de votação** continuam pendentes. Não usar agregado por local de votação como validado.
- Dados eleitorais originais/canônicos independentes dos benefícios; confira no repo quais snapshots estão disponíveis para runtime/deploy e se a publicação do snapshot foi concluída. Não presumir que arquivos SQLite locais estão no GitHub.

## Bolsa Família — CGU
- Origem ZIP por competência: `https://portaldatransparencia.gov.br/download-de-dados/novo-bolsa-familia/AAAAMM`.
- Ponte SIAFI–IBGE Tesouro: `tabmun.csv`, SHA-256 `3651c930ca1ddfde0bb7b47130795f332330d4c66b3db70f49f3ca3494e4242d`.
- Correção territorial específica em código: SIAFI **MT/1182** → IBGE **5101837**, Boa Esperança do Norte. O hash da ponte só cobre CSV Tesouro original, não a exceção em código.
- 20 competências consecutivas: **202501 a 202608**. Fonte de setembro/2026 indisponível em 13–14/10/2026.
- **387.119.228 parcelas**; **R$ 260.005.670.043,00** em valores registrados.
- Cobertura **5.570 municípios** em 202501–202509 e **5.571** em 202510–202608.
- Auditoria longitudinal no Colab: **PASS**, zero alertas. Única alteração no conjunto mensal de municípios: entrada de IBGE `5101837` em 202510; nenhum município saiu.
- Não houve grupos agregados com valores totais zero ou negativos (isso não avalia valores individuais brutos).
- Parcela com `mes_referencia` anterior a `mes_competencia`: jan/2025 120.400 (**0,5873%**); jan/2026 865.053 (**4,4407%**); ago/2026 30.794 (**0,1637%**). Isso não prova atraso de pagamento.
- Auditoria estrutural no Colab: cinco PASS (integridade, 20 meses, reconciliação de totais, consistência básica e integridade referencial).
- Backup disponível no Mac do usuário: `beneficios_ate_202608.sqlite` (~29 MB), não publicado em GitHub. Relatórios enviados ao ChatGPT: `auditoria_bolsa_familia_202501_202608.json` e `auditoria_longitudinal_bolsa_202501_202608.json`.
- Documentos do PR #9: `methodology/auditoria-consolidada-bolsa-familia-202501-202608.md`, `methodology/resultado-auditoria-longitudinal-202501-202608.md`. Script: `scripts/auditar_serie_bolsa_familia.py`.

## IBGE
- Chave IBGE de sete caracteres é base de joins.
- Trabalho populacional em PR #6 descrito como **experimental**, não pronto para consumo sem conferência. Investigar no repo o estado atual de dados e testes populacionais, sem inventar população.

## Riscos / lacunas para o MVP
1. Confirmar quais **snapshots municipais TSE** realmente existem em `main` ou no armazenamento local; gerar dataset de distribuição/deploy a partir de fonte oficial se necessário.
2. Preparar/exportar a camada pública municipal de Bolsa Família do SQLite local, sem dados pessoais.
3. Validar **IBGE/população** e joins TSE–IBGE–CGU, preservando a diferença de cobertura histórica.
4. Implementar interface e hospedagem/deploy; ainda não localizada aplicação web nos caminhos usuais no início de 14/10/2026.
5. Confirmar revisões e atualização da fonte CGU; dataset até 202608, não 202609.
6. Auditar que a variável de voto usada no MVP corresponde ao primeiro turno presidencial e ao município IBGE correto; não trabalhar com seções/locais onde há divergências.
