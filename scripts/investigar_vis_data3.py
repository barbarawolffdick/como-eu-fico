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
ix=html.find("busca_metadados_mis2.php")
print(json.dumps({"endpoint_block":html[max(0,ix-800):ix+3200] if ix>=0 else ""},ensure_ascii=False))
