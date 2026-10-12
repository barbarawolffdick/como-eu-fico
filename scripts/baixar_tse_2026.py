#!/usr/bin/env python3
"""Descobre e baixa recursos oficiais do conjunto Resultados 2026 do TSE (CKAN)."""
import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://dadosabertos.tse.jus.br/api/3/action/package_show?id=resultados-2026"
PAGE = "https://dadosabertos.tse.jus.br/dataset/resultados-2026"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent":"ComoEuFico-auditoria/1.0", "Accept-Encoding":"identity"})
    with urllib.request.urlopen(req, timeout=120) as response:
        data=response.read()
        encoding=response.headers.get("Content-Encoding","").lower()
    if encoding=="gzip" or data.startswith(b"\x1f\x8b"):
        import gzip
        data=gzip.decompress(data)
    return data

def discover():
    payload=json.loads(fetch(API).decode("utf-8-sig"))
    if not payload.get("success"):
        raise RuntimeError("CKAN não confirmou sucesso")
    resources=payload["result"].get("resources",[])
    found=[]
    for r in resources:
        name=r.get("name","")
        normalized=name.casefold()
        if ("presidente" in normalized and "votação por seção" in normalized) or "detalhe da apuração" in normalized:
            url=r.get("url","")
            if not url.startswith("https://"):
                continue
            found.append({"id":r.get("id"),"name":name,"url":url,
                          "format":r.get("format"),"last_modified":r.get("last_modified"),
                          "created":r.get("created"),"size_catalog":r.get("size"),
                          "description":r.get("description","")[:300]})
    if not found:raise RuntimeError("Nenhum recurso correspondente encontrado. Inspecionar catálogo manualmente.")
    return found

def download(item, directory):
    name=urllib.parse.urlparse(item["url"]).path.split("/")[-1] or "tse-resource"
    name=re.sub(r"[^A-Za-z0-9_.-]","_",name)
    if "." not in name:name += ".dat"
    path=directory/name
    req=urllib.request.Request(item["url"],headers={"User-Agent":"ComoEuFico-auditoria/1.0", "Accept-Encoding":"identity"})
    digest=hashlib.sha256()
    size=0
    with urllib.request.urlopen(req,timeout=120) as response, path.open("wb") as out:
        while True:
            block=response.read(1024*1024)
            if not block:break
            out.write(block)
            digest.update(block)
            size+=len(block)
    return {"file":str(path),"bytes":size,"sha256":digest.hexdigest()}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--download",action="store_true",help="Baixa recursos; por padrão só registra manifesto")
    p.add_argument("--output",type=Path,default=Path("data/raw/tse/2026"))
    a=p.parse_args()
    resources=discover()
    a.output.mkdir(parents=True,exist_ok=True)
    manifest={"catalogue":PAGE,"api":API,
              "retrieved_at_utc":datetime.now(timezone.utc).isoformat(),
              "resources":resources}
    if a.download:
        for item in resources:
            item["download"]=download(item,a.output)
    dest=a.output/"manifest.json"
    dest.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"manifest":str(dest),"resources":[{"name":r["name"],"url":r["url"],"download":r.get("download")} for r in resources]},ensure_ascii=False,indent=2))

if __name__=="__main__":main()
