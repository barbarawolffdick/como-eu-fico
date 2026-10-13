#!/usr/bin/env python3
"""Processa uma competência por execução, com backup portátil e retomada.

O banco é local; não conecta ao Google Drive. Executar do diretório raiz do projeto.
"""
import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

def backup(db, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    temp=target.with_suffix(".sqlite.part")
    try:
        with sqlite3.connect(db) as src, sqlite3.connect(temp) as dst:
            src.backup(dst)
        with sqlite3.connect(temp) as conn:
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Backup SQLite reprovado")
        temp.replace(target)
    finally:
        temp.unlink(missing_ok=True)

def run(mes,db,backup_dir,delete_zip):
    with sqlite3.connect(db) as conn:
        done=conn.execute(
            "SELECT mes_competencia FROM origem ORDER BY mes_competencia"
        ).fetchall()
    if not done:
        raise ValueError("Banco sem meses anteriores; validar janeiro e fevereiro primeiro")
    checkpoint=backup_dir / ("beneficios_ate_"+done[-1][0]+".sqlite")
    backup(db,checkpoint)
    print("BACKUP ANTES:",checkpoint,flush=True)
    if any(r[0]==mes for r in done):
        print("Mês já importado:",mes,flush=True)
        return checkpoint
    cmd=[sys.executable,"scripts/ingerir_bolsa_familia.py","--mes",mes,"--db",str(db)]
    print("PROCESSANDO:",mes,flush=True)
    subprocess.run(cmd,check=True)
    with sqlite3.connect(db) as conn:
        if conn.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
            raise ValueError("SQLite reprovado")
        record=conn.execute("SELECT parcelas,valor_centavos FROM origem WHERE mes_competencia=?",(mes,)).fetchone()
        sums=conn.execute("SELECT SUM(quantidade_parcelas),SUM(valor_centavos) FROM parcelas_municipais WHERE mes_competencia=?",(mes,)).fetchone()
        if not record or record!=sums:raise ValueError("Totais divergentes")
    target=backup_dir/("beneficios_ate_"+mes+".sqlite")
    backup(db,target)
    print("BACKUP DEPOIS:",target,flush=True)
    if delete_zip:
        path=Path("data/raw/cgu/bolsa_familia")/(mes+".zip")
        if path.is_file():
            path.unlink()
            print("ZIP temporário liberado:",path,flush=True)
    return target

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mes",required=True)
    p.add_argument("--db",type=Path,default=Path("data/beneficios/beneficios.sqlite"))
    p.add_argument("--backups",type=Path,default=Path("data/beneficios/backups"))
    p.add_argument("--apagar-zip",action="store_true")
    a=p.parse_args()
    if not a.db.exists():p.error("Banco SQLite anterior ausente; não começar do zero")
    if not ("202503"<=a.mes<="202609"):p.error("Processamento incremental começa em 202503")
    run(a.mes,a.db,a.backups,a.apagar_zip)
if __name__=="__main__":main()
