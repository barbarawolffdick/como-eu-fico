#!/usr/bin/env python3
"""Inspeciona estrutura dos ZIPs TSE sem extrair bases completas."""
import argparse
import csv
import io
import json
import zipfile
from pathlib import Path

FILES = [
    "votacao_secao_2026_BR.zip",
    "detalhe_votacao_secao_2026.zip",
    "detalhe_votacao_munzona_2026.zip",
]
def inspect(path):
    result={"arquivo":str(path),"membros":[]}
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            member={"nome":info.filename,"bytes_descompactados":info.file_size}
            if info.filename.lower().endswith((".csv",".txt")):
                with z.open(info) as stream:
                    header=stream.readline()
                    raw=stream.readline()
                for encoding in ("utf-8-sig","latin-1"):
                    try:
                        first=header.decode(encoding)
                        second=raw.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                separator=";" if first.count(";")>=first.count(",") else ","
                member.update({"codificacao":encoding,"separador":separator,
                               "colunas":next(csv.reader([first],delimiter=separator)),
                               "amostra_linha_2":next(csv.reader([second],delimiter=separator),[])})
            result["membros"].append(member)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dir",type=Path,default=Path("data/raw/tse/2026"))
    p.add_argument("--output",type=Path,default=Path("data/quality/estrutura_tse_2026.json"))
    a=p.parse_args()
    result=[inspect(a.dir/name) for name in FILES]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for item in result:
        print("\n"+item["arquivo"])
        for m in item["membros"]:
            print("  ",m["nome"],"(" + str(m["bytes_descompactados"])+ " bytes)")
            if "colunas" in m:
                print("  CODIFICAÇÃO:",m["codificacao"],"  COLUNAS:",", ".join(m["colunas"]))
    print("\nRelatório:",a.output)

if __name__=="__main__":
    main()
