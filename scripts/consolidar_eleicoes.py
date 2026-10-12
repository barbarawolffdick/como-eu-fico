#!/usr/bin/env python3
"""Consolida resumos eleitorais municipais com IBGE e emite auditoria reproduzível."""
import argparse
import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

COLS = {
 "LOCAIS":"locais_votacao", "APTOS":"eleitores_aptos",
 "COMPARECIMENTO":"comparecimento", "ABSTENCOES":"abstencoes",
 "VOTOS VALIDOS":"votos_validos", "LULA":"votos_lula",
 "FLAVIO BOLSONARO":"votos_flavio",
 "LOCAIS LULA A FRENTE":"locais_lula_frente",
 "LOCAIS FLAVIO A FRENTE":"locais_flavio_frente",
 "LOCAIS EMPATE":"locais_empate"
}
PCT = {"% ABSTENCOES":"pct_abstencoes_origem",
 "% LULA (validos)":"pct_lula_origem",
 "% FLAVIO (validos)":"pct_flavio_origem",
 "DIFERENCA (p.p.)":"diferenca_pp_origem"}
FIELDS = ["codigo_ibge","uf","municipio_ibge","municipio_origem","ano_eleicao","turno",
          *COLS.values(), "votos_outros_candidatos",
          "pct_abstencoes","pct_lula_validos","pct_flavio_validos",
          "diferenca_votos_lula_menos_flavio","diferenca_pp_lula_menos_flavio",
          "metodo_correspondencia","arquivo_origem","linha_origem"]
CHECKS = ["arquivo_origem","linha_origem","codigo_ibge","uf","municipio_origem","regra","detalhe"]

def load(path, delimiter=","):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))

def write(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

def integer(value):
    s = str(value or "").strip()
    if not s or not s.isascii() or not s.isdigit():
        raise ValueError("inteiro inválido: "+repr(value))
    return int(s)

def decimal_pt(value):
    try:
        return Decimal(str(value).strip().replace(",", "."))
    except InvalidOperation as e:
        raise ValueError("decimal inválido: "+repr(value)) from e

def percent(num, den):
    if not den:
        return Decimal("0")
    return Decimal(100)*Decimal(num)/Decimal(den)

def display(value):
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=Path("dados-municipios"))
    p.add_argument("--data", type=Path, default=Path("data"))
    p.add_argument("--ano", type=int, default=2026)
    p.add_argument("--turno", type=int, default=1)
    a=p.parse_args()
    mapping=load(a.data/"reference"/"municipios_mapeados.csv")
    by_source={(x["arquivo_origem"],int(x["linha_origem"])):x for x in mapping}
    files=sorted(a.source.glob("*/resumo_municipios_*.csv"))
    out, issues=[],[]
    seen=set()
    def issue(base,rule,detail):
        issues.append({**base,"regra":rule,"detalhe":str(detail)})
    for path in files:
        for line,raw in enumerate(load(path,";"),2):
            base={"arquivo_origem":str(path),"linha_origem":line,
                  "codigo_ibge":"","uf":raw.get("UF",""),"municipio_origem":raw.get("MUNICIPIO","")}
            reference=by_source.get((str(path),line))
            if reference is None:
                issue(base,"sem_codigo_ibge","Correspondência territorial ausente")
                continue
            base["codigo_ibge"]=reference["codigo_ibge"]
            if reference["uf"]!=base["uf"] or reference["municipio_origem"]!=base["municipio_origem"]:
                issue(base,"correspondencia_desatualizada","UF/nome difere do mapeamento")
                continue
            code=reference["codigo_ibge"]
            if code in seen:
                issue(base,"codigo_duplicado",code)
                continue
            seen.add(code)
            try:
                vals={dest:integer(raw[src]) for src,dest in COLS.items()}
                raw_pct={dest:decimal_pt(raw[src]) for src,dest in PCT.items()}
                difference=integer(raw["DIFERENCA (votos)"].lstrip("-")) * (-1 if str(raw["DIFERENCA (votos)"]).startswith("-") else 1)
            except (KeyError,ValueError) as e:
                issue(base,"campo_invalido",e)
                continue
            apt,attendance,absent,valid=(
                vals["eleitores_aptos"],vals["comparecimento"],vals["abstencoes"],vals["votos_validos"])
            lula,flavio=vals["votos_lula"],vals["votos_flavio"]
            if apt!=attendance+absent: issue(base,"eleitorado","aptos != comparecimento + abstenções")
            if valid>attendance: issue(base,"comparecimento","votos válidos > comparecimento")
            if lula+flavio>valid: issue(base,"votos_candidatos","soma dos candidatos > votos válidos")
            if vals["locais_lula_frente"]+vals["locais_flavio_frente"]+vals["locais_empate"]!=vals["locais_votacao"]:
                issue(base,"locais","distribuição de locais difere do total")
            if lula-flavio!=difference: issue(base,"diferenca_votos","diferença original difere do cálculo")
            calculated={
                "pct_abstencoes":percent(absent,apt),
                "pct_lula_validos":percent(lula,valid),
                "pct_flavio_validos":percent(flavio,valid),
                "diferenca_pp_lula_menos_flavio":percent(lula-flavio,valid)
            }
            comparisons={
                "pct_abstencoes":raw_pct["pct_abstencoes_origem"],
                "pct_lula_validos":raw_pct["pct_lula_origem"],
                "pct_flavio_validos":raw_pct["pct_flavio_origem"],
                "diferenca_pp_lula_menos_flavio":raw_pct["diferenca_pp_origem"]
            }
            for metric,calc in calculated.items():
                if abs(calc-comparisons[metric])>Decimal("0.02"):
                    issue(base,"percentual_divergente",f"{metric}: calculado={display(calc)}, origem={comparisons[metric]}")
            out.append({
                **reference,**vals,"ano_eleicao":a.ano,"turno":a.turno,
                "votos_outros_candidatos":valid-lula-flavio,
                **{k:display(v) for k,v in calculated.items()},
                "diferenca_votos_lula_menos_flavio":lula-flavio
            })
    write(a.data/"processed"/"eleicoes_2026_municipios.csv",out,FIELDS)
    write(a.data/"quality"/"inconsistencias_eleitorais.csv",issues,CHECKS)
    missing_codes={x["codigo_ibge"] for x in mapping}-{x["codigo_ibge"] for x in out}
    report={"ano":a.ano,"turno":a.turno,"arquivos_processados":len(files),
            "registros_consolidados":len(out),"municipios_sem_saida":len(missing_codes),
            "inconsistencias":len(issues),"por_regra":dict(Counter(x["regra"] for x in issues)),
            "aviso":"Verificações internas aos CSVs; NÃO é conferência com resultados oficiais do TSE."}
    (a.data/"quality"/"resumo_eleitoral.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    if not files or len(files)!=27 or issues or missing_codes or len(out)!=len(mapping):
        raise SystemExit(1)

if __name__=="__main__":
    main()
