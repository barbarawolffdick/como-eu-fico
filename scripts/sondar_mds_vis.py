"""Sonda reprodutível do endpoint público VIS DATA, sem aceitar retorno parcial."""
import argparse
import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser

BASE="https://aplicacoes.cidadania.gov.br/vis/tabelas/tabela.php"
class Table(HTMLParser):
 def __init__(self):
  super().__init__();self.rows=[];self.row=None;self.cell=None
 def handle_starttag(self,tag,attrs):
  if tag=="tr":self.row=[]
  if tag in ("td","th") and self.row is not None:self.cell=[]
 def handle_data(self,data):
  if self.cell is not None:self.cell.append(data)
 def handle_endtag(self,tag):
  if tag in ("td","th") and self.cell is not None:
   self.row.append(" ".join(" ".join(self.cell).split()));self.cell=None
  if tag=="tr" and self.row is not None:
   if self.row:self.rows.append(self.row)
   self.row=None

def get(period="2026-08-01",page=1,registros=100):
 params={"cfc":f"prog=1$banco=Producao$referencia={period}|$vars=bf_qtd_fam",
         "exibe_num":"1","exibir_codigo_divisao":"1","iuid":"78273",
         "pagina":str(page),"paginacao":"1","registros":str(registros),"tipo_divisao":"m"}
 url=BASE+"?"+urllib.parse.urlencode(params)
 req=urllib.request.Request(url,headers={"User-Agent":"ComoEuFico/1.0","Accept":"text/html"})
 with urllib.request.urlopen(req,timeout=90) as response:
  body=response.read()
 parser=Table();parser.feed(body.decode("utf-8",errors="replace"))
 return {"url":url,"bytes":len(body),"linhas":len(parser.rows),
         "amostra":parser.rows[:8],"codigos_encontrados":len({x for row in parser.rows for x in row if re.fullmatch(r"\\d{6,7}",x)})}

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--periodo",default="2026-08-01");p.add_argument("--registros",type=int,default=100);a=p.parse_args()
 print(json.dumps(get(a.periodo,registros=a.registros),ensure_ascii=False,indent=2))
