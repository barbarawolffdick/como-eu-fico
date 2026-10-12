#!/usr/bin/env python3
"""Auditoria de todas as linhas de locais de votação nos painéis HTML (stdlib)."""
import argparse
import csv
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

FIELDS=["uf","municipio","arquivo_html","local_votacao","zona",
        "aptos","votos_validos","votos_lula","votos_flavio",
        "soma_lula_flavio","excesso_votos","regra","detalhe"]

class PanelParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active=False
        self.in_body=False
        self.in_row=False
        self.in_local=False
        self.in_meta=False
        self.row={}
        self.rows=[]
        self.local_parts=[]
        self.meta_parts=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="table" and a.get("data-unidade")=="locais":
            self.active=True
        elif self.active and tag=="tbody": self.in_body=True
        elif self.in_body and tag=="tr":
            self.in_row=True
            self.row={}
        elif self.in_row and tag in ("td","th"):
            label=a.get("data-label")
            if label is not None:
                self.row[label]=a.get("data-v","")
        elif self.in_row and tag=="span" and "local" in a.get("class","").split():
            self.in_local=True
            self.local_parts=[]
        elif self.in_row and tag=="span" and "meta" in a.get("class","").split():
            self.in_meta=True
            self.meta_parts=[]
    def handle_data(self,data):
        if self.in_local:self.local_parts.append(data)
        if self.in_meta:self.meta_parts.append(data)
    def handle_endtag(self,tag):
        if tag=="span":
            if self.in_local:
                self.row["local"]="".join(self.local_parts).strip()
                self.in_local=False
            if self.in_meta:
                self.row["meta"]="".join(self.meta_parts).strip()
                self.in_meta=False
        if tag=="tr" and self.in_row:
            self.rows.append(self.row)
            self.in_row=False
        elif tag=="tbody" and self.in_body: self.in_body=False
        elif tag=="table" and self.active: self.active=False

def num(v):
    s=str(v).strip().replace(".","")
    if not s:return None
    # data-v em HTML armazena floats como 1502.0; aceita somente inteiro.
    try:
        f=float(str(v))
        return int(f) if f.is_integer() and f>=0 else None
    except ValueError:return None

def run(source,output):
    issues=[]
    counts=Counter()
    files=sorted(source.glob("*/municipios_*/*/painel_*.html"))
    for path in files:
        counts["paineis_lidos"]+=1
        panel=PanelParser()
        try:
            panel.feed(path.read_text(encoding="utf-8-sig"))
        except (UnicodeError,ValueError) as exc:
            counts["paineis_com_erro"]+=1
            issues.append({"uf":"","municipio":path.parent.name,"arquivo_html":str(path),
                           "local_votacao":"","zona":"","aptos":"","votos_validos":"",
                           "votos_lula":"","votos_flavio":"","soma_lula_flavio":"",
                           "excesso_votos":"","regra":"erro_leitura","detalhe":str(exc)})
            continue
        uf_match=re.search(r"municipios_([A-Z]{2})",str(path))
        uf=uf_match.group(1) if uf_match else ""
        if not panel.rows:
            counts["paineis_sem_locais"]+=1
            issues.append({"uf":uf,"municipio":path.parent.name,"arquivo_html":str(path),
                           "local_votacao":"","zona":"","aptos":"","votos_validos":"",
                           "votos_lula":"","votos_flavio":"","soma_lula_flavio":"",
                           "excesso_votos":"","regra":"sem_locais","detalhe":"Tabela não encontrada ou vazia"})
        for row in panel.rows:
            counts["locais_lidos"]+=1
            valid=num(row.get("Votos válidos"))
            lula=num(row.get("Lula (votos)"))
            flavio=num(row.get("Flávio (votos)"))
            apt=num(row.get("Eleitores aptos"))
            meta=row.get("meta","")
            zone=re.search(r"Zona\s+(\d+)",meta)
            base={"uf":uf,"municipio":path.parent.name,"arquivo_html":str(path),
                  "local_votacao":row.get("local",""),"zona":zone.group(1) if zone else "",
                  "aptos":apt if apt is not None else "",
                  "votos_validos":valid if valid is not None else "",
                  "votos_lula":lula if lula is not None else "",
                  "votos_flavio":flavio if flavio is not None else "",
                  "soma_lula_flavio":lula+flavio if None not in (lula,flavio) else "",
                  "excesso_votos":lula+flavio-valid if None not in (lula,flavio,valid) else ""}
            def flag(rule,detail):
                issues.append({**base,"regra":rule,"detalhe":detail})
                counts["ocorrencias_"+rule]+=1
            if None in (valid,lula,flavio,apt):
                flag("valores_invalidos","Campo numérico ausente ou inválido")
                continue
            if valid>apt:flag("validos_maiores_aptos",f"{valid} > {apt}")
            if lula>valid:flag("lula_maior_validos",f"{lula} > {valid}")
            if flavio>valid:flag("flavio_maior_validos",f"{flavio} > {valid}")
            if lula+flavio>valid:flag("soma_maior_validos",f"{lula+flavio} > {valid}")
    output.mkdir(parents=True,exist_ok=True)
    with (output/"inconsistencias_locais.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS)
        w.writeheader()
        w.writerows(issues)
    summary={"paineis_lidos":counts["paineis_lidos"],
             "locais_lidos":counts["locais_lidos"],
             "ocorrencias":len(issues),
             "locais_unicos_com_alertas":len(set((r["arquivo_html"],r["local_votacao"]) for r in issues)),
             "municipios_com_alertas":len(set((r["uf"],r["municipio"]) for r in issues)),
             "por_regra":dict(sorted((k.removeprefix("ocorrencias_"),v) for k,v in counts.items() if k.startswith("ocorrencias_"))),
             "paineis_sem_locais":counts["paineis_sem_locais"],
             "paineis_com_erro":counts["paineis_com_erro"],
             "nota":"Consistência interna dos HTMLs. Não verifica fonte TSE ou todos os candidatos."}
    (output/"resumo_locais.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if not files or issues:
        raise SystemExit(1)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("dados-municipios"))
    p.add_argument("--output",type=Path,default=Path("data/quality"))
    a=p.parse_args()
    run(a.source,a.output)
