#!/usr/bin/env python3
"""Base eleitoral 2026 exclusivamente TSE + cadastro municipal oficial IBGE.

Usa SQLite (stdlib) para agregaçāo reproduzível, sem depender do CSV eleitoral antigo.
Sem fuzzy matching: municípios não conciliados bloqueiam a publicação.
"""
import argparse
import csv
import hashlib
import io
import json
import sqlite3
import unicodedata
import re
import zipfile
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone

VOTEZIP="votacao_secao_2026_BR.zip"
DETAILZIP="detalhe_votacao_secao_2026.zip"
VOTECSV="votacao_secao_2026_BR.csv"
DETAILCSV="detalhe_votacao_secao_2026_BRASIL.csv"
COLUMNS={
 "votes":{"ANO_ELEICAO","NR_TURNO","TP_ABRANGENCIA","DS_CARGO","SG_UF","CD_MUNICIPIO","NM_MUNICIPIO","NR_ZONA","NR_SECAO","NR_LOCAL_VOTACAO","NR_VOTAVEL","NM_VOTAVEL","QT_VOTOS"},
 "detail":{"ANO_ELEICAO","NR_TURNO","TP_ABRANGENCIA","DS_CARGO","SG_UF","CD_MUNICIPIO","NM_MUNICIPIO","NR_ZONA","NR_SECAO","NR_LOCAL_VOTACAO","QT_APTOS","QT_COMPARECIMENTO","QT_ABSTENCOES","QT_VOTOS_NOMINAIS","QT_VOTOS_BRANCOS","QT_VOTOS_NULOS","QT_VOTOS_LEGENDA","QT_VOTOS_ANULADOS_APU_SEP"}
}
ALIASES={} # Não reutilizar aliases da base original; revisar pendências TSE/IBGE separadamente.

def norm(s):
    s=unicodedata.normalize("NFKD",str(s or ""))
    return " ".join(re.sub(r"[^A-Z0-9]+"," ", "".join(c for c in s if not unicodedata.combining(c)).upper()).split())

def number(value, where):
    if not value or not value.isascii() or not value.isdigit():
        raise ValueError(f"{where}: inteiro inválido {value!r}")
    return int(value)

def rows(path, member, required):
    with zipfile.ZipFile(path) as archive:
        if archive.namelist().count(member)!=1:
            raise ValueError(f"Membro ausente/duplicado: {member}")
        with archive.open(member) as stream:
            reader=csv.DictReader(io.TextIOWrapper(stream,encoding="latin-1",newline=""),delimiter=";")
            absent=required-set(reader.fieldnames or [])
            if absent:
                raise ValueError(f"{member}: faltam colunas {sorted(absent)}")
            for lineno,row in enumerate(reader,2):
                if None in row or any(x is None for x in row.values()):
                    raise ValueError(f"{member}:{lineno} formato irregular")
                if row["ANO_ELEICAO"]!="2026" or row["NR_TURNO"]!="1" or row["TP_ABRANGENCIA"]!="F" or norm(row["DS_CARGO"])!="PRESIDENTE":
                    continue
                if row["SG_UF"]=="ZZ":
                    continue
                yield lineno,row

def connect(path):
    db=sqlite3.connect(str(path))
    db.executescript("""
    PRAGMA journal_mode=DELETE;
    CREATE TABLE votos (
      uf TEXT NOT NULL, cd_tse TEXT NOT NULL, municipio TEXT NOT NULL,
      zona TEXT NOT NULL, secao TEXT NOT NULL, local TEXT NOT NULL,
      votavel TEXT NOT NULL, nome_votavel TEXT NOT NULL, votos INTEGER NOT NULL,
      PRIMARY KEY(uf,cd_tse,zona,secao,votavel)
    );
    CREATE TABLE apuracao (
      uf TEXT NOT NULL, cd_tse TEXT NOT NULL, municipio TEXT NOT NULL,
      zona TEXT NOT NULL, secao TEXT NOT NULL, local TEXT NOT NULL,
      aptos INTEGER NOT NULL, comparecimento INTEGER NOT NULL, abstencoes INTEGER NOT NULL,
      nominais INTEGER NOT NULL, brancos INTEGER NOT NULL, nulos INTEGER NOT NULL,
      legenda INTEGER NOT NULL, anulados INTEGER NOT NULL,
      PRIMARY KEY(uf,cd_tse,zona,secao)
    );
    CREATE TABLE ibge (
      codigo_ibge TEXT PRIMARY KEY, uf TEXT NOT NULL, municipio_ibge TEXT NOT NULL,
      nome_normalizado TEXT NOT NULL, UNIQUE(uf,nome_normalizado)
    );
    CREATE TABLE municipios_tse_ibge (
      uf TEXT NOT NULL, cd_tse TEXT NOT NULL, municipio_tse TEXT NOT NULL,
      codigo_ibge TEXT NOT NULL, metodo TEXT NOT NULL,
      PRIMARY KEY(uf,cd_tse), UNIQUE(codigo_ibge)
    );
    """)
    return db

def load_ibge(db,path):
    with path.open(encoding="utf-8-sig",newline="") as handle:
        for x in csv.DictReader(handle):
            code=x["codigo_ibge"]
            if not re.fullmatch(r"\d{7}",code):
                raise ValueError("Código IBGE inválido: "+code)
            db.execute("INSERT INTO ibge VALUES (?,?,?,?)",(code,x["uf"],x["municipio_ibge"],norm(x["municipio_ibge"])))

def insert_sources(db, root):
    stats=Counter()
    for line,row in rows(root/VOTEZIP,VOTECSV,COLUMNS["votes"]):
        where=f"{VOTECSV}:{line}"
        q=number(row["QT_VOTOS"],where)
        # 95 e 96 são categorias, nunca candidatos; demais códigos requerem classificação pela apuração.
        try:
            db.execute("INSERT INTO votos VALUES (?,?,?,?,?,?,?,?,?)",
                (row["SG_UF"],row["CD_MUNICIPIO"],row["NM_MUNICIPIO"],row["NR_ZONA"],row["NR_SECAO"],
                 row["NR_LOCAL_VOTACAO"],row["NR_VOTAVEL"],row["NM_VOTAVEL"],q))
        except sqlite3.IntegrityError as e:
            raise ValueError(f"{where}: duplicação na chave de votação") from e
        stats["linhas_votacao"]+=1
    db.commit()
    for line,row in rows(root/DETAILZIP,DETAILCSV,COLUMNS["detail"]):
        where=f"{DETAILCSV}:{line}"
        cols=[number(row[k],where) for k in ("QT_APTOS","QT_COMPARECIMENTO","QT_ABSTENCOES","QT_VOTOS_NOMINAIS",
                                              "QT_VOTOS_BRANCOS","QT_VOTOS_NULOS","QT_VOTOS_LEGENDA","QT_VOTOS_ANULADOS_APU_SEP")]
        try:
            db.execute("INSERT INTO apuracao VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (row["SG_UF"],row["CD_MUNICIPIO"],row["NM_MUNICIPIO"],row["NR_ZONA"],row["NR_SECAO"],row["NR_LOCAL_VOTACAO"],*cols))
        except sqlite3.IntegrityError as e:
            raise ValueError(f"{where}: duplicação na chave de apuração") from e
        stats["linhas_apuracao"]+=1
    db.commit()
    return stats

def map_ibge(db):
    issues=[]
    index={(uf,nm):(code,name) for code,uf,name,nm in db.execute("SELECT * FROM ibge")}
    seen=set()
    for uf,cd,nm in db.execute("SELECT uf,cd_tse,MIN(municipio) FROM apuracao GROUP BY uf,cd_tse ORDER BY uf,cd_tse"):
        names=[x[0] for x in db.execute("SELECT DISTINCT municipio FROM apuracao WHERE uf=? AND cd_tse=?",(uf,cd))]
        vote_names=[x[0] for x in db.execute("SELECT DISTINCT municipio FROM votos WHERE uf=? AND cd_tse=?",(uf,cd))]
        if len(names)!=1 or len(vote_names)!=1 or norm(names[0])!=norm(vote_names[0]):
            issues.append({"uf":uf,"codigo_tse":cd,"municipio_tse":nm,"motivo":"nome_tse_inconsistente"})
            continue
        reference=index.get((uf,norm(nm)))
        if reference is None:
            issues.append({"uf":uf,"codigo_tse":cd,"municipio_tse":nm,"motivo":"sem_correspondencia_ibge"})
            continue
        code,_=reference
        if code in seen:
            issues.append({"uf":uf,"codigo_tse":cd,"municipio_tse":nm,"motivo":"codigo_ibge_duplicado"})
            continue
        seen.add(code)
        db.execute("INSERT INTO municipios_tse_ibge VALUES (?,?,?,?,?)",(uf,cd,nm,code,"uf_nome_normalizado"))
    db.commit()
    return issues

def audit(db):
    issues=[]
    def problem(rule, query):
        for x in db.execute(query):
            issues.append({"regra":rule,"uf":x[0],"codigo_tse":x[1],"zona":x[2],"secao":x[3],"detalhe":str(x[4])})
    problem("secao_sem_apuracao", """SELECT v.uf,v.cd_tse,v.zona,v.secao,COUNT(*) FROM votos v LEFT JOIN apuracao a
      ON (v.uf,v.cd_tse,v.zona,v.secao)=(a.uf,a.cd_tse,a.zona,a.secao)
      WHERE a.uf IS NULL GROUP BY v.uf,v.cd_tse,v.zona,v.secao""")
    problem("apuracao_sem_votos", """SELECT a.uf,a.cd_tse,a.zona,a.secao,1 FROM apuracao a LEFT JOIN votos v
      ON (v.uf,v.cd_tse,v.zona,v.secao)=(a.uf,a.cd_tse,a.zona,a.secao)
      WHERE v.uf IS NULL""")
    problem("composicao_secao", """SELECT a.uf,a.cd_tse,a.zona,a.secao,
      printf('nominais=%d/%d; brancos=%d/%d; nulos=%d/%d; comparecimento=%d',
        COALESCE(SUM(CASE WHEN v.votavel NOT IN ('95','96') THEN v.votos END),0),a.nominais,
        COALESCE(SUM(CASE WHEN v.votavel='95' THEN v.votos END),0),a.brancos,
        COALESCE(SUM(CASE WHEN v.votavel='96' THEN v.votos END),0),a.nulos,a.comparecimento)
      FROM apuracao a LEFT JOIN votos v ON (v.uf,v.cd_tse,v.zona,v.secao)=(a.uf,a.cd_tse,a.zona,a.secao)
      GROUP BY a.uf,a.cd_tse,a.zona,a.secao
      HAVING COALESCE(SUM(CASE WHEN v.votavel NOT IN ('95','96') THEN v.votos END),0)!=a.nominais
      OR COALESCE(SUM(CASE WHEN v.votavel='95' THEN v.votos END),0)!=a.brancos
      OR COALESCE(SUM(CASE WHEN v.votavel='96' THEN v.votos END),0)!=a.nulos
      OR a.nominais+a.brancos+a.nulos+a.legenda+a.anulados!=a.comparecimento
      OR a.legenda!=0 OR a.anulados!=0""")
    problem("local_inconsistente", """SELECT a.uf,a.cd_tse,a.zona,a.secao,
      a.local||' vs '||MIN(v.local) FROM apuracao a JOIN votos v
      ON (v.uf,v.cd_tse,v.zona,v.secao)=(a.uf,a.cd_tse,a.zona,a.secao)
      GROUP BY a.uf,a.cd_tse,a.zona,a.secao HAVING MIN(v.local)!=MAX(v.local) OR a.local!=MIN(v.local)""")
    return issues

def export_query(db,path,query,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as handle:
        w=csv.writer(handle);w.writerow(fields)
        w.writerows(db.execute(query))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--tse",type=Path,default=Path("data/raw/tse/2026"))
    p.add_argument("--ibge",type=Path,default=Path("data/reference/municipios_ibge.csv"))
    p.add_argument("--out",type=Path,default=Path("data/tse_oficial"))
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    dbpath=a.out/"eleicoes_2026.sqlite"
    if dbpath.exists():
        raise SystemExit(f"Não sobrescrever base anterior: {dbpath}. Use --out em diretório novo.")
    db=connect(dbpath)
    report={"fonte_eleitoral":"TSE","fonte_territorial":"IBGE","ano":2026,"turno":1,
            "gerado_em_utc":datetime.now(timezone.utc).isoformat()}
    try:
        load_ibge(db,a.ibge)
        report["ingestao"]=dict(insert_sources(db,a.tse))
        mapping=map_ibge(db)
        issues=audit(db)
        report["municipios_tse"]=db.execute("SELECT COUNT(*) FROM (SELECT DISTINCT uf,cd_tse FROM apuracao)").fetchone()[0]
        report["municipios_correspondidos_ibge"]=db.execute("SELECT COUNT(*) FROM municipios_tse_ibge").fetchone()[0]
        report["municipios_referencia_ibge"]=db.execute("SELECT COUNT(*) FROM ibge").fetchone()[0]
        report["pendencias_mapeamento"]=len(mapping)
        report["pendencias_eleitorais"]=len(issues)
        export_query(db,a.out/"pendencias_mapeamento.csv",
                     "SELECT uf,cd_tse,municipio_tse,metodo FROM municipios_tse_ibge WHERE 1=0",
                     ["uf","codigo_tse","municipio_tse","motivo"])
        with (a.out/"pendencias_mapeamento.csv").open("a",encoding="utf-8",newline="") as handle:
            w=csv.DictWriter(handle,fieldnames=["uf","codigo_tse","municipio_tse","motivo"]);w.writerows(mapping)
        with (a.out/"pendencias_eleitorais.csv").open("w",encoding="utf-8",newline="") as handle:
            w=csv.DictWriter(handle,fieldnames=["regra","uf","codigo_tse","zona","secao","detalhe"])
            w.writeheader();w.writerows(issues)
        if mapping or issues or report["municipios_tse"]!=report["municipios_referencia_ibge"]:
            report["resultado"]="BLOQUEADO"
        else:
            report["resultado"]="PASS"
            export_query(db,a.out/"municipios.csv", """
              SELECT m.codigo_ibge,a.uf,m.municipio_tse,a.cd_tse,
                     SUM(a.aptos),SUM(a.comparecimento),SUM(a.abstencoes),
                     SUM(a.nominais),SUM(a.brancos),SUM(a.nulos),
                     COUNT(*)
              FROM apuracao a JOIN municipios_tse_ibge m ON (a.uf,a.cd_tse)=(m.uf,m.cd_tse)
              GROUP BY m.codigo_ibge,a.uf,m.municipio_tse,a.cd_tse ORDER BY m.codigo_ibge""",
              ["codigo_ibge","uf","municipio","codigo_tse","aptos","comparecimento","abstencoes","votos_validos","brancos","nulos","secoes"])
            export_query(db,a.out/"locais.csv", """
              SELECT m.codigo_ibge,a.uf,a.cd_tse,a.zona,a.local,
                     SUM(a.aptos),SUM(a.comparecimento),SUM(a.abstencoes),SUM(a.nominais),COUNT(*)
              FROM apuracao a JOIN municipios_tse_ibge m ON (a.uf,a.cd_tse)=(m.uf,m.cd_tse)
              GROUP BY m.codigo_ibge,a.uf,a.cd_tse,a.zona,a.local
              ORDER BY m.codigo_ibge,a.zona,a.local""",
              ["codigo_ibge","uf","codigo_tse","zona","local","aptos","comparecimento","abstencoes","votos_validos","secoes"])
            export_query(db,a.out/"candidatos_municipios.csv", """
              SELECT m.codigo_ibge,v.uf,v.cd_tse,v.votavel,MIN(v.nome_votavel),SUM(v.votos)
              FROM votos v JOIN municipios_tse_ibge m ON (v.uf,v.cd_tse)=(m.uf,m.cd_tse)
              WHERE v.votavel NOT IN ('95','96')
              GROUP BY m.codigo_ibge,v.uf,v.cd_tse,v.votavel ORDER BY m.codigo_ibge,v.votavel""",
              ["codigo_ibge","uf","codigo_tse","numero_candidato","nome_candidato","votos"])
            export_query(db,a.out/"secoes.csv", """
              SELECT m.codigo_ibge,a.uf,a.cd_tse,a.zona,a.secao,a.local,
                     a.aptos,a.comparecimento,a.abstencoes,a.nominais,a.brancos,a.nulos
              FROM apuracao a JOIN municipios_tse_ibge m ON (a.uf,a.cd_tse)=(m.uf,m.cd_tse)
              ORDER BY m.codigo_ibge,a.zona,a.secao""",
              ["codigo_ibge","uf","codigo_tse","zona","secao","local","aptos","comparecimento","abstencoes","votos_validos","brancos","nulos"])
    except Exception as e:
        report["resultado"]="ERRO"
        report["erro"]=str(e)
    finally:
        db.commit();db.close()
        (a.out/"validacao.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
        print(json.dumps(report,ensure_ascii=False,indent=2))
    if report["resultado"]!="PASS":
        raise SystemExit(1)

if __name__=="__main__":
    main()
