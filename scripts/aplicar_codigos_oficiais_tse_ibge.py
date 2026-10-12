#!/usr/bin/env python3
"""Aplica correspondência de códigos TSE–IBGE oficial ao SQLite existente.

Preserva a apuração; publica apenas CSVs municipais após auditoria eleitoral e territorial.
Não considera diferença de código de local como erro de votos municipais.
"""
import argparse
import csv
import io
import json
import sqlite3
import zipfile
from pathlib import Path
from datetime import datetime, timezone
from scripts.construir_base_tse_ibge import norm
from scripts.diagnosticar_base_tse import report as audit

MEMBER="municipio_tse_ibge.csv"
REQUIRED={"SG_UF","CD_MUNICIPIO_TSE","CD_MUNICIPIO_IBGE","NM_MUNICIPIO_TSE","NM_MUNICIPIO_IBGE"}

def mapping_from_zip(path):
    with zipfile.ZipFile(path) as z:
        if z.namelist().count(MEMBER)!=1:
            raise ValueError("CSV de correspondência ausente/duplicado")
        with z.open(MEMBER) as raw:
            r=csv.DictReader(io.TextIOWrapper(raw,encoding="utf-8-sig",newline=""),delimiter=";")
            missing=REQUIRED-set(r.fieldnames or [])
            if missing:
                raise ValueError("Colunas ausentes: "+str(sorted(missing)))
            out={}
            used={}
            for lineno,row in enumerate(r,2):
                uf=row["SG_UF"].strip().upper()
                code=row["CD_MUNICIPIO_TSE"].strip()
                ibge=row["CD_MUNICIPIO_IBGE"].strip()
                if not code.isdigit() or not ibge.isdigit() or len(ibge)!=7:
                    raise ValueError(f"Códigos inválidos na linha {lineno}")
                key=(uf,str(int(code)))
                if key in out and out[key]!=(ibge,row["NM_MUNICIPIO_TSE"]):
                    raise ValueError(f"Código TSE com mapeamento conflitante: {key}")
                if ibge in used and used[ibge]!=key:
                    raise ValueError(f"Código IBGE com múltiplos códigos TSE: {ibge}")
                out[key]=(ibge,row["NM_MUNICIPIO_TSE"])
                used[ibge]=key
            return out

def validate(db,mapping):
    problems=[]
    match=[]
    tse=list(db.execute("SELECT uf,cd_tse,MIN(municipio),COUNT(DISTINCT municipio) FROM apuracao GROUP BY uf,cd_tse"))
    for uf,raw_code,name,name_count in tse:
        key=(uf,str(int(raw_code)))
        found=mapping.get(key)
        if not found:
            problems.append({"uf":uf,"codigo_tse":raw_code,"municipio":name,"motivo":"sem_codigo_na_tabela_oficial"})
            continue
        ibge,official_tse_name=found
        reference=db.execute("SELECT uf,municipio_ibge FROM ibge WHERE codigo_ibge=?",(ibge,)).fetchone()
        if not reference or reference[0]!=uf:
            problems.append({"uf":uf,"codigo_tse":raw_code,"municipio":name,"codigo_ibge":ibge,"motivo":"ibge_ausente_ou_uf_divergente"})
            continue
        if name_count!=1:
            problems.append({"uf":uf,"codigo_tse":raw_code,"municipio":name,"codigo_ibge":ibge,"motivo":"nomes_inconsistentes_no_tse"})
            continue
        # Código, não nome, define identidade. Divergência de nomenclatura é informativa.
        match.append((uf,raw_code,name,ibge,"codigo_oficial_tse_ibge"))
    if len({m[3] for m in match})!=len(match):
        problems.append({"motivo":"codigo_ibge_nao_unico"})
    ibge_count=db.execute("SELECT COUNT(*) FROM ibge").fetchone()[0]
    if len(match)!=len(tse) or len(match)!=ibge_count:
        problems.append({"motivo":"cobertura_incompleta","tse":len(tse),"match":len(match),"ibge":ibge_count})
    return match,problems

def write_csv(path,db,sql,header):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f)
        w.writerow(header)
        w.writerows(db.execute(sql))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",type=Path,default=Path("data/tse_oficial/eleicoes_2026.sqlite"))
    p.add_argument("--correspondencia",type=Path,default=Path("data/reference/tse_ibge/municipio_tse_ibge.zip"))
    p.add_argument("--out",type=Path,default=Path("data/tse_oficial/codigos_oficiais"))
    args=p.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        p.error("Diretório de saída deve estar vazio; não sobrescrever auditorias")
    args.out.mkdir(parents=True,exist_ok=True)
    mapping=mapping_from_zip(args.correspondencia)
    db=sqlite3.connect("file:"+str(args.db.resolve())+"?mode=ro",uri=True)
    try:
        diag=audit(db)
        matches,problems=validate(db,mapping)
        summary={
            "gerado_em_utc":datetime.now(timezone.utc).isoformat(),
            "fonte_correspondencia":str(args.correspondencia),
            "municipios_tse":diag["metricas"]["municipios_tse"],
            "municipios_ibge_correspondidos":len(matches),
            "pendencias_correspondencia":len(problems),
            "secoes_composicao_divergente":diag["metricas"]["secoes_composicao_divergente"],
            "secoes_local_divergente":diag["metricas"]["secoes_local_divergente"],
            "consistencia_eleitoral":diag["consistencia_eleitoral"],
            "locais":"PENDENTE" if diag["metricas"]["secoes_local_divergente"] else "PASS",
            "correspondencia":"PASS" if not problems else "PENDENTE",
            "resultados_municipais":"BLOQUEADOS",
        }
        with (args.out/"pendencias_correspondencia.json").open("w",encoding="utf-8") as f:
            json.dump(problems,f,indent=2,ensure_ascii=False)
        if not problems and diag["consistencia_eleitoral"]=="PASS":
            # TEMP views não modificam o arquivo fonte aberto em modo ro.
            db.execute("CREATE TEMP TABLE codigo_oficial (uf TEXT, cd_tse TEXT, municipio_tse TEXT, codigo_ibge TEXT, metodo TEXT)")
            db.executemany("INSERT INTO codigo_oficial VALUES (?,?,?,?,?)",matches)
            write_csv(args.out/"municipios.csv",db,"""
              SELECT c.codigo_ibge,a.uf,i.municipio_ibge,a.cd_tse,
                     SUM(a.aptos),SUM(a.comparecimento),SUM(a.abstencoes),
                     SUM(a.nominais),SUM(a.brancos),SUM(a.nulos),COUNT(*)
              FROM apuracao a JOIN codigo_oficial c ON a.uf=c.uf AND a.cd_tse=c.cd_tse
              JOIN ibge i ON i.codigo_ibge=c.codigo_ibge
              GROUP BY c.codigo_ibge,a.uf,i.municipio_ibge,a.cd_tse ORDER BY c.codigo_ibge""",
              ["codigo_ibge","uf","municipio_ibge","codigo_tse","aptos","comparecimento","abstencoes","votos_validos","brancos","nulos","secoes"])
            write_csv(args.out/"candidatos_municipios.csv",db,"""
              SELECT c.codigo_ibge,v.uf,v.cd_tse,v.votavel,MIN(v.nome_votavel),SUM(v.votos)
              FROM votos v JOIN codigo_oficial c ON v.uf=c.uf AND v.cd_tse=c.cd_tse
              WHERE v.votavel NOT IN ('95','96')
              GROUP BY c.codigo_ibge,v.uf,v.cd_tse,v.votavel ORDER BY c.codigo_ibge,v.votavel""",
              ["codigo_ibge","uf","codigo_tse","numero_candidato","nome_candidato","votos"])
            write_csv(args.out/"secoes.csv",db,"""
              SELECT c.codigo_ibge,a.uf,a.cd_tse,a.zona,a.secao,
                     a.local,a.aptos,a.comparecimento,a.abstencoes,a.nominais,a.brancos,a.nulos
              FROM apuracao a JOIN codigo_oficial c ON a.uf=c.uf AND a.cd_tse=c.cd_tse
              ORDER BY c.codigo_ibge,a.zona,a.secao""",
              ["codigo_ibge","uf","codigo_tse","zona","secao","local_detalhe_tse","aptos","comparecimento","abstencoes","votos_validos","brancos","nulos"])
            summary["resultados_municipais"]="PASS"
            summary["observacao"]="Locais e seções exportados apenas para inspeção; divergência nos códigos de local permanece pendente."
    finally:
        db.close()
    (args.out/"validacao.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if summary["resultados_municipais"]!="PASS":
        raise SystemExit(1)
if __name__=="__main__":
    main()
