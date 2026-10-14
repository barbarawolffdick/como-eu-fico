"""Publica cobertura populacional municipal PBF, soma oficial de três faixas disjuntas MDS VIS DATA 3."""
import hashlib,html,json,re,unicodedata,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"data/public/pessoas_mds.json"
BASE="https://aplicacoes.cidadania.gov.br/vis/data3/"
SEARCH="https://aplicacoes.cidadania.gov.br/vis/tabelas/busca_metadados_mis2.php"
MAP="https://aplicacoes.cidadania.gov.br/vis/dash/sv-mapa-faixas.php?qe="
PERIODO="202608"
LABELS=("em situação de pobreza, segundo a faixa do Programa","de baixa renda","acima de meio salário-mínimo")
def request(url,post=None):
    req=urllib.request.Request(url,
      data=urllib.parse.urlencode(post).encode() if post is not None else None,
      headers={"User-Agent":"ComoEuFico/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=175) as res:return res.read()
def norm(s):
    s=unicodedata.normalize("NFKD",str(s).upper())
    return re.sub(r"[^A-Z0-9]","", "".join(ch for ch in s if not unicodedata.combining(ch)))
def extract_options(page):
    m=re.search(r'<select[^>]+id="sltVariavelMapa[^"]+"[^>]*>(.*?)</select>',page,re.S|re.I)
    if not m:raise ValueError("Indicadores municipais ausentes na página VIS DATA")
    opts=[]
    for attrs,label in re.findall(r'<option([^>]*)>(.*?)</option>',m.group(1),re.S|re.I):
        attrs=dict(re.findall(r'([A-Za-z0-9_-]+)="([^"]*)"',attrs))
        if "value" not in attrs:continue
        opts.append((html.unescape(re.sub(r"<[^>]+>","",label)).strip(),attrs["value"]))
    if len(opts)!=3 or not all(any(mark in x[0] for x in opts) for mark in LABELS):
        raise ValueError("Faixas MDS inesperadas: "+str([o[0] for o in opts]))
    return opts
def parse_features(obj,title):
    if obj.get("type")!="FeatureCollection":raise ValueError("Resposta de mapa não é GeoJSON")
    result={};ref=set()
    for item in obj.get("features",[]):
        p=item.get("properties",{})
        key=(str(p.get("uf","")),norm(p.get("nome","")))
        popup=p.get("popupContent","")
        if title not in popup:raise ValueError("Indicador diferente do selecionado: "+popup[:150])
        m=re.search(r":\s*([0-9][0-9.]*)<br>",popup)
        if not m:raise ValueError("Quantidade municipal inválida: "+popup[:150])
        n=int(m.group(1).replace(".",""))
        if key in result:raise ValueError("Município duplicado "+repr(key))
        result[key]=n
        ref.add(str(p.get("referencia","")))
    if ref!={"2026-08-01"}:raise ValueError("Competência do mapa diferente de agosto 2026: "+repr(ref))
    if len(result)<5500:raise ValueError("Cobertura geográfica baixa: "+str(len(result)))
    return result
def run():
    source=json.loads((ROOT/"data/public/rankings_2026.json").read_text(encoding="utf-8"))
    rows=source["registros"]
    if len(rows)!=5571 or not source.get("populacao_completa"):raise ValueError("Cadastro/população IBGE não validado")
    keys={}
    for m in rows:
        key=(m["uf"],norm(m["nome"]))
        if key in keys:raise ValueError("Municípios com nomes IBGE ambíguos: "+str(key))
        keys[key]=m
    params={"q":"Quantidade total de pessoas em famílias beneficiárias do Programa Bolsa Família",
      "cpo":"relevancia","cpot":"asc","qt":"30","p":"0","str_prog":"",
      "str_unidade":"","t":"","sistemas":"","wiki":"","str_fonte":"",
      "fct":"programa_social_hd;fonte_cd;categoria_limp_s;unidade_cd",
      "palavras_chave":"","olvy":"1"}
    cat=json.loads(request(SEARCH,params))
    first=cat["res"].split('<div class="card card-shadow card-item-')[1]
    fragment=first.split('href="v.php?q[]=',1)[1].split('"',1)[0]
    pageurl=BASE+"v.php?q[]="+fragment
    page=request(pageurl).decode("utf-8","replace")
    options=extract_options(page)
    extracts=[];provenance=[]
    for title,token in options:
        body=request(MAP+token,{"ref":"2026-08-01","ag":"p","area":"","area_user":"",
          "temp":"1","mes_ou_ano":"mes","p_ibge":"0","nr":"","ma":"",
          "op":"1","wt":"json","f0":"0","f1":"2000000","cor":"#195b49","v":title,"vf":"numero"})
        byname=parse_features(json.loads(body),title)
        extracts.append(byname)
        provenance.append({"variavel":title,"url":MAP+token,
            "sha256_resposta_geojson":hashlib.sha256(body).hexdigest(),
            "municipios_com_geometria":len(byname),"total_na_resposta":sum(byname.values())})
        print(json.dumps({k:v for k,v in provenance[-1].items() if k!="url"},ensure_ascii=False),flush=True)
    sets=[set(x) for x in extracts]
    if sets[0]!=sets[1] or sets[0]!=sets[2]:raise ValueError("Faixas com cobertura municipal diferente")
    extra=sets[0]-set(keys)
    if len(extra)>50:raise ValueError("Mais de 50 nomes territoriais sem correspondência IBGE: "+repr(sorted(extra)[:20]))
    print(json.dumps({"nomes_mds_sem_correspondencia":sorted(extra)},ensure_ascii=False),flush=True)
    available=sets[0]&set(keys)
    data={}
    excess=[]
    for key,m in keys.items():
        n=sum(x[key] for x in extracts) if key in available else None
        pop=m["populacao"]
        ratio=round(n/pop*100,4) if n is not None else None
        if ratio is not None and ratio>100:excess.append((m["codigo_ibge"],ratio))
        data[m["codigo_ibge"]]={"pessoas":n,"populacao":pop,"cobertura_pct":ratio}
    if excess:raise ValueError("Coberturas acima de 100% exigem revisão: "+repr(excess[:15]))
    result={"esquema":1,"fonte":"MDS VIS DATA 3","unidade":"pessoas_em_familias_beneficiarias",
       "periodo":PERIODO,"referencia_populacao":2026,
       "municipios_ibge":5571,"municipios_com_dado":len(available),
       "municipios_sem_dado":sorted(m["codigo_ibge"] for key,m in keys.items() if key not in available),
       "nomes_mds_sem_correspondencia":[list(x) for x in sorted(extra)],
       "data_extracao":datetime.now(timezone.utc).isoformat(),
       "pagina_fonte":pageurl,"metodo":"Soma de três faixas de renda disjuntas apresentadas pelo MDS; ausência municipal não é zero.",
       "proveniencia":provenance,"registros":data}
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps({"municipios_com_dado":len(available),"municipios_sem_dado":result["municipios_sem_dado"],
      "total_pessoas_municipios_disponiveis":sum(x["pessoas"] for x in data.values() if x["pessoas"] is not None)},ensure_ascii=False),flush=True)
if __name__=="__main__":run()
