#!/usr/bin/env python3
"""Exporta dados municipais do Bolsa Família para o MVP, sem dados pessoais.

Não altera o SQLite de origem. A saída é CSV agregada por competência e município.
"""
import argparse
import csv
import json
import sqlite3
from pathlib import Path

def exportar(banco, destino):
    if not banco.is_file():
        raise FileNotFoundError("Banco de benefícios não encontrado: " + str(banco))
    if destino.exists():
        raise FileExistsError("Destino já existe; não sobrescrever: " + str(destino))
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(destino.suffix + ".part")
    sql = """
        SELECT mes_competencia, codigo_ibge,
               SUM(quantidade_parcelas) AS parcelas,
               SUM(valor_centavos) AS valor_centavos
        FROM parcelas_municipais
        GROUP BY mes_competencia, codigo_ibge
        ORDER BY mes_competencia, codigo_ibge
    """
    totais = {}
    try:
        with sqlite3.connect(banco.resolve().as_uri() + "?mode=ro", uri=True) as cx:
            if cx.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Integridade SQLite falhou")
            origem = {
                mes: (parcelas, valor)
                for mes, parcelas, valor in cx.execute(
                    "SELECT mes_competencia, parcelas, valor_centavos FROM origem"
                )
            }
            if not origem:
                raise ValueError("Tabela origem vazia")
            with temporario.open("w", encoding="utf-8", newline="") as out:
                writer = csv.writer(out)
                writer.writerow(("mes_competencia", "codigo_ibge", "parcelas", "valor_centavos"))
                for mes, codigo, parcelas, valor in cx.execute(sql):
                    if len(codigo) != 7 or not codigo.isdigit():
                        raise ValueError("Código IBGE inválido: " + str(codigo))
                    writer.writerow((mes, codigo, parcelas, valor))
                    previous = totais.get(mes, (0, 0))
                    totais[mes] = (previous[0] + parcelas, previous[1] + valor)
        if totais != origem:
            raise ValueError("Exportação não reconcilia com a tabela origem")
        temporario.replace(destino)
    finally:
        temporario.unlink(missing_ok=True)
    return {"competencias": len(origem), "parcelas": sum(v[0] for v in origem.values()),
            "valor_centavos": sum(v[1] for v in origem.values()), "arquivo": str(destino)}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True, type=Path)
    p.add_argument("--saida", required=True, type=Path)
    args = p.parse_args()
    print(json.dumps(exportar(args.db, args.saida), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
