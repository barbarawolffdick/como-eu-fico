#!/usr/bin/env python3
"""Ingestão municipal mensal do Novo Bolsa Família (CGU), independente do TSE.

Não armazena CPF, NIS ou nome; lê CSV do ZIP em streaming; guarda só agregados.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import sqlite3
import urllib.request
import zipfile
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
import unicodedata

def keymap(headers):
    def norm(s):
        s = unicodedata.normalize("NFKD", str(s))
        return "".join(ch for ch in s if not unicodedata.combining(ch)).upper().strip().replace("_", " ")
    cols = {norm(h): h for h in headers}
    required = ("MES COMPETENCIA", "MES REFERENCIA", "UF", "CODIGO MUNICIPIO SIAFI", "VALOR PARCELA")
    missing = [k for k in required if k not in cols]
    if missing:
        raise ValueError("Colunas ausentes: " + ", ".join(missing))
    return {k: cols[k] for k in required}

def value(s):
    s = (s or "").strip().replace("R$", "").replace(" ", "")
    if not s or s in ("-", "..."):
        raise ValueError("Valor ausente")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\\d{1,3}(?:\\.\\d{3})+", s):
        s = s.replace(".", "")
    try:
        v = Decimal(s)
    except InvalidOperation:
        raise ValueError("Valor inválido")
    if not v.is_finite() or v.as_tuple().exponent < -2:
        raise ValueError("Valor não finito ou com mais de duas casas")
    return int(v * 100)

CGU="https://portaldatransparencia.gov.br/download-de-dados/novo-bolsa-familia/{mes}"
TESOURO=("https://www.tesourotransparente.gov.br/ckan/dataset/"
"abb968cb-3710-4f85-89cf-875c91b9c7f6/resource/"
"eebb3bc6-9eea-4496-8bcf-304f33155282/download/tabmun.csv")
SCHEMA="""
CREATE TABLE IF NOT EXISTS origem (
 mes_competencia TEXT PRIMARY KEY, sha256_zip TEXT NOT NULL,
 sha256_ponte TEXT NOT NULL, linhas INTEGER NOT NULL,
 parcelas INTEGER NOT NULL, valor_centavos INTEGER NOT NULL,
 municipios INTEGER NOT NULL, url TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS parcelas_municipais (
 mes_competencia TEXT NOT NULL, mes_referencia TEXT NOT NULL,
 codigo_ibge TEXT NOT NULL, valor_centavos INTEGER NOT NULL,
 quantidade_parcelas INTEGER NOT NULL,
 PRIMARY KEY(mes_competencia,mes_referencia,codigo_ibge),
 FOREIGN KEY(mes_competencia) REFERENCES origem(mes_competencia)
);
"""
def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def download(url,dest):
    if dest.exists(): return
    dest.parent.mkdir(parents=True,exist_ok=True)
    temp=dest.with_suffix(dest.suffix+".part")
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"ComoEuFico/1.0"})
        with urllib.request.urlopen(req,timeout=180) as src,open(temp,"wb") as out:
            for chunk in iter(lambda:src.read(1024*1024),b""):out.write(chunk)
        temp.replace(dest)
    finally:
        temp.unlink(missing_ok=True)

def bridge(path):
    data=path.read_bytes()
    content=data.decode("latin-1")
    delimiter=";" if content.splitlines()[0].count(";")>content.splitlines()[0].count(",") else ","
    mapping={}
    for row in csv.reader(io.StringIO(content),delimiter=delimiter):
        if len(row)!=5: raise ValueError("Tabela SIAFI inesperada (precisa 5 colunas)")
        siafi,cnpj,name,uf,ibge=[x.strip() for x in row]
        if not (re.fullmatch(r"\d{1,5}",siafi) and re.fullmatch(r"\d{7}",ibge)
                and re.fullmatch(r"[A-Z]{2}",uf)):
            raise ValueError("Ponte inválida: "+str((siafi,uf,ibge)))
        key=(uf,siafi.zfill(4))
        if key in mapping and mapping[key]!=ibge:
            raise ValueError("Ponte conflitante: "+str(key))
        mapping[key]=ibge
    # Atualização territorial documentada: Boa Esperança do Norte (MT), IBGE 5101837.
    # O CSV do Tesouro utilizado nesta ingestão não inclui o código 1182.
    # Prefeitura: https://www.boaesperancadonorte.mt.gov.br/pages/codigos-de-identificacao-do-municipio
    # IBGE: https://www.ibge.gov.br/explica/codigos-dos-municipios.php
    # O arquivo fonte permanece inalterado; aplicar exceção somente se não houver
    # outro mapeamento, para não mascarar conflito com atualização posterior.
    key=("MT","1182")
    if key in mapping and mapping[key]!="5101837":
        raise ValueError("Ponte conflitante com Boa Esperança do Norte: "+mapping[key])
    mapping[key]="5101837"
    return mapping

def transform(zip_path, mapping, mes, expected=None):
    """Memória limitada ao número de combinações município/referência."""
    if not re.fullmatch(r"20\d{2}(0[1-9]|1[0-2])",mes):
        raise ValueError("Competência inválida")
    groups=defaultdict(lambda:[0,0])
    total=0;money=0;refs=set();municipios=set()
    with zipfile.ZipFile(zip_path) as z:
        members=[n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(members)!=1: raise ValueError("Esperado um CSV no ZIP")
        if z.testzip() is not None: raise ValueError("Falha CRC no ZIP")
        with z.open(members[0]) as src:
            reader=csv.DictReader(io.TextIOWrapper(src,encoding="latin-1",newline=""),delimiter=";")
            cols=keymap(reader.fieldnames or [])
            for line,r in enumerate(reader,start=2):
                comp=(r[cols["MES COMPETENCIA"]] or "").strip()
                ref=(r[cols["MES REFERENCIA"]] or "").strip()
                uf=(r[cols["UF"]] or "").strip().upper()
                siafi=(r[cols["CODIGO MUNICIPIO SIAFI"]] or "").strip().zfill(4)
                if comp!=mes or not re.fullmatch(r"20\d{2}(0[1-9]|1[0-2])",ref):
                    raise ValueError(f"Linha {line}: competência/referência inválida")
                ibge=mapping.get((uf,siafi))
                if ibge is None:raise ValueError(f"Linha {line}: SIAFI sem ponte: {uf}/{siafi}")
                cents=value(r[cols["VALOR PARCELA"]])
                item=groups[(comp,ref,ibge)]
                item[0]+=cents;item[1]+=1
                total+=1;money+=cents;refs.add(ref);municipios.add(ibge)
    if expected:
        for k,v in expected.items():
            got={"linhas":total,"parcelas":total,"total_centavos":money,
                 "municipios_ibge":len(municipios)}.get(k)
            if got is not None and got!=v:raise ValueError(f"{k}: esperado {v}, encontrado {got}")
    assert sum(x[0] for x in groups.values())==money
    assert sum(x[1] for x in groups.values())==total
    return groups,{"linhas":total,"parcelas":total,"total_centavos":money,
                   "municipios":len(municipios),"meses_referencia":sorted(refs)}

def write_month(db,mes,groups,meta,zip_hash,bridge_hash):
    db.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(db) as cx:
        cx.execute("PRAGMA foreign_keys=ON")
        cx.executescript(SCHEMA)
        if cx.execute("SELECT 1 FROM origem WHERE mes_competencia=?",(mes,)).fetchone():
            raise ValueError("Competência já ingerida, não sobrescrever: "+mes)
        # atomic month transaction
        with cx:
            cx.execute("INSERT INTO origem VALUES(?,?,?,?,?,?,?,?)",
                       (mes,zip_hash,bridge_hash,meta["linhas"],meta["parcelas"],
                        meta["total_centavos"],meta["municipios"],CGU.format(mes=mes)))
            cx.executemany("INSERT INTO parcelas_municipais VALUES(?,?,?,?,?)",
                           [(a,b,c,x[0],x[1]) for (a,b,c),x in sorted(groups.items())])
            check=cx.execute("SELECT SUM(valor_centavos),SUM(quantidade_parcelas) "
                             "FROM parcelas_municipais WHERE mes_competencia=?",(mes,)).fetchone()
            if check!=(meta["total_centavos"],meta["parcelas"]):
                raise ValueError("SQLite não preservou totais")
    return True

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mes",required=True,help="AAAAMM, ex. 202502")
    p.add_argument("--zip",type=Path,help="ZIP local; se omitido baixa da CGU")
    p.add_argument("--ponte",type=Path,default=Path("data/reference/siafi_ibge_tabmun.csv"))
    p.add_argument("--db",type=Path,default=Path("data/beneficios/beneficios.sqlite"))
    p.add_argument("--esperado",type=Path,help="JSON de validação, opcional para 202501")
    args=p.parse_args()
    if args.mes[:4] not in ("2025","2026") or args.mes>"202609":
        p.error("Primeira fase: competências entre 202501 e 202609")
    path=args.zip or Path("data/raw/cgu/bolsa_familia")/(args.mes+".zip")
    if not args.zip:download(CGU.format(mes=args.mes),path)
    download(TESOURO,args.ponte)
    expected=None
    if args.esperado:
        d=json.loads(args.esperado.read_text(encoding="utf-8"))
        if d["competencia"]!=args.mes:raise ValueError("Validação é de outro mês")
        expected={"parcelas":d["parcelas"],
                  "total_centavos":d["valor_total_centavos"],
                  "municipios_ibge":d["municipios_ibge"]}
    groups,meta=transform(path,bridge(args.ponte),args.mes,expected)
    write_month(args.db,args.mes,groups,meta,sha(path),sha(args.ponte))
    print(json.dumps({"status":"PASS","competencia":args.mes,**meta,
                      "sha256_zip":sha(path),"sha256_ponte":sha(args.ponte)},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
