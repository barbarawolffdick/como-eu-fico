# Dados do MVP: TSE + IBGE + Bolsa Família

O **Como Eu Fico** mostra resultados eleitorais municipais do primeiro turno presidencial de 2026 ao lado de fluxos federais. Bases originais permanecem independentes; a integração se faz por `codigo_ibge` textual de sete dígitos em uma camada derivada.

## Módulos de dados que o MVP consome

| Domínio | Origem | Produção para interface |
|---|---|---|
| Eleitoral | TSE 2026; código de município TSE mapeado a IBGE | Snapshot municipal canônico indicado no README; sem dados por local de votação não conciliados |
| Territorial | IBGE; cadastro e população com ano definido | Código IBGE, nome, UF e população após validar série de referência |
| Bolsa Família | CGU; arquivo ZIP por competência; ponte SIAFI–IBGE Tesouro | CSV de parcelas e centavos por competência e município via `scripts/exportar_bolsa_mvp.py` |

**Não há um banco único mestre.** Exportações são reproduzíveis, e dados nominativos CGU (CPF, NIS, nomes) nunca devem ir para o repositório.

## O que está implementado neste módulo

- `scripts/ingerir_bolsa_familia.py`: ingestão eventual de competências da CGU para SQLite agregado; não é obrigatório reexecutá-la para o MVP se o backup validado já existir. Inclui a correspondência documentada `MT/1182 → 5101837` para Boa Esperança do Norte, sem modificar a tabela do Tesouro.
- `scripts/exportar_bolsa_mvp.py`: **única operação rotineira** do módulo para gerar um dataset municipal para a interface, em CSV UTF-8. Soma as referências de uma competência por município, mantém valores em centavos, valida os totais por competência e não sobrescreve resultados.
- `tests/test_ingerir_bolsa_familia.py`, `tests/test_municipio_novo_bolsa.py`, `tests/test_exportar_bolsa_mvp.py`: testes unitários das funções de produção.

Os scripts exploratórios para Colab, processamento de lotes e relatórios intermediários **não integram a árvore proposta para o MVP**. Seu histórico permanece no Git; não são importados pela solução acima.

## Dados históricos validados (evidência de execução, não versão permanente)

Relatórios produzidos no Colab para o backup local `beneficios_ate_202608.sqlite` validaram competências **202501–202608**: 20 meses, **387.119.228 parcelas**, **R$ 260.005.670.043,00**, cobertura de 5.570 municípios até 202509 e 5.571 a partir de 202510. Única entrada entre meses: IBGE 5101837 em 202510. Setembro/2026 não estava disponível no momento daquela coleta. Estes números descrevem a execução histórica, não devem ser usados para presumir a versão atual do arquivo sem revalidar.

**Interpretação:** parcelas não são famílias únicas; valores registrados não provam saque; `mes_competencia` e `mes_referencia` são diferentes. A exportação por competência agrega referências distintas; se o produto precisar desagregar mês de referência, isso deve ser uma consulta/exportação explícita e testada.

## Execução — somente quando o backup estiver disponível

Da raiz do repositório:

```bash
python3 -m unittest discover -s tests -p 'test_ingerir_bolsa_familia.py' -v
python3 -m unittest discover -s tests -p 'test_municipio_novo_bolsa.py' -v
python3 -m unittest discover -s tests -p 'test_exportar_bolsa_mvp.py' -v
python3 scripts/exportar_bolsa_mvp.py --db /caminho/para/beneficios_ate_202608.sqlite --saida data/curated/bolsa_familia_mvp/municipios_mes.csv
```

Após exportar, auditar o total, esquema, tamanho e cobertura e só então preparar o arquivo público de deploy com manifestos de versão. Não incluir SQLite nem ZIP bruto na aplicação web. Antes de juntar o CSV ao TSE, testar cardinalidade e cobertura do IBGE e não preencher competências ausentes como zero.

## Fora do MVP

BPC, Pé-de-Meia, PNAE, SUS, comparação por local de votação, ingestão automática de novas competências, explicações causais e somas heterogêneas de fluxos. Não são condições para construir e publicar o primeiro produto.
