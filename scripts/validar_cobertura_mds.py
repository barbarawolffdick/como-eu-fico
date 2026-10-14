"""Valida agregado mensal de famílias/pessoas beneficiárias do PBF fornecido pelo MDS.

Entrada: CSV previamente extraído do MDS e acompanhado de manifesto verificável.
NÃO converte parcelas da CGU em beneficiários; NÃO estima pessoas por família.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

def validar(csv_path: Path, manifesto: Path, codigos: set[str]):
    meta=json.loads(manifesto.read_text(encoding="utf-8"))
    digest=hashlib.sha256(csv_path.read_bytes()).hexdigest()
    if meta.get("fonte")!="MDS" or meta.get("sha256_csv")!=digest or not meta.get("url_fonte"):
        raise ValueError("Proveniência MDS e SHA-256 obrigatórios")
    if meta.get("definicao_unidade") not in ("familias_beneficiarias","pessoas_em_familias_beneficiarias"):
        raise ValueError("Unidade de medida não identificada pelo MDS")
    if meta.get("periodo") is None or len(str(meta["periodo"]))!=6:
        raise ValueError("Período mensal obrigatório")
    with csv_path.open(encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream)
        if set(reader.fieldnames or [])!={"codigo_ibge","periodo","quantidade"}:
            raise ValueError("Esperadas apenas as colunas codigo_ibge, periodo, quantidade")
        result={}
        for row in reader:
            code=row["codigo_ibge"]
            n=row["quantidade"]
            if (code not in codigos or code in result or row["periodo"]!=meta["periodo"]
                or not n.isascii() or not n.isdigit()):
                raise ValueError("Registro MDS inválido ou duplicado: "+repr(code))
            result[code]=int(n)
    if set(result)!=codigos:
        raise ValueError("Cobertura municipal MDS incompleta")
    return {"fonte":meta["fonte"],"url_fonte":meta["url_fonte"],"sha256_csv":digest,
            "periodo":meta["periodo"],"unidade":meta["definicao_unidade"],"municipios":len(result)}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--csv",required=True,type=Path)
    parser.add_argument("--manifesto",required=True,type=Path)
    parser.add_argument("--db",default="data/app/como_eu_fico.sqlite",type=Path)
    args=parser.parse_args()
    import sqlite3
    with sqlite3.connect(f"file:{args.db.resolve()}?mode=ro",uri=True) as db:
        codes={x[0] for x in db.execute("SELECT codigo_ibge FROM municipios")}
    if len(codes)!=5571: raise ValueError("Cadastro IBGE incompleto")
    print(json.dumps(validar(args.csv,args.manifesto,codes),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
