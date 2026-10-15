"""Testes HTTP do Next.js para cobertura com o snapshot MDS+IBGE publicado."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = os.environ.get("COMO_EU_FICO_TEST_URL", "http://127.0.0.1:3000").rstrip("/")
SNAPSHOT = json.loads(Path("data/public/pessoas_mds.json").read_text(encoding="utf-8"))
RANKS = json.loads(Path("data/public/rankings_2026.json").read_text(encoding="utf-8"))

def get(path, params=None, expected=200):
    uri = BASE+path
    if params: uri += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(uri, timeout=15) as res:
            status, body = res.status, json.load(res)
    except urllib.error.HTTPError as ex:
        status, body = ex.code, json.load(ex)
    assert status == expected, (uri, status, body)
    return body

assert len(SNAPSHOT["registros"]) == 5571
assert SNAPSHOT["periodo"] == "202608"
assert SNAPSHOT["unidade"] == "pessoas_em_familias_beneficiarias"

sp = get("/api/cobertura", {"municipio":"3550308"})
assert sp["periodo"] == SNAPSHOT["periodo"] and sp["disponivel"] is True, sp
item = sp["municipio"]
expected = SNAPSHOT["registros"]["3550308"]
assert item["pessoas"] == expected["pessoas"], (item, expected)
assert abs(item["cobertura_pct"] - 100*item["pessoas"]/item["populacao"]) <= .000051
assert "titulares" in sp["descricao"]

missing = SNAPSHOT["municipios_sem_dado"][0]
unavailable = get("/api/cobertura", {"municipio":missing})
assert unavailable["disponivel"] is False and unavailable["municipio"]["cobertura_pct"] is None

all_br = get("/api/cobertura", {"limite":"100"})
assert all_br["municipios_com_dado"] == SNAPSHOT["municipios_com_dado"]
assert len(all_br["resultados"]) == 100
assert all(row["cobertura_pct"] is not None for row in all_br["resultados"])
assert all(a["cobertura_pct"] >= b["cobertura_pct"] for a,b in zip(all_br["resultados"],all_br["resultados"][1:]))

by_uf = get("/api/cobertura", {"uf":"SP"})
assert by_uf["resultados"] and all(row["uf"] == "SP" for row in by_uf["resultados"])

for candidato in ("13","22","outros"):
    res = get("/api/cobertura", {"vencedor":candidato})
    assert len(res["resultados"]) <= 10
    assert all((row["vencedor"]==candidato if candidato!="outros" else row["vencedor"] not in ("13","22")) for row in res["resultados"])

for params in ({"municipio":"123"},{"uf":"ZZZ"},{"vencedor":"999"},{"limite":"101"},{"limite":"2.5"}):
    get("/api/cobertura", params, 422)
get("/api/cobertura", {"municipio":"9999999"}, 404)

print(json.dumps({"resultado":"PASS","municipios_com_cobertura":SNAPSHOT["municipios_com_dado"],"periodo":SNAPSHOT["periodo"],"rotas_verificadas":["individual","ausente","ranking","UF","vencedor","erros"]},ensure_ascii=False))
