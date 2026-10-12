#!/usr/bin/env python3
"""Confronta votos válidos por seção para os oito municípios. Somente leitura."""
import csv
import io
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.reconciliar_8_municipios import TARGETS, norm, scope, section, integer, reconcile, write_csv

VOTE = "votacao_secao_2026_BR.csv"
DETAIL = "detalhe_votacao_secao_2026_BRASIL.csv"

def read(z, member):
    if z.namelist().count(member) != 1:
        raise ValueError("Membro ausente/duplicado: " + member)
    with z.open(member) as f:
        reader = csv.DictReader(io.TextIOWrapper(f,encoding="latin-1",newline=""),delimiter=";")
        for line,row in enumerate(reader,2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"Linha inválida: {member}:{line}")
            yield line,row

def verify(directory):
    votes = defaultdict(lambda: defaultdict(int))
    ids = defaultdict(set)
    affected = defaultdict(set)
    with zipfile.ZipFile(directory/"votacao_secao_2026_BR.zip") as z:
        for line,row in read(z,VOTE):
            key=(row["SG_UF"],norm(row["NM_MUNICIPIO"]))
            if key not in TARGETS or not scope(row):
                continue
            sec=section(row)
            number=row["NR_VOTAVEL"]
            identity=(sec,number)
            if identity in ids[key]:
                raise ValueError(f"Linha de votação duplicada: {identity}")
            ids[key].add(identity)
            amount=integer(row["QT_VOTOS"],f"{VOTE}:{line}")
            label=norm(row["NM_VOTAVEL"])
            if number=="95" and label=="VOTO BRANCO":
                category="brancos"
            elif number=="96" and label=="VOTO NULO":
                category="nulos"
            elif number in ("95","96") or label in ("VOTO BRANCO","VOTO NULO"):
                raise ValueError(f"Categoria ambígua: {VOTE}:{line}")
            else:
                category="nominais"
            votes[sec][category]+=amount
            affected[key].add(sec)

    totals=defaultdict(int)
    details=defaultdict(set)
    problems=defaultdict(list)
    with zipfile.ZipFile(directory/"detalhe_votacao_secao_2026.zip") as z:
        with z.open(DETAIL) as handle:
            columns = next(csv.reader([handle.readline().decode("latin-1")], delimiter=";"))
        expected = {"QT_VOTOS_NOMINAIS","QT_VOTOS_BRANCOS","QT_VOTOS_NULOS",
                    "QT_COMPARECIMENTO","QT_VOTOS_LEGENDA","QT_VOTOS_ANULADOS_APU_SEP"}
        missing = expected - set(columns)
        if missing:
            raise ValueError(f"{DETAIL}: colunas ausentes: {sorted(missing)}")
        for line,row in read(z,DETAIL):
            key=(row["SG_UF"],norm(row["NM_MUNICIPIO"]))
            if key not in TARGETS or not scope(row):
                continue
            sec=section(row)
            if sec in details[key]:
                raise ValueError(f"Detalhe duplicado: {sec}")
            details[key].add(sec)
            cols=["QT_VOTOS_NOMINAIS","QT_VOTOS_BRANCOS","QT_VOTOS_NULOS",
                  "QT_COMPARECIMENTO","QT_VOTOS_LEGENDA","QT_VOTOS_ANULADOS_APU_SEP"]
            n,b,u,att,leg,ann=[integer(row[c],f"{DETAIL}:{line}") for c in cols]
            totals[key]+=n
            actual=votes[sec]
            if (actual["nominais"]!=n or actual["brancos"]!=b or actual["nulos"]!=u
                or n+b+u+leg+ann!=att or leg!=0 or ann!=0):
                problems[key].append({"zona":sec[2],"secao":sec[3],"linha":line,
                    "nominais_votacao":actual["nominais"],"nominais_detalhe":n,
                    "brancos_votacao":actual["brancos"],"brancos_detalhe":b,
                    "nulos_votacao":actual["nulos"],"nulos_detalhe":u,
                    "comparecimento":att,"legenda":leg,"anulados":ann})
    output={}
    for key in sorted(TARGETS):
        issues=[]
        if not affected[key] or affected[key]!=details[key]:
            issues.append("cobertura_secoes_divergente")
        if problems[key]:
            issues.append("composicao_por_secao_divergente")
        output[key]={"status":"INCONCLUSIVO" if issues else "PASS",
                     "votos_validos":totals[key] if not issues else None,
                     "secoes":len(details[key]),"alertas":issues,
                     "exemplos_divergencias":problems[key][:10],
                     "quantidade_secoes_divergentes":len(problems[key])}
    return output

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--tse",type=Path,default=Path("data/raw/tse/2026"))
    p.add_argument("--issues",type=Path,default=Path("data/quality/inconsistencias_eleitorais.csv"))
    p.add_argument("--out",type=Path,default=Path("data/quality/reconciliacao_8_municipios_validos.csv"))
    a=p.parse_args()
    previous,_=reconcile(a.issues,a.tse)
    checks=verify(a.tse)
    rows=[]
    for row in previous:
        key=(row["uf"],row["municipio"])
        item=checks[key]
        valid=item["votos_validos"]
        verified=(item["status"]=="PASS" and row["observacoes"]=="definicao_votos_validos_pendente")
        rows.append({
            "uf":row["uf"],"municipio":row["municipio"],"codigo_ibge":row["codigo_ibge"],
            "origem_votos_lula":row["origem_votos_lula"],"tse_votos_lula":row["tse_votos_lula"],
            "dif_lula":row["dif_lula"],
            "origem_votos_flavio":row["origem_votos_flavio"],"tse_votos_flavio":row["tse_votos_flavio"],
            "dif_flavio":row["dif_flavio"],
            "origem_votos_validos":row["origem_votos_validos"],
            "tse_votos_validos":valid if verified else "",
            "dif_validos":valid-int(row["origem_votos_validos"]) if verified else "",
            "status":"PASS" if verified else "INCONCLUSIVO",
            "alertas":";".join(item["alertas"] + ([] if verified else [row["observacoes"]])),
            "secoes_verificadas":item["secoes"],
            "secoes_divergentes":item["quantidade_secoes_divergentes"],
            "arquivo_origem":row["arquivo_origem"],"linha_origem":row["linha_origem"]
        })
    write_csv(a.out,rows,list(rows[0]))
    detail=a.out.with_suffix(".json")
    detail.write_text(json.dumps({str(key):value for key,value in checks.items()},ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"resultado":"PASS" if all(r["status"]=="PASS" for r in rows) else "INCONCLUSIVO",
                      "municipios":len(rows),"csv":str(a.out),"detalhes":str(detail),
                      "status_por_municipio":[{"municipio":r["municipio"],"uf":r["uf"],"status":r["status"]} for r in rows]},
                      ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
