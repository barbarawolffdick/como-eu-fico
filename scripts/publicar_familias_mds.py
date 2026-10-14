"""Publica duas fotografias oficiais de famílias beneficiárias do Bolsa Família (MDS/VIS DATA).
Não interpreta famílias como pessoas; não mistura com registros de parcelas da CGU.
"""
import hashlib,json,re,sqlite3,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from scripts.sondar_mds_vis import Table,BASE

ROOT=Path(__file__).resolve().parents[1]
MONTHS=("2025-01-01","2026-08-01")
OUT=ROOT/"data/public/familias_mds.json"

def fetch(period):
    params={"cfc":f"prog=1$banco=Producao$referencia={period}|$vars=bf_qtd_fam",
        "exibe_num":"1","exibir_codigo_divisao":"1","iuid":"78273",
        "pagina":"1","paginacao":"1","registros":"6000","tipo_divisao":"m"}
    url=BASE+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"ComoEuFico/1.0","Accept":"text/html"})
    with urllib.request.urlopen(req,timeout=150) as response:body=response.read()
    parser=Table();parser.feed(body.decode("utf-8",errors="replace"))
    return parser.rows,hashlib.sha256(body).hexdigest(),url

def extract(rows,period,codes):
    by_six={code[:6]:code for code in codes}
    if len(by_six)!=len(codes):raise ValueError("Chaves IBGE de seis dígitos ambíguas")
    result={}
    for row in rows:
        if len(row)<5:continue
        six=row[2].strip()
        if not (len(six)==6 and six.isascii() and six.isdigit()):continue
        if six not in by_six:raise ValueError("Município MDS desconhecido: "+six)
        code=by_six[six]
        if code in result:raise ValueError("Município duplicado: "+code)
        raw=row[4].strip().replace(".","")
        if not raw.isascii() or not raw.isdigit():raise ValueError("Famílias inválidas: "+repr(row))
        result[code]=int(raw)
    if set(result)!=codes:raise ValueError("Cobertura MDS divergente: "+str({"presentes":len(result),"faltantes":len(codes-set(result))}))
    return result

def run():
    with sqlite3.connect(f"file:{(ROOT/'data/app/como_eu_fico.sqlite').resolve()}?mode=ro",uri=True) as db:
        codes={r[0] for r in db.execute("SELECT codigo_ibge FROM municipios")}
    if len(codes)!=5571:raise ValueError("Banco municipal incompleto")
    series={};proveniencia={}
    for date in MONTHS:
        rows,digest,url=fetch(date)
        series[date[:7].replace("-","")]=extract(rows,date,codes)
        proveniencia[date]={"url":url,"sha256_resposta":digest}
    document={"esquema":1,"unidade":"familias_beneficiarias","fonte":"MDS VIS DATA",
       "coleta_utc":datetime.now(timezone.utc).isoformat(),"municipios":len(codes),
       "periodos":list(series),"proveniencia":proveniencia,"registros":series}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(document,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print(json.dumps({"arquivo":str(OUT),"periodos":list(series),"municipios":len(codes),
      "familias_nacionais":{k:sum(v.values()) for k,v in series.items()}},ensure_ascii=False))
if __name__=="__main__":run()
