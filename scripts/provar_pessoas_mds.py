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
cards=info["res"].split('<div class="card card-shadow card-item-')
cand=[]
for card in cards:
 marker='href="v.php?q[]='
 start=card.find(marker)
 if start<0:continue
 encrypted=card[start+len(marker):].split('"',1)[0]
 url='v.php?q[]='+encrypted
 plain=h.unescape(re.sub("<[^>]+>"," ",card))
 plain=" ".join(plain.split())
 cand.append((plain[:320],url))
print(json.dumps({"found":info.get("numFound"),"cards":len(cand),
 "titles":[{"texto":v[0][:260],"url_inicio":v[1][:90]} for v in cand[:12]]},ensure_ascii=False))
if not cand:raise SystemExit("Nenhum link v.php identificado")
chosen=next((v for v in cand if "Quantidade total de pessoas em famílias beneficiárias do Programa Bolsa Família" in v[0]),cand[0])
url=urllib.parse.urljoin(BASE,chosen[1])
with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=90) as res:
 page=res.read().decode("utf-8","replace")

match=re.search(r'<select[^>]+id="sltVariavelMapa[^"]+"[^>]*>(.*?)</select>',page,re.S|re.I)
if not match:raise SystemExit("Seleção do mapa não localizada")
opts=re.findall(r'<option([^>]*)>(.*?)</option>',match.group(1),re.S|re.I)
options=[]
for attrs,label in opts:
 attrs_dict=dict(re.findall(r'([a-zA-Z0-9_-]+)="([^"]*)"',attrs))
 options.append({"label":h.unescape(re.sub("<[^>]+>","",label)).strip(),**attrs_dict})


meta=page.find("objItensVisualizacaoInfo.push({'cab':'Quantidade total de pessoas em famílias beneficiárias do Programa Bolsa Família'")
if meta<0:raise SystemExit("Expressão oficial de total não encontrada")
fragment=page[meta:meta+2000]
qt=fragment.split("'u':'",1)[1].split("'",1)[0]
api="https://aplicacoes.cidadania.gov.br/vis/dash/sv-mapa-faixas.php?qe="+qt
params={"ref":"","ag":"p","area":"","area_user":"","temp":"1",
      "mes_ou_ano":"mes","p_ibge":"0","nr":"","ma":""}
for nome,extra in [("faixas",{"q":"4"}),("amostra",{"op":"1","wt":"json","f0":"1","f1":"10000","cor":"#195b49","v":"Quantidade total de pessoas em famílias beneficiárias do Programa Bolsa Família","vf":"numero"})]:
 req=urllib.request.Request(api,data=urllib.parse.urlencode({**params,**extra}).encode(),
  headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"},method="POST")
 try:
  with urllib.request.urlopen(req,timeout=140) as response:raw=response.read()
  obj=json.loads(raw)
  feats=obj.get("features",[])
  print(json.dumps({"teste":nome,"bytes":len(raw),"info":obj if nome=="faixas" else
    {"features":len(feats),"amostra":[x.get("properties") for x in feats[:4]]}},ensure_ascii=False))
 except Exception as e:print(json.dumps({"teste":nome,"erro":str(e)}))
