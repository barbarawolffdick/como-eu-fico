"""Localiza id e URL do indicador oficial de pessoas PBF no catálogo VIS DATA 3."""
import json,re,urllib.parse,urllib.request
BASE="https://aplicacoes.cidadania.gov.br/vis"
url=BASE+"/tabelas/busca_metadados_mis2.php"
for termo in ("Quantidade total de pessoas em famílias beneficiárias","pessoas em famílias beneficiárias"):
 params={"q":termo,"cpo":"relevancia","cpot":"asc","qt":"30","p":"0","str_prog":"",
 "str_unidade":"","t":"","sistemas":"","wiki":"","str_fonte":"",
 "fct":"programa_social_hd;fonte_cd;categoria_limp_s;unidade_cd",
 "palavras_chave":"","olvy":"1"}
 req=urllib.request.Request(url,data=urllib.parse.urlencode(params).encode(),
   headers={"User-Agent":"Mozilla/5.0","Accept":"application/json","Content-Type":"application/x-www-form-urlencoded"})
 try:
  with urllib.request.urlopen(req,timeout=65) as resp:
   raw=resp.read()
  obj=json.loads(raw)
  html=obj.get("res","") or ""
  snippets=[]
  for m in list(re.finditer("Quantidade total de pessoas|pessoas em famílias|q\\[\\]|v.php",html,re.I))[:12]:
   snippets.append(html[max(0,m.start()-230):m.end()+360])
  print(json.dumps({"termo":termo,"numFound":obj.get("numFound"),"keys":list(obj),
   "res_bytes":len(html),"snippets":snippets,"head":html[:800]},ensure_ascii=False))
 except Exception as e:
  print(json.dumps({"termo":termo,"erro":str(e)},ensure_ascii=False))
