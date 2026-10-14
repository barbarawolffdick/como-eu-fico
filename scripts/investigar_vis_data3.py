"""Inspeciona metadados e scripts públicos VIS DATA 3 para localizar extração municipal."""
import re,urllib.request,urllib.parse,json
from html.parser import HTMLParser
BASE="https://aplicacoes.cidadania.gov.br"
URL=BASE+"/vis/data3/data-explorer.php"
req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0"})
with urllib.request.urlopen(req,timeout=45) as response:html=response.read().decode("utf-8","replace")
scripts=re.findall(r'<script[^>]+src=[\'"]([^\'"]+)',html,re.I)
links=re.findall(r'<a[^>]+href=[\'"]([^\'"]+)',html,re.I)
print(json.dumps({"url":URL,"size":len(html),"scripts":scripts[:35],"links":links[:25],
 "fragments":[html[max(0,m.start()-100):m.end()+150] for m in list(re.finditer(r"pessoas|ajax|json|endpoint|api/",html,re.I))[:12]]},ensure_ascii=False))
for key in ("Quantidade total de pessoas","pessoas em famílias","$.ajax","ajax:","url:","buscarIndicador","buscar_indicador","dataTable","data-explorer","vis/data3","api.php","v.php"):
 matches=list(re.finditer(re.escape(key),html,re.I))
 print(json.dumps({"pattern":key,"count":len(matches),"context":[html[max(0,m.start()-190):m.end()+340] for m in matches[:4]]},ensure_ascii=False))
for word in ("Quantidade total de pessoas em famílias beneficiárias","pessoas","beneficiárias"):
 url=URL+"?search="+urllib.parse.quote(word)
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=40) as response: page=response.read().decode("utf-8","replace")
  matchs=list(re.finditer("pessoas em famílias|pessoas|beneficiárias|v.php\\?",page,re.I))
  print(json.dumps({"termo":word,"bytes":len(page),"matches":len(matchs),"samples":[page[max(0,m.start()-240):m.end()+360] for m in matchs[:9]]},ensure_ascii=False))
 except Exception as e:print(json.dumps({"termo":word,"erro":str(e)}))
for src in scripts:
 if "vis" not in src and (src.startswith("https:") or src.startswith("//")):continue
 full=urllib.parse.urljoin(URL,src)
 if not full.startswith(BASE):continue
 try:
  with urllib.request.urlopen(urllib.request.Request(full,headers={"User-Agent":"Mozilla/5.0"}),timeout=20) as response:
   js=response.read(1000000).decode("utf-8","replace")
  matches=list(re.finditer(r"data3/|ajax|csv|api/|pessoas em famílias",js,re.I))
  if matches:print(json.dumps({"script":src,"size":len(js),"snippets":[js[max(0,m.start()-90):m.end()+140] for m in matches[:10]]},ensure_ascii=False))
 except Exception as e:print(json.dumps({"script":src,"erro":str(e)[:150]}))
