#!/usr/bin/env python3
"""Auditoria local de UM ZIP mensal da CGU, sem publicar dados pessoais.

Não modifica a base eleitoral. Aceita ZIP ou CSV (arquivo oficial baixado à parte).
Saída: JSON agregado por município SIAFI, sem CPF/NIS/nomes.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import unicodedata
import zipfile
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

def norm(s):
    s=unicodedata.normalize("NFKD", str(s))
    return "".join(x for x in s if not unicodedata.combining(x)).upper().strip().replace("_"," ")

def keymap(headers):
    cols={norm(x):x for x in headers}
    required=["MES COMPETENCIA","MES REFERENCIA","UF","CODIGO MUNICIPIO SIAFI","VALOR PARCELA"]
    missing=[k for k in required if k not in cols]
    if missing: raise ValueError("Colunas ausentes: "+", ".join(missing)+"; encontradas: "+repr(list(cols)))
    return {k:cols[k] for k in required}

def value(s):
    s=(s or "").strip().replace("R$","").replace(" ","")
    if not s or s in ("-","..."): raise ValueError("valor ausente")
    if "," in s: s=s.replace(".","").replace(",",".")
    elif re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+",s): s=s.replace(".","")
    try:
        v=Decimal(s)
    except InvalidOperation: raise ValueError("valor inválido")
    if not v.is_finite(): raise ValueError("valor não finito")
    if v.as_tuple().exponent < -2: raise ValueError("mais de duas casas decimais")
    return int(v*100)

def audit_bytes(blob, period, filename):
    sample=blob[:15000]
    decoded=None
    encoding=None
    for enc in ("utf-8-sig","cp1252","latin-1"):
        try: decoded=sample.decode(enc);encoding=enc;break
        except UnicodeDecodeError: pass
    if decoded is None: raise ValueError("Codificação não reconhecida")
    delim=";" if decoded.splitlines()[0].count(";")>=decoded.splitlines()[0].count(",") else ","
    reader=csv.DictReader(io.TextIOWrapper(io.BytesIO(blob),encoding=encoding,newline=""),delimiter=delim)
    if not reader.fieldnames: raise ValueError("CSV vazio")
    km=keymap(reader.fieldnames)
    aggregates=defaultdict(lambda:{"parcelas":0,"centavos":0})
    competences=set()
    refs=set()
    errors=[]
    rows=0
    for num,r in enumerate(reader,start=2):
        rows+=1
        try:
            competencia=(r[km["MES COMPETENCIA"]] or "").strip()
            referencia=(r[km["MES REFERENCIA"]] or "").strip()
            uf=(r[km["UF"]] or "").strip().upper()
            siafi=(r[km["CODIGO MUNICIPIO SIAFI"]] or "").strip()
            if not re.fullmatch(r"\d{6}",competencia) or not re.fullmatch(r"\d{6}",referencia):
                raise ValueError("mês inválido")
            for month in (competencia,referencia):
                if not (1<=int(month[-2:])<=12): raise ValueError("mês fora do calendário")
            if competencia != period: raise ValueError("competência diferente do arquivo esperado")
            if not re.fullmatch(r"[A-Z]{2}",uf): raise ValueError("UF inválida")
            if not re.fullmatch(r"\d+",siafi): raise ValueError("SIAFI inválido")
            cents=value(r[km["VALOR PARCELA"]])
            competences.add(competencia)
            refs.add(referencia)
            a=aggregates[(competencia,referencia,uf,siafi)]
            a["parcelas"]+=1
            a["centavos"]+=cents
        except (ValueError,TypeError) as e:
            if len(errors)<12: errors.append({"linha":num,"problema":str(e)})
    if not rows: raise ValueError("Não há linhas de dados")
    result={
        "status":"PASS" if not errors else "BLOCKED",
        "arquivo":filename,"mes_competencia_esperado":period,
        "linhas":rows,"municipios_siafi":len(set((k[2],k[3]) for k in aggregates)),"grupos_municipio_referencia":len(aggregates),
        "meses_competencia":sorted(competences),
        "meses_referencia":sorted(refs),
        "colunas_encontradas":list(reader.fieldnames),
        "erros_amostra":errors,
        "total_centavos":sum(v["centavos"] for v in aggregates.values()),
        "agregado_municipal":[{"mes_competencia":competencia,"mes_referencia":referencia,"uf":uf,"codigo_siafi":siafi,**v}
                             for (competencia,referencia,uf,siafi),v in sorted(aggregates.items())]
    }
    return result

def inspect(path, period):
    if not re.fullmatch(r"20\d{4}",period) or not 1<=int(period[-2:])<=12:
        raise ValueError("Período esperado em AAAAMM")
    raw=path.read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    if zipfile.is_zipfile(io.BytesIO(raw)):
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            files=[name for name in z.namelist() if name.lower().endswith(".csv") and not name.startswith("__MACOSX/")]
            if not files: raise ValueError("ZIP sem CSV")
            if len(files)!=1: raise ValueError("ZIP com múltiplos CSVs; inspecionar manualmente: "+repr(files))
            with z.open(files[0]) as f: blob=f.read()
            name=files[0]
    elif path.suffix.lower()==".csv":
        blob=raw;name=path.name
    else: raise ValueError("Esperado ZIP ou CSV oficial")
    result=audit_bytes(blob,period,name)
    result["fonte"]="CGU — Novo Bolsa Família"
    result["sha256_arquivo_original"]=sha
    result["nota"]="Agregação de parcelas disponibilizadas, NÃO prova saque; quantidade de parcelas NÃO equivale a famílias únicas; ainda não convertido de SIAFI para IBGE."
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("arquivo",type=Path,help="ZIP ou CSV mensal oficial da CGU")
    p.add_argument("--mes",required=True,help="mês da folha esperado AAAAMM")
    p.add_argument("--saida",type=Path,default=Path("data/quality/bolsa_familia_amostra.json"))
    a=p.parse_args()
    try:
        result=inspect(a.arquivo,a.mes)
        # Não persistir o cabeçalho, pois é só metadado de formato.
        result.pop("colunas_encontradas",None)
        a.saida.parent.mkdir(parents=True,exist_ok=True)
        if a.saida.exists(): raise FileExistsError("Não sobrescrever: "+str(a.saida))
        a.saida.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        summary={k:v for k,v in result.items() if k!="agregado_municipal"}
        print(json.dumps(summary,ensure_ascii=False,indent=2))
        if result["status"]!="PASS": p.exit(1,"Auditoria bloqueada; revisar erros.\n")
    except Exception as e: p.exit(1,str(e)+"\n")

if __name__=="__main__": main()
