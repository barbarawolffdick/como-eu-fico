"""Localiza indicador de pessoas beneficiárias e verifica serviço territorial do VIS DATA 3."""
import json,re,urllib.parse,urllib.request,html as h
BASE="https://aplicacoes.cidadania.gov.br/vis/data3/"
END="https://aplicacoes.cidadania.gov.br/vis/tabelas/busca_metadados_mis2.php"
post={"q":"Quantidade total de pessoas em famílias beneficiárias do Programa Bolsa Família",
 "cpo":"relevancia","cpot":"asc","qt":"30","p":"0","str_prog":"",
 "str_unidade":"","t":"","sistemas":"","wiki":"","str_fonte":"",
 "fct":"programa_social_hd;fonte_cd;categoria_limp_s;unidade_cd",
 "palavras_chave":"","olvy":"1"}
req=urllib.request.Request(END,data=urllib.parse.urlencode(post).encode(),
 headers={"User-Agent":"Mozilla/5.0","Content-Type":"application/x-www-form-urlencoded"})
with urllib.request.urlopen(req,timeout=70) as res: info=json.loads(res.read())
cards=re.split(r'(?=<div class="card card-shadow card-item-)',info["res"])
cand=[]
for card in cards:
 match=re.search(r'href="(v\\.php\\?q\\[\\]=[^"]+)"',card)
 if not match:continue
 text=h.unescape(re.sub(r"<[^>]+>"," ",card))
 text=" ".join(text.split())
 cand.append((text[:320],h.unescape(match.group(1))))
print(json.dumps({"found":info.get("numFound"),"cards":len(cand),
 "titles":[{"texto":v[0][:260],"url_inicio":v[1][:90]} for v in cand[:12]]},ensure_ascii=False))
if not cand:raise SystemExit("Nenhum link v.php identificado")
chosen=next((v for v in cand if "Quantidade total de pessoas em famílias beneficiárias do Programa Bolsa Família" in v[0]),cand[0])
url=urllib.parse.urljoin(BASE,chosen[1])
with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=90) as res:
 page=res.read().decode("utf-8","replace")
patterns=("município","servicos/","tabelas/","csv","fetch(","$.ajax","dataTable","beneficiárias","referencia")
report={}
for key in patterns:
 ms=list(re.finditer(re.escape(key),page,re.I))
 report[key]={"count":len(ms),"samples":[page[max(0,m.start()-130):m.end()+250] for m in ms[:4]]}
print(json.dumps({"escolhido":chosen[0][:260],"url":url,"len":len(page),"indicadores":report},ensure_ascii=False))
