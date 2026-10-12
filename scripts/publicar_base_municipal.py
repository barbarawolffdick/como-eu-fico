#!/usr/bin/env python3
"""Publica snapshot municipal validado em diretório canônico, sem tocar fontes."""
import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime,timezone
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        while chunk:=f.read(1024*1024): h.update(chunk)
    return h.hexdigest()

def load(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def publish(source,dest):
    status=json.loads((source/"validacao.json").read_text(encoding="utf-8"))
    needed={"resultados_municipais":"PASS","consistencia_eleitoral":"PASS","correspondencia":"PASS"}
    for key,value in needed.items():
        if status.get(key)!=value: raise ValueError(f"Validação insuficiente: {key}={status.get(key)}")
    municipalities=load(source/"municipios.csv")
    candidates=load(source/"candidatos_municipios.csv")
    if len(municipalities)!=5571:
        raise ValueError(f"Esperados 5571 municípios, obtidos {len(municipalities)}")
    ids=[r["codigo_ibge"] for r in municipalities]
    if len(set(ids))!=5571 or any(len(c)!=7 or not c.isdigit() for c in ids):
        raise ValueError("Códigos IBGE duplicados/inválidos")
    votes={}
    for row in candidates:
        code=row["codigo_ibge"]
        if code not in set(ids):
            raise ValueError("Candidato associado a IBGE desconhecido: "+code)
        amount=int(row["votos"])
        if amount<0: raise ValueError("Votos negativos")
        votes[code]=votes.get(code,0)+amount
    for row in municipalities:
        expected=int(row["votos_validos"])
        if votes.get(row["codigo_ibge"],0)!=expected:
            raise ValueError("Composição municipal por candidatos divergente: "+row["codigo_ibge"])
    if dest.exists():
        raise FileExistsError(f"Destino já existe; preservar snapshots: {dest}")
    dest.mkdir(parents=True)
    for name in ("municipios.csv","candidatos_municipios.csv","validacao.json"):
        shutil.copy2(source/name,dest/name)
    manifest={
        "gerado_em_utc":datetime.now(timezone.utc).isoformat(),
        "origem":str(source),
        "escopo":"Presidente; Brasil; primeiro turno; 2026",
        "fonte_votos":"TSE",
        "chave_municipal":"codigo_ibge",
        "municipios":len(municipalities),
        "resultados_municipais":"PASS",
        "locais_de_votacao":"PENDENTE",
        "arquivos_sha256":{p.name:sha(p) for p in dest.iterdir() if p.is_file()}
    }
    (dest/"manifesto.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/tse_oficial/codigos_oficiais"))
    p.add_argument("--dest",type=Path,default=Path("data/curated/eleicoes_2026_t1"))
    a=p.parse_args()
    try:
        print(json.dumps(publish(a.source,a.dest),ensure_ascii=False,indent=2))
    except Exception as e:
        p.exit(1,str(e)+"\n")
if __name__=="__main__":
    main()
