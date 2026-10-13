#!/usr/bin/env python3
"""Processa até 3 competências sequenciais, com checkpoint mensal.

Não conecta a serviços de nuvem. Baixe o backup final antes de encerrar Colab.
"""
import argparse
import sqlite3
from pathlib import Path
try:
    from scripts.processar_mes_bolsa_seguro import run
except ModuleNotFoundError:
    from processar_mes_bolsa_seguro import run

def months(start, count):
    if count<1 or count>3: raise ValueError("Lote de 1 a 3 meses")
    y,m=int(start[:4]),int(start[4:])
    if len(start)!=6 or not 1<=m<=12: raise ValueError("Mês inválido")
    result=[]
    for _ in range(count):
        code=f"{y:04d}{m:02d}"
        if not "202503"<=code<="202609":raise ValueError("Mês fora do recorte 202503–202609")
        result.append(code)
        m+=1
        if m==13:y,m=y+1,1
    return result

def batch(start,count,db,backups,delete_zip):
    if not db.is_file():raise FileNotFoundError("Banco existente ausente: "+str(db))
    target=None
    for mes in months(start,count):
        target=run(mes,db,backups,delete_zip)
    print("BACKUP FINAL PARA BAIXAR:",target,flush=True)
    return target

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--inicio",required=True,help="AAAAMM")
    p.add_argument("--quantidade",type=int,default=3)
    p.add_argument("--db",type=Path,default=Path("data/beneficios/beneficios.sqlite"))
    p.add_argument("--backups",type=Path,default=Path("data/beneficios/backups"))
    p.add_argument("--apagar-zip",action="store_true")
    a=p.parse_args()
    batch(a.inicio,a.quantidade,a.db,a.backups,a.apagar_zip)
if __name__=="__main__":main()
