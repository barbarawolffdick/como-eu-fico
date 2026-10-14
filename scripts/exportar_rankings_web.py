"""Exporta indicadores municipais para frontend Next.js sem depender de FastAPI hospedado."""
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATABASE = ROOT / "data/app/como_eu_fico.sqlite"
DESTINATION = ROOT / "data/public/rankings_2026.json"
DETAILS = ROOT / "data/public/detalhes_2026.json"

QUERY = """
WITH bf AS (
 SELECT codigo_ibge, SUM(valor_centavos) valor_centavos,
        SUM(parcelas) parcelas, COUNT(*) competencias
 FROM bolsa_familia_mensal
 WHERE mes_competencia BETWEEN '202601' AND '202608'
 GROUP BY codigo_ibge
), ordenados AS (
 SELECT codigo_ibge,candidato,votos,
        SUM(votos) OVER (PARTITION BY codigo_ibge) votos_total,
        RANK() OVER (PARTITION BY codigo_ibge ORDER BY votos DESC) posicao
 FROM votos_presidenciais WHERE eleicao=2026 AND turno=1
), vencedores AS (
 SELECT codigo_ibge, MAX(CASE WHEN posicao=1 THEN candidato END) vencedor,
        MAX(CASE WHEN posicao=1 THEN votos END) votos_vencedor,
        MAX(votos_total) votos_total,
        SUM(CASE WHEN posicao=1 THEN 1 ELSE 0 END) empatados
 FROM ordenados GROUP BY codigo_ibge
)
SELECT m.codigo_ibge,m.nome,m.uf,m.populacao,m.ano_populacao,
       bf.valor_centavos,bf.parcelas,bf.competencias,
       v.vencedor,v.votos_vencedor,v.votos_total,v.empatados
FROM municipios m LEFT JOIN bf USING(codigo_ibge)
LEFT JOIN vencedores v USING(codigo_ibge)
ORDER BY m.codigo_ibge
"""

def run(database=DATABASE, destination=DESTINATION):
    with sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True) as cx:
        cx.row_factory = sqlite3.Row
        rows = [dict(row) for row in cx.execute(QUERY)]
        count = cx.execute("SELECT COUNT(*) FROM municipios").fetchone()[0]
        sources = [dict(row) for row in cx.execute("SELECT * FROM origem_dados ORDER BY dominio")]
    if count != 5571 or len(rows) != 5571 or len({r["codigo_ibge"] for r in rows}) != 5571:
        raise ValueError("Cobertura territorial inválida")
    populacao_completa = all(r["populacao"] is not None and r["populacao"] > 0 for r in rows)
    if any(r["valor_centavos"] is None or r["vencedor"] is None for r in rows):
        raise ValueError("Dados eleitorais ou do Bolsa Família incompletos")
    if any(r["competencias"] != 8 for r in rows):
        raise ValueError("Cobertura de competências janeiro-agosto 2026 incompleta")
    data = {"populacao_completa": populacao_completa, "esquema": 1, "inicio": "202601", "fim": "202608",
            "eleicao": 2026, "turno": 1, "municipios": count,
            "origem_dados": sources, "registros": rows}
    destination.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(data,ensure_ascii=False,separators=(",",":"))+"\n").encode("utf-8")
    destination.write_bytes(raw)
    print(json.dumps({"arquivo":str(destination),"municipios":count,"sha256":hashlib.sha256(raw).hexdigest()},ensure_ascii=False))

    with sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True) as cx:
        cx.row_factory = sqlite3.Row
        votos = {}
        for item in cx.execute("SELECT codigo_ibge,candidato,votos FROM votos_presidenciais WHERE eleicao=2026 AND turno=1 ORDER BY votos DESC"):
            votos.setdefault(item["codigo_ibge"], []).append({"candidato": item["candidato"], "votos": item["votos"]})
        bolsa = {}
        for item in cx.execute("SELECT codigo_ibge,mes_competencia,parcelas,valor_centavos FROM bolsa_familia_mensal ORDER BY mes_competencia"):
            bolsa.setdefault(item["codigo_ibge"], []).append({"mes_competencia": item["mes_competencia"], "parcelas": item["parcelas"], "valor_centavos": item["valor_centavos"]})
    detalhes = {
        item["codigo_ibge"]: {
            "municipio": {key:item[key] for key in ("codigo_ibge","nome","uf","populacao","ano_populacao")},
            "votos_presidenciais": votos.get(item["codigo_ibge"], []),
            "bolsa_familia": bolsa.get(item["codigo_ibge"], []),
            "eleitoral_disponivel": bool(votos.get(item["codigo_ibge"]))
        } for item in rows
    }
    detail_bytes = (json.dumps({"esquema":1,"municipios":count,"registros":detalhes},ensure_ascii=False,separators=(",",":"))+"\\n").encode("utf-8")
    DETAILS.write_bytes(detail_bytes)
    print(json.dumps({"detalhes":str(DETAILS),"sha256_detalhes":hashlib.sha256(detail_bytes).hexdigest()},ensure_ascii=False))

if __name__ == "__main__":
    run()
