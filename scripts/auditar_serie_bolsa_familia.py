#!/usr/bin/env python3
"""Auditoria longitudinal de agregados CGU. Somente leitura; não requer internet."""
import argparse
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

def audit(path):
    uri=path.resolve().as_uri()+"?mode=ro"
    with sqlite3.connect(uri,uri=True) as db:
        db.row_factory=sqlite3.Row
        if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
            raise ValueError("Integridade SQLite falhou")
        origins=[dict(r) for r in db.execute("SELECT * FROM origem ORDER BY mes_competencia")]
        months=[r["mes_competencia"] for r in origins]
        if months!=[f"{y}{m:02d}" for y in (2025,2026) for m in range(1,13) if "202501"<=f"{y}{m:02d}"<="202608"]:
            raise ValueError("Banco não contém exatamente 202501–202608")
        series=[]
        sets={}
        references=[]
        alerts=[]
        for origin in origins:
            month=origin["mes_competencia"]
            rows=list(db.execute("""
                SELECT mes_referencia, codigo_ibge, valor_centavos, quantidade_parcelas
                FROM parcelas_municipais WHERE mes_competencia=?
            """,(month,)))
            keys={r["codigo_ibge"] for r in rows}
            sets[month]=keys
            count=sum(r["quantidade_parcelas"] for r in rows)
            cents=sum(r["valor_centavos"] for r in rows)
            if (count,cents,len(keys))!=(origin["parcelas"],origin["valor_centavos"],origin["municipios"]):
                raise ValueError("Divergência em "+month)
            refdata=defaultdict(lambda:[0,0])
            invalid=0
            zeros=0
            negatives=0
            for r in rows:
                ref=r["mes_referencia"]
                if not re.fullmatch(r"20\d{2}(0[1-9]|1[0-2])",ref) or ref>month:invalid+=1
                if r["valor_centavos"]==0:zeros+=1
                if r["valor_centavos"]<0:negatives+=1
                refdata[ref][0]+=r["quantidade_parcelas"]
                refdata[ref][1]+=r["valor_centavos"]
            if invalid: alerts.append({"mes":month,"problema":"referencias_invalidas","grupos":invalid})
            current=refdata.get(month,[0,0])
            prev_count=count-current[0]
            prev_value=cents-current[1]
            series.append({
                "mes_competencia":month,"parcelas":count,"valor_centavos":cents,
                "municipios":len(keys),"parcelas_referencia_igual":current[0],
                "parcelas_referencia_anterior":prev_count,
                "percentual_parcelas_referencia_anterior":round(100*prev_count/count,4) if count else None,
                "centavos_referencia_anterior":prev_value,
                "grupos_valor_zero":zeros,"grupos_valor_negativo":negatives,
                "meses_referencia":[{"mes":r,"parcelas":v[0],"centavos":v[1]} for r,v in sorted(refdata.items())]
            })
        changes=[]
        for earlier,later in zip(months,months[1:]):
            entered=sorted(sets[later]-sets[earlier])
            exited=sorted(sets[earlier]-sets[later])
            if entered or exited:
                changes.append({"de":earlier,"para":later,"entraram":entered,"sairam":exited})
        first_presence={}
        for month in months:
            for code in sets[month]:
                first_presence.setdefault(code,month)
        if len(sets[months[-1]])!=5571:
            alerts.append({"problema":"cobertura_final_diferente_5571","municipios":len(sets[months[-1]])})
        # Presença de município novo não prova o motivo jurídico/administrativo da mudança.
        return {
            "status":"PASS_COM_RESSALVAS" if alerts else "PASS",
            "fonte":"SQLite de agregados Novo Bolsa Familia",
            "periodo":[months[0],months[-1]],
            "total_parcelas":sum(x["parcelas"] for x in series),
            "total_centavos":sum(x["valor_centavos"] for x in series),
            "municipios_unicos_no_periodo":len(set.union(*sets.values())),
            "primeira_presenca_boa_esperanca_do_norte":first_presence.get("5101837"),
            "mudancas_conjunto_municipal":changes,
            "serie":series,"alertas":alerts,
            "observacoes":[
                "Parcelas nao sao familias ou pessoas unicas.",
                "Competencia e referencia sao eixos distintos; referencia anterior nao comprova pagamento retroativo.",
                "A verificacao de valores zeros/negativos incide em grupos municipais agregados, nao em parcelas individuais.",
                "A cobertura territorial precisa ser cotejada com IBGE/TSE; este script so usa o SQLite CGU.",
                "Nao ha afirmacao causal sobre mudancas de parcelas ou valores."
            ]
        }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",type=Path,required=True)
    p.add_argument("--saida",type=Path,default=Path("auditoria_longitudinal_bolsa_202501_202608.json"))
    a=p.parse_args()
    if not a.db.is_file():p.error("SQLite nao encontrado: "+str(a.db))
    result=audit(a.db)
    a.saida.parent.mkdir(parents=True,exist_ok=True)
    a.saida.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("status","periodo","total_parcelas","total_centavos","municipios_unicos_no_periodo","primeira_presenca_boa_esperanca_do_norte","mudancas_conjunto_municipal","alertas")},ensure_ascii=False,indent=2))
    print("Relatorio:",a.saida)
if __name__=="__main__":main()
