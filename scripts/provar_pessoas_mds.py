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
for key in ("url+='&tpconsulta","&tpconsulta","function export_csv(","function inicializaTabela","type:'POST'","ajax: {","url_aux_export","getInfoMetadadoPagina"):
 pos=page.find(key)
 print(json.dumps({"chave":key,"ocorrencia":pos,"codigo":page[max(0,pos-180):pos+4100] if pos>=0 else ""},ensure_ascii=False))
