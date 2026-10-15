"""Investigação: buscar via consulta tabular do MDS seis municípios sem geometria.
Não publica nem preenche dados faltantes.
"""
import json,re,urllib.parse,urllib.request
from scripts.sondar_mds_vis import Table
SEARCH="https://aplicacoes.cidadania.gov.br/vis/tabelas/busca_metadados_mis2.php"
BASE="https://aplicacoes.cidadania.gov.br/vis/data3/"
params={"q":"Quantidade total de pessoas em famílias beneficiárias do Programa Bolsa Família",
 "cpo":"relevancia","cpot":"asc","qt":"30","p":"0","str_prog":"","str_unidade":"",
 "t":"","sistemas":"","wiki":"","str_fonte":"",
 "fct":"programa_social_hd;fonte_cd;categoria_limp_s;unidade_cd",
 "palavras_chave":"","olvy":"1"}
def read(url,post=None):
 req=urllib.request.Request(url,data=urllib.parse.urlencode(post).encode() if post is not None else None,
   headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=70) as response:return response.read()
catalog=json.loads(read(SEARCH,params))["res"]
card=catalog.split('<div class="card card-shadow card-item-')[1]
token=card.split('href="v.php?q[]=',1)[1].split('"',1)[0]
url=BASE+"v.php?q[]="+token
page=read(url).decode("utf-8","replace")
for needle in ("tpconsulta=1","num_total_rows","10 Maiores","function inicializaAbaMaiores","function inicializaAbaMenores","function visualiza_maiores","tp_funcao_consulta"):
 hits=list(re.finditer(re.escape(needle),page,re.I))
 print(json.dumps({"needle":needle,"count":len(hits),"snippets":[page[max(0,m.start()-400):m.end()+1900] for m in hits[:2]]},ensure_ascii=False))
for params in (
 {"start":"0","length":"10000","page":"1","registros":"6000"},
 {"start":"0","length":"10000","p":"1","qt":"6000"},
 {"page":"1","per_page":"6000","municipios":"1"},
):
 data=json.loads(read(url+"&tpconsulta=1",params))
 objects=[(k,len(v.get("dados",[]))) for k,v in data.items() if isinstance(v,dict)]
 print(json.dumps({"request_params":params,"items":objects},ensure_ascii=False))

# Consulta direta ao módulo de tabelas com nomes de variáveis publicados no VIS DATA 3.
TABLE="https://aplicacoes.cidadania.gov.br/vis/tabelas/tabela.php"
for variable in ("n_pess_cad_pbf",):
 query={"cfc":f"prog=1$banco=Producao$referencia=2026-08-01|$vars={variable}",
        "exibe_num":"1","exibir_codigo_divisao":"1","iuid":"78273","pagina":"1",
        "paginacao":"1","registros":"6000","tipo_divisao":"m"}
 uri=TABLE+"?"+urllib.parse.urlencode(query)
 try:
  with urllib.request.urlopen(urllib.request.Request(uri,headers={"User-Agent":"Mozilla/5.0"}),timeout=35) as response:
   body=response.read()
  decoded=body.decode("utf-8","replace")
  parsed=Table();parsed.feed(decoded)
  probes={}
  for fragment in ("Moju","MOJU","150475","510183","421265","Pescaria","Boa Esper","São Paulo","355030"):
   k=decoded.lower().find(fragment.lower())
   probes[fragment]=decoded[max(0,k-130):k+260] if k>=0 else None
  wanted={"150475","421265","422000","431454","500627","510183","355030"}
  target=[row for row in parsed.rows if len(row)>2 and row[2].strip() in wanted]
  raw_snippets={}
  for city in ("MOJUÍ DOS CAMPOS","SÃO PAULO"):
   pos=decoded.find(city)
   raw_snippets[city]=decoded[max(0,pos-500):pos+1600] if pos>=0 else "ausente"
  print(json.dumps({"variavel":variable,"rows":len(parsed.rows),"headers":parsed.rows[:2],
        "target_rows":target,"html_registros":raw_snippets},ensure_ascii=False))
 except Exception as error:
  print(json.dumps({"variavel":variable,"erro":str(error)},ensure_ascii=False))
