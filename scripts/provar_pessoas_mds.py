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

qe=options[0]["value"]
mapurl="https://aplicacoes.cidadania.gov.br/vis/dash/sv-mapa-faixas.php?qe="+qe
base={"ref":"2026-09-01","ag":"p","area":"","area_user":"","temp":"1",
      "mes_ou_ano":"mes","p_ibge":"0","nr":"","ma":""}
for name,extra in [("faixas",{"q":"4"}),("valores",{"op":"1","wt":"json","f0":"0","f1":"99999999","cor":"#195b49",
    "v":options[0]["label"],"vf":"numero"})]:
 req=urllib.request.Request(mapurl,data=urllib.parse.urlencode({**base,**extra}).encode(),
   headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"},method="POST")
 try:
  with urllib.request.urlopen(req,timeout=140) as response:raw=response.read()
  try:
   parsed=json.loads(raw)
   if isinstance(parsed,dict):
    feats=parsed.get("features",parsed.get("r",[]))
    summ={"keys":list(parsed.keys())[:20],"items":len(feats) if isinstance(feats,list) else None,
     "sample":feats[:2] if isinstance(feats,list) else None}
   else:summ={"tipo":type(parsed).__name__,"items":len(parsed),"sample":parsed[:2]}
  except Exception:summ={"prefix":raw[:300].decode("utf-8","replace")}
  print(json.dumps({"teste":name,"bytes":len(raw),"resultado":summ},ensure_ascii=False))
 except Exception as e:print(json.dumps({"teste":name,"erro":str(e)},ensure_ascii=False))
