# Protocolo de evidências — Como Eu Fico

Regras para diagnóstico, execução e auditoria de dados:

1. Registrar **observação verificável** separadamente de **hipótese** e **conclusão**.
2. Não atribuir causa sem evidência suficiente. Quando não houver, declarar **causa indeterminada**.
3. Não mudar dados originais, branch, histórico Git ou código durante a coleta diagnóstica.
4. Preservar saídas de comandos, caminhos, versões, hashes e rastreabilidade.
5. Toda correção deve ter teste reproduzível que falha antes e passa depois, quando aplicável.
6. Uma execução sem erro não prova a veracidade das informações eleitorais.
7. Divergências eleitorais só são resolvidas mediante comparação com fontes oficiais, com valores anteriores preservados.

## Interpretação política e experiência do cidadão

Direção de produto aprovada em 15/10/2026: o Como Eu Fico promove conscientização política através de dados, conectando o voto da cidade à evolução das políticas públicas e às condições de vida. O placar eleitoral é uma referência permanente. A promessa, as três camadas do produto e as quatro jornadas estão definidas no [contrato editorial e de dados](../docs/contrato-editorial-dados-v1.md#1-objetivo-editorial).

Ao produzir indicadores, análises e textos para essas jornadas:

1. Separar **evolução observada durante um mandato**, **responsabilidade de cada esfera de governo** e **impacto demonstrado**. Coincidência temporal não comprova efeito da presidência.
2. Investigar tanto a presença quanto a ausência de efeitos sem antecipar a conclusão. Ausência de evidência de impacto não demonstra, por si só, ausência de impacto.
3. Preservar distribuição de votos, percentuais, eleição, turno e denominadores no placar eleitoral. O resultado municipal não revela motivações ou comportamento individual dos moradores.
4. Distinguir **escolha eleitoral**, **percepção de valor** e **condições de vida observadas**. Percepções exigem evidências próprias, como pesquisas, com período, população pesquisada, método e limites explícitos; votos e repasses não as medem diretamente.
5. Tratar relações entre linhas políticas e percepções como hipóteses a investigar. Cruzamentos descritivos não bastam para afirmar influência causal.
6. Permitir conferir cada afirmação publicada: apontar fonte, período, unidade, universo, método e limites relevantes. Evidências de percepção ainda não integradas e funcionalidades futuras não devem ser apresentadas como disponíveis.

## Diagnóstico inicial de ambiente (somente leitura)

```bash
python3 scripts/diagnosticar_ambiente.py
```

Saída: `diagnostico-ambiente.json`. O script lê o estado local do Git, informa existência do script de inspeção em HEAD e na ref remota **já disponível localmente**, e não corrige nada.

O arquivo de diagnóstico pode revelar caminhos locais e metadados de trabalho. Revisar antes de publicar.
