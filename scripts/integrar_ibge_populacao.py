#!/usr/bin/env python3
"""Acrescenta população estimada IBGE 2026 à base municipal SEM alterar originais.

Fonte: SIDRA tabela 6579, variável 9324, nível municipal N6.
Recusa cobertura incompleta, valores não numéricos ou códigos inesperados.
"""
import argparse
import csv
import hashlib
import json
import urllib.request
from datetime import datetime,timezone
from pathlib import Path

URL="https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/2026?formato=json"
YEAR=2026

def records(path):
    with path.open("r",encoding="utf-8-sig",newline="") as file:
        return list(csv.DictReader(file))

def population(payload):
    if not isinstance(payload,list) or len(payload)<2:
        raise ValueError("SIDRA: resposta vazia ou inesperada")
    header=payload[0]
    if not all(k in header for k in ("D1C","D2C","D3C","V")):
        raise ValueError("SIDRA: esquema não reconhecido; faltam D1C, D2C, D3C ou V")
    result={}
    for r in payload[1:]:
        code=str(r.get("D1C","")).strip()
        variable=str(r.get("D2C","")).strip()
        period=str(r.get("D3C","")).strip()
        raw=str(r.get("V","")).strip()
        if not (code.isdigit() and len(code)==7):
            raise ValueError("SIDRA: município inválido "+repr(code))
        if variable!="9324":
            raise ValueError("SIDRA: variável não é 9324: "+variable)
        if period!=str(YEAR):
            raise ValueError("SIDRA: período não é 2026: "+period)
        if not raw.isascii() or not raw.isdigit():
            raise ValueError("SIDRA: valor populacional ausente ou inválido para "+code+": "+repr(raw))
        if code in result:
            raise ValueError("SIDRA: município duplicado "+code)
        result[code]=int(raw)
    return result

def join(electoral,pop):
    if len(electoral)!=5571: raise ValueError("Base eleitoral não tem 5571 municípios")
    ids=[r["codigo_ibge"] for r in electoral]
    if len(set(ids))!=len(ids):
        raise ValueError("Base eleitoral contém código IBGE duplicado")
    missing=sorted(set(ids)-set(pop))
    extra=sorted(set(pop)-set(ids))
    if missing or extra:
        raise ValueError(f"Cobertura IBGE divergente: faltantes={len(missing)}, extras={len(extra)}; amostras={missing[:8]}, {extra[:8]}")
    out=[]
    for r in electoral:
        # Preservar todos os campos eleitorais; acrescentar somente um indicador novo.
        out.append({**r,"populacao_estimada_2026":pop[r["codigo_ibge"]]})
    return out

def run(source,output,raw,offline=False):
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Não sobrescrever publicação anterior: "+str(output))
    if not (source/"validacao.json").is_file():
        raise ValueError("Validação eleitoral ausente")
    status=json.loads((source/"validacao.json").read_text(encoding="utf-8"))
    if any(status.get(k)!="PASS" for k in ("resultados_municipais","consistencia_eleitoral","correspondencia")):
        raise ValueError("Fonte eleitoral não validada")
    electoral=records(source/"municipios.csv")
    if offline:
        data=raw.read_bytes()
    else:
        req=urllib.request.Request(URL,headers={"User-Agent":"ComoEuFico/1.0","Accept-Encoding":"identity"})
        with urllib.request.urlopen(req,timeout=120) as response:
            data=response.read()
    pop=population(json.loads(data.decode("utf-8-sig")))
    enriched=join(electoral,pop)
    # Não criar artefatos até todas as verificações serem concluídas.
    output.mkdir(parents=True,exist_ok=True)
    rawtarget=output/"sidra_6579_2026_raw.json"
    rawtarget.write_bytes(data)
    path=output/"municipios_populacao_2026.csv"
    with path.open("w",encoding="utf-8",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=list(enriched[0]))
        writer.writeheader()
        writer.writerows(enriched)
    report={
        "resultado":"PASS","fonte":"IBGE SIDRA","tabela":6579,"variavel":9324,
        "ano_referencia":YEAR,"url":URL,"arquivo_eleitoral":str(source/"municipios.csv"),
        "codigo_chave":"codigo_ibge","municipios":len(enriched),
        "populacao_nula":0,"acrescentou_coluna":"populacao_estimada_2026",
        "dados_eleitorais_alterados":False,
        "gerado_em_utc":datetime.now(timezone.utc).isoformat(),
        "sha256_sidra":hashlib.sha256(data).hexdigest(),
        "sha256_saida":hashlib.sha256(path.read_bytes()).hexdigest()
    }
    (output/"validacao.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/curated/eleicoes_2026_t1"))
    p.add_argument("--out",type=Path,default=Path("data/curated/ibge_populacao_2026"))
    p.add_argument("--raw",type=Path,help="JSON do SIDRA já baixado para execução sem rede")
    args=p.parse_args()
    try:
        print(json.dumps(run(args.source,args.out,args.raw,offline=args.raw is not None),ensure_ascii=False,indent=2))
    except Exception as e:
        p.exit(1,str(e)+"\n")
if __name__=="__main__":
    main()
