#!/usr/bin/env python3
"""Coleta e inventaria tabela OFICIAL TSE-IBGE; sem inferir nomes de colunas."""
import argparse
import csv
import hashlib
import io
import json
import urllib.request
import zipfile
from datetime import datetime,timezone
from pathlib import Path

URL="https://cdn.tse.jus.br/estatistica/sead/odsele/municipio_tse_ibge/municipio_tse_ibge.zip"

def download(url,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        return
    temporary=path.with_suffix(".part")
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"ComoEuFico-Auditoria/1.0","Accept-Encoding":"identity"})
        with urllib.request.urlopen(req,timeout=120) as response, temporary.open("wb") as dest:
            while chunk:=response.read(1024*1024):
                dest.write(chunk)
        with zipfile.ZipFile(temporary) as z:
            if z.testzip() is not None:
                raise ValueError("ZIP inválido")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)

def inspect(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        while chunk:=f.read(1024*1024):
            h.update(chunk)
    result={"fonte":URL,"baixado_em_utc":datetime.now(timezone.utc).isoformat(),
            "arquivo":str(path),"sha256":h.hexdigest(),"bytes":path.stat().st_size,"arquivos":[]}
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            record={"membro":info.filename,"bytes_descompactados":info.file_size}
            if info.filename.lower().endswith(".csv"):
                with archive.open(info) as f:
                    raw=f.readline()
                    raw_example=f.readline()
                for encoding in ("utf-8-sig","latin-1"):
                    try:
                        header=raw.decode(encoding)
                        example=raw_example.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                sep=";" if header.count(";")>=header.count(",") else ","
                record.update({"encoding":encoding,"delimitador":sep,
                               "colunas":next(csv.reader([header],delimiter=sep)),
                               "amostra":next(csv.reader([example],delimiter=sep),[])})
            result["arquivos"].append(record)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,default=Path("data/reference/tse_ibge"))
    a=p.parse_args()
    path=a.out/"municipio_tse_ibge.zip"
    try:
        download(URL,path)
        result=inspect(path)
        a.out.mkdir(parents=True,exist_ok=True)
        report=a.out/"inventario.json"
        report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"resultado":"PASS","arquivo":str(path),"inventario":str(report),
                          "membros":[{"nome":r["membro"],"colunas":r.get("colunas")} for r in result["arquivos"]]},
                         ensure_ascii=False,indent=2))
    except Exception as exc:
        print(json.dumps({"resultado":"FAIL","erro":str(exc)},ensure_ascii=False))
        raise SystemExit(1)
if __name__=="__main__":
    main()
