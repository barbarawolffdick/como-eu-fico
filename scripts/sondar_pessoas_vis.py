"""Testa indicadores possíveis no endpoint legado do MDS, sem publicar dados."""
import json, urllib.parse, urllib.request
from html.parser import HTMLParser
from scripts.sondar_mds_vis import Table,BASE

CANDIDATOS=["bf_qtd_pes","bf_qtd_pessoas","bf_qtd_pes_ben","bf_qtd_pes_beneficiarias","bf_pessoas","bf_qtd_beneficiarios"]
def run(periodo="2026-02-01"):
 for variable in CANDIDATOS:
  params={"cfc":f"prog=1$banco=Producao$referencia={periodo}|$vars={variable}",
    "exibe_num":"1","exibir_codigo_divisao":"1","iuid":"78273","pagina":"1",
    "paginacao":"1","registros":"3","tipo_divisao":"m"}
  url=BASE+"?"+urllib.parse.urlencode(params)
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"ComoEuFico/1.0"}),timeout=22) as res:
    body=res.read()
   table=Table();table.feed(body.decode("utf-8",errors="replace"))
   print(json.dumps({"variavel":variable,"bytes":len(body),"linhas":len(table.rows),
     "cabecalhos":table.rows[:2],"amostra":table.rows[2:4]},ensure_ascii=False),flush=True)
  except Exception as exc: print(json.dumps({"variavel":variable,"erro":str(exc)[:150]}),flush=True)

if __name__=="__main__":run()
