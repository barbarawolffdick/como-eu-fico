#!/usr/bin/env python3
"""Diagnóstico independente: consistência de votos versus atribuição de locais."""
import argparse
import csv
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

def report(db):
    queries = {
      "secoes_apuracao": "SELECT COUNT(*) FROM apuracao",
      "secoes_distintas_votacao": "SELECT COUNT(*) FROM (SELECT DISTINCT uf,cd_tse,zona,secao FROM votos)",
      "municipios_tse": "SELECT COUNT(*) FROM (SELECT DISTINCT uf,cd_tse FROM apuracao)",
      "municipios_mapeados_ibge": "SELECT COUNT(*) FROM municipios_tse_ibge",
      "secoes_sem_apuracao": """SELECT COUNT(*) FROM (SELECT DISTINCT v.uf,v.cd_tse,v.zona,v.secao FROM votos v
        LEFT JOIN apuracao a ON a.uf=v.uf AND a.cd_tse=v.cd_tse AND a.zona=v.zona AND a.secao=v.secao
        WHERE a.uf IS NULL)""",
      "secoes_sem_votacao": """SELECT COUNT(*) FROM apuracao a WHERE NOT EXISTS
        (SELECT 1 FROM votos v WHERE v.uf=a.uf AND v.cd_tse=a.cd_tse AND v.zona=a.zona AND v.secao=a.secao)""",
      "secoes_composicao_divergente": """SELECT COUNT(*) FROM (
        SELECT a.uf,a.cd_tse,a.zona,a.secao,a.nominais,a.brancos,a.nulos,
          a.comparecimento,a.legenda,a.anulados,
          COALESCE(SUM(CASE WHEN v.votavel NOT IN ('95','96') THEN v.votos ELSE 0 END),0) as nom,
          COALESCE(SUM(CASE WHEN v.votavel='95' THEN v.votos ELSE 0 END),0) as bra,
          COALESCE(SUM(CASE WHEN v.votavel='96' THEN v.votos ELSE 0 END),0) as nul
        FROM apuracao a LEFT JOIN votos v ON a.uf=v.uf AND a.cd_tse=v.cd_tse AND a.zona=v.zona AND a.secao=v.secao
        GROUP BY a.uf,a.cd_tse,a.zona,a.secao
        HAVING nom!=a.nominais OR bra!=a.brancos OR nul!=a.nulos
          OR a.nominais+a.brancos+a.nulos+a.legenda+a.anulados!=a.comparecimento
          OR a.legenda!=0 OR a.anulados!=0)""",
      "secoes_local_divergente": """SELECT COUNT(*) FROM (
        SELECT a.uf,a.cd_tse,a.zona,a.secao
        FROM apuracao a JOIN votos v
          ON a.uf=v.uf AND a.cd_tse=v.cd_tse AND a.zona=v.zona AND a.secao=v.secao
        GROUP BY a.uf,a.cd_tse,a.zona,a.secao
        HAVING MIN(v.local)!=MAX(v.local) OR a.local!=MIN(v.local))""",
    }
    values={name:db.execute(query).fetchone()[0] for name,query in queries.items()}
    electoral_ok=(values["secoes_sem_apuracao"]==0 and values["secoes_sem_votacao"]==0 and
                   values["secoes_composicao_divergente"]==0)
    geographic_ok=values["secoes_local_divergente"]==0
    return {"gerado_em_utc":datetime.now(timezone.utc).isoformat(),
            "metricas":values,
            "consistencia_eleitoral":"PASS" if electoral_ok else "FAIL",
            "identificacao_locais":"PASS" if geographic_ok else "PENDENTE",
            "correspondencia_ibge":"PENDENTE",
            "publicacao":"BLOQUEADA",
            "nota":"Diagnóstico sem correções. PASS eleitoral não certifica mapeamento territorial nem locais."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",type=Path,default=Path("data/tse_oficial/eleicoes_2026.sqlite"))
    p.add_argument("--out",type=Path,default=Path("data/tse_oficial/diagnostico_independente.json"))
    a=p.parse_args()
    if not a.db.is_file():
        p.error("Banco SQLite não encontrado: "+str(a.db))
    with sqlite3.connect("file:"+str(a.db.resolve())+"?mode=ro",uri=True) as db:
        data=report(db)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
