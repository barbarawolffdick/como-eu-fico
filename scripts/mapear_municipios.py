#!/usr/bin/env python3
"""Mapeia municípios dos resumos eleitorais para códigos IBGE sem alterar originais."""
import argparse
import csv
import gzip
import json
import re
import unicodedata
import urllib.request
from collections import Counter
from pathlib import Path

IBGE_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
UF_NAMES = {
    "Acre":"AC","Alagoas":"AL","Amapa":"AP","Amazonas":"AM","Bahia":"BA",
    "Ceara":"CE","Distrito_Federal":"DF","Espirito_Santo":"ES","Goias":"GO",
    "Maranhao":"MA","Mato_Grosso":"MT","Mato_Grosso_do_Sul":"MS",
    "Minas_Gerais":"MG","Para":"PA","Paraiba":"PB","Parana":"PR",
    "Pernambuco":"PE","Piaui":"PI","Rio_Grande_do_Norte":"RN",
    "Rio_Grande_do_Sul":"RS","Rio_de_Janeiro":"RJ","Rondonia":"RO",
    "Roraima":"RR","Santa_Catarina":"SC","Sao_Paulo":"SP",
    "Sergipe":"SE","Tocantins":"TO"
}

# Equivalências revisadas explicitamente (UF, nome na base eleitoral) -> código IBGE.
# Não utilizar fuzzy matching: qualquer nome novo permanece pendente.
ALIASES_IBGE = {
    ("GO", "BOM JESUS"): "5203500",
    ("MT", "SANTO ANTÔNIO DO LEVERGER"): "5107800",
    ("MG", "BARÃO DE MONTE ALTO"): "3105509",
    ("MG", "DONA EUSÉBIA"): "3122900",
    ("MG", "SÃO THOMÉ DAS LETRAS"): "3165206",
    ("PA", "ELDORADO DOS CARAJÁS"): "1502954",
    ("PR", "MUNHOZ DE MELLO"): "4116307",
    ("RN", "BOA SAÚDE"): "2405306",
    ("RO", "ALVORADA DO OESTE"): "1100346",
    ("RO", "ESPIGÃO DO OESTE"): "1100098",
    ("RR", "SÃO LUIZ"): "1400605",
    ("SP", "SÃO LUÍS DO PARAITINGA"): "3550001",
    ("SE", "AMPARO DE SÃO FRANCISCO"): "2800100",
}

def norm(s):
    s = unicodedata.normalize("NFKD", str(s).strip())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Z0-9]+", " ", s.upper())
    return " ".join(s.split())

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))

def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def ibge_records(cache, refresh=False):
    if refresh or not cache.exists():
        req = urllib.request.Request(IBGE_URL, headers={"User-Agent":"como-eu-fico/1.0"})
        with urllib.request.urlopen(req, timeout=60) as response:
            payload = response.read()
        if payload.startswith(b"\x1f\x8b"):
            payload = gzip.decompress(payload)
        records = json.loads(payload.decode("utf-8-sig"))
        if not isinstance(records, list) or len(records) < 5500:
            raise ValueError("Resposta IBGE incompleta; cache não atualizado")
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(records, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return json.loads(cache.read_text(encoding="utf-8"))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=Path("dados-municipios"))
    p.add_argument("--output", type=Path, default=Path("data"))
    p.add_argument("--refresh-ibge", action="store_true")
    a = p.parse_args()
    cache = a.output / "reference" / "ibge_municipios_raw.json"
    official = ibge_records(cache, a.refresh_ibge)
    index = {}
    ref = []
    for r in official:
        # A API pode retornar microrregiao nula; usa a divisao regional atual.
        uf_info = None
        micro = r.get("microrregiao")
        if micro and micro.get("mesorregiao"):
            uf_info = micro["mesorregiao"].get("UF")
        imediata = r.get("regiao-imediata")
        if not uf_info and imediata and imediata.get("regiao-intermediaria"):
            uf_info = imediata["regiao-intermediaria"].get("UF")
        if not uf_info or not uf_info.get("sigla"):
            raise ValueError(f"UF ausente nas hierarquias IBGE: {r.get('id')} - {r.get('nome')}")
        uf = uf_info["sigla"]
        row = {"codigo_ibge":str(r["id"]), "uf":uf, "municipio_ibge":r["nome"]}
        ref.append(row)
        key = (uf, norm(r["nome"]))
        if key in index:
            raise ValueError("Código municipal ambíguo no IBGE: "+str(key))
        index[key] = row
    ref.sort(key=lambda r:(r["uf"], r["municipio_ibge"]))
    write_csv(a.output/"reference"/"municipios_ibge.csv", ref, ["codigo_ibge","uf","municipio_ibge"])

    codes = {r["codigo_ibge"]: r for r in ref}
    aliases = {(uf, norm(name)): code for (uf, name), code in ALIASES_IBGE.items()}
    matched, unresolved, seen = [], [], set()
    files = sorted(a.source.glob("*/resumo_municipios_*.csv"))
    for path in files:
        folder_uf = UF_NAMES.get(path.parent.name)
        for row_number, r in enumerate(read_csv(path), 2):
            uf = (r.get("UF") or "").strip().upper()
            name = (r.get("MUNICIPIO") or "").strip()
            key = (uf, norm(name))
            base = {"arquivo_origem":str(path), "linha_origem":row_number, "uf":uf,"municipio_origem":name}
            if not folder_uf or uf != folder_uf:
                unresolved.append({**base,"motivo":"UF não corresponde à pasta"})
                continue
            if key in seen:
                unresolved.append({**base,"motivo":"Município duplicado nos resumos"})
                continue
            seen.add(key)
            reference = index.get(key)
            method = "nome_exato_normalizado"
            if reference is None and key in aliases:
                code = aliases[key]
                reference = codes.get(code)
                method = "equivalencia_revisada"
                if reference is None or reference["uf"] != uf:
                    raise ValueError(f"Alias IBGE inválido: {key} -> {code}")
            if reference is None:
                unresolved.append({**base,"motivo":"Sem correspondência IBGE; requer revisão"})
                continue
            matched.append({**base,**reference,"metodo_correspondencia":method})
    write_csv(a.output/"reference"/"municipios_mapeados.csv", matched,
              ["codigo_ibge","uf","municipio_ibge","municipio_origem","arquivo_origem","linha_origem","metodo_correspondencia"])
    write_csv(a.output/"quality"/"municipios_nao_correspondidos.csv", unresolved,
              ["arquivo_origem","linha_origem","uf","municipio_origem","motivo"])
    matched_codes = {r["codigo_ibge"] for r in matched}
    missing = [r for r in ref if r["codigo_ibge"] not in matched_codes]
    write_csv(a.output/"quality"/"municipios_ibge_ausentes.csv", missing,
              ["codigo_ibge","uf","municipio_ibge"])
    report = {
        "fonte_ibge":IBGE_URL, "arquivos_csv_lidos":len(files),
        "registros_ibge":len(ref), "municipios_mapeados":len(matched),
        "registros_pendentes":len(unresolved), "municipios_ibge_ausentes":len(missing),
        "equivalencias_revisadas":sum(r["metodo_correspondencia"]=="equivalencia_revisada" for r in matched),
        "motivos_pendencia":dict(Counter(r["motivo"] for r in unresolved)),
        "observacao":"Nome normalizado ou equivalência explícita por código IBGE, sem matching aproximado."
    }
    (a.output/"quality"/"resumo_mapeamento.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not files or unresolved or missing or len(matched_codes) != len(matched):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
