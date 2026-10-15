"""Investigação: buscar via consulta tabular do MDS seis municípios sem geometria.
Não publica nem preenche dados faltantes.
"""
import json,re,urllib.parse,urllib.request
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
