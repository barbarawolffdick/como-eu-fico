# Protocolo de evidências — Como Eu Fico

Regras para diagnóstico, execução e auditoria de dados:

1. Registrar **observação verificável** separadamente de **hipótese** e **conclusão**.
2. Não atribuir causa sem evidência suficiente. Quando não houver, declarar **causa indeterminada**.
3. Não mudar dados originais, branch, histórico Git ou código durante a coleta diagnóstica.
4. Preservar saídas de comandos, caminhos, versões, hashes e rastreabilidade.
5. Toda correção deve ter teste reproduzível que falha antes e passa depois, quando aplicável.
6. Uma execução sem erro não prova a veracidade das informações eleitorais.
7. Divergências eleitorais só são resolvidas mediante comparação com fontes oficiais, com valores anteriores preservados.

## Diagnóstico inicial de ambiente (somente leitura)

```bash
python3 scripts/diagnosticar_ambiente.py
```

Saída: `diagnostico-ambiente.json`. O script lê o estado local do Git, informa existência do script de inspeção em HEAD e na ref remota **já disponível localmente**, e não corrige nada.

O arquivo de diagnóstico pode revelar caminhos locais e metadados de trabalho. Revisar antes de publicar.
