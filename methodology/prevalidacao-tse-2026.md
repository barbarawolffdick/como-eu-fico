# Pré-validação TSE — testes bloqueantes

Comando (executar na raiz do repositório, após atualizar a branch):

```bash
python3 -m unittest discover -s tests -p 'test_validar_tse_2026.py' -v
python3 scripts/validar_tse_2026.py
```

A segunda execução lê os três ZIPs já baixados, confere hashes SHA-256 com o manifesto, verifica esquema, filtra a eleição presidencial de 2026 no primeiro turno, verifica chaves e aritmética básica no arquivo nacional **BRASIL** de detalhamento por seção, e gera `data/quality/validacao_tse_2026.json`. Não altera os ZIPs nem os dados eleitorais existentes.

Critérios: `FAIL` significa falha observada e código de saída 1. `PASS` significa apenas que a condição específica foi satisfeita. `INCONCLUSIVO` significa requisito ainda não demonstrado. A execução só usa código de saída 0 na ausência de FAIL, **não significa autorização para publicar**, pois existem testes inconclusivos intencionais. O estado consolidado será `INCONCLUSIVO` enquanto a reconciliação independente não estiver implementada.

Limitações explícitas: o esquema do CSV de votação não assegura unicidade por seção porque há diversos votáveis; os códigos dos votáveis e situações especiais requerem conferência no leiame oficial; não basta comparar soma de linhas com votos nominais sem classificação. O arquivo de detalhe por seção selecionado é `*_BRASIL.csv`, não uma soma dos arquivos estaduais (que incluem cargos diferentes). A validação é somente leitura e não corrige dados. Rodar sobre os arquivos reais é indispensável antes de afirmar a cobertura nacional.

Os testes de unidade usam ZIPs **sintéticos**, destinados a comprovar detecção de hash adulterado e duplicação de seção, e não são evidência de resultados eleitorais.
