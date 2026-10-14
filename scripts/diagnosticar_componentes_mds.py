"""Auditoria exploratória: componentes municipais do indicador pessoas PBF (não publica sem validar)."""
import hashlib,html,json,re,unicodedata,urllib.parse,urllib.request
from pathlib import Path
BASE="https://aplicacoes.cidadania.gov.br/vis/data3/"
END="https://aplicacoes.cidadania.gov.br/vis/tabelas/busca_metadados_mis2.php"
def read(url,post=None):
 req=urllib.request.Request(url,data=urllib.parse.urlencode(post).encode() if post is not None else None,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=170) as response:return response.read()
post={"q":"Quantidade total de pessoas em famílias beneficiárias do Programa Bolsa Família","cpo":"relevancia","cpot":"asc","qt":"30","p":"0","str_prog":"","str_unidade":"","t":"","sistemas":"","wiki":"","str_fonte":"","fct":"programa_social_hd;fonte_cd;categoria_limp_s;unidade_cd","palavras_chave":"","olvy":"1"}
catalog=json.loads(read(END,post))
card=catalog["res"].split('<div class="card card-shadow card-item-')[1]
token=card.split('href="v.php?q[]=',1)[1].split('"',1)[0]
url=BASE+"v.php?q[]="+token
page=read(url).decode("utf-8","replace")
match=re.search(r'<select[^>]+id="sltVariavelMapa[^"]+"[^>]*>(.*?)</select>',page,re.S|re.I)
opts=re.findall(r'<option([^>]*)>(.*?)</option>',match.group(1),re.S|re.I)
report=[]
for attrs,label in opts:
 values=dict(re.findall(r'([a-zA-Z0-9_-]+)="([^"]*)"',attrs))
 if "value" not in values:continue
 name=html.unescape(re.sub(r"<[^>]+>","",label)).strip()
 api="https://aplicacoes.cidadania.gov.br/vis/dash/sv-mapa-faixas.php?qe="+values["value"]
 params={"ref":"","ag":"p","area":"","area_user":"","temp":"1","mes_ou_ano":"mes","p_ibge":"0","nr":"","ma":"","op":"1","wt":"json","f0":"0","f1":"2000000","cor":"#195b49","v":name,"vf":"numero"}
 raw=read(api,params)
 obj=json.loads(raw)
 features=obj.get("features",[])
 counts={}
 values_sample=[]
 dates=set()
 for f in features:
  p=f.get("properties",{})
  key=(p.get("uf"),p.get("nome"))
  if key in counts:raise ValueError("Duplicidade territorial "+repr(key))
  popup=p.get("popupContent","")
  m=re.search(r":\\s*([0-9][0-9.]*)<br>",popup)
  if not m:raise ValueError("Sem valor no mapa "+popup[:220])
  counts[key]=int(m.group(1).replace(".",""))
  dates.add(p.get("referencia"))
  if len(values_sample)<2:values_sample.append({"uf":key[0],"nome":key[1],"valor":counts[key]})
 report.append({"variavel":name,"features":len(features),"data":sorted(dates),"total":sum(counts.values()),"amostra":values_sample,"sha256":hashlib.sha256(raw).hexdigest(),"chaves":counts})
 print(json.dumps({k:v for k,v in report[-1].items() if k!="chaves"},ensure_ascii=False),flush=True)
unique=set().union(*(set(r["chaves"]) for r in report))
intersection=set.intersection(*(set(r["chaves"]) for r in report))
print(json.dumps({"uniao":len(unique),"intersecao":len(intersection),"faltas_por_categoria":[len(unique-set(r["chaves"])) for r in report],"soma_componentes":sum(r["total"] for r in report)},ensure_ascii=False),flush=True)
resp=json.loads(read(url+"&wt=json&tp_funcao_consulta=0",{"start":"0","length":"100","wt":"json"}))
print(json.dumps({"brasil_series_tail":resp.get("data",[])[-6:],"n_rows":resp.get("recordsTotal")},ensure_ascii=False),flush=True)
