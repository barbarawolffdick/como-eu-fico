"""Atualiza os nomes dos municípios pelo cadastro oficial do IBGE.

Não altera votos nem Bolsa Família; preserva as fontes originais.
"""
import argparse
import json
import sqlite3
import urllib.request
from pathlib import Path

URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

def uf_do_municipio(item):
    # Hierarquia de localidades do IBGE (região imediata ou microrregião).
    imediato = item.get("regiao-imediata")
    if imediato:
        return imediato["regiao-intermediaria"]["UF"]["sigla"]
    micro = item.get("microrregiao")
    if micro:
        return micro["mesorregiao"]["UF"]["sigla"]
    raise ValueError("UF não informada pelo IBGE: " + str(item.get("id")))

def carregar_nomes(db_path, dados, origem=URL):
    municipios = {}
    for item in dados:
        codigo = str(item["id"])
        nome = item["nome"].strip()
        uf = uf_do_municipio(item)
        if len(codigo) != 7 or not codigo.isdigit() or not nome or len(uf) != 2 or codigo in municipios:
            raise ValueError("Cadastro IBGE contém município inválido ou duplicado: " + codigo)
        municipios[codigo] = (nome, uf)
    if len(municipios) < 5500:
        raise ValueError("Cadastro IBGE incompleto: " + str(len(municipios)))
    with sqlite3.connect(db_path) as db:
        db.execute("BEGIN IMMEDIATE")
        presentes = {codigo: uf for codigo, uf in db.execute("SELECT codigo_ibge,uf FROM municipios")}
        if len(presentes) < 5500:
            raise ValueError("Banco operacional incompleto")
        correspondentes = presentes.keys() & municipios.keys()
        if len(correspondentes) < 5500:
            raise ValueError("Correspondência territorial insuficiente: " + str(len(correspondentes)))
        inconsistentes = [codigo for codigo in correspondentes if presentes[codigo] and presentes[codigo] != municipios[codigo][1]]
        if inconsistentes:
            raise ValueError("UF divergente entre TSE e IBGE: " + ", ".join(inconsistentes[:5]))
        db.executemany("UPDATE municipios SET nome=?,uf=? WHERE codigo_ibge=?",
                       [(municipios[codigo][0],municipios[codigo][1],codigo) for codigo in correspondentes])
        db.execute("INSERT OR REPLACE INTO origem_dados(dominio,arquivo,nota) VALUES (?,?,?)",
                   ("nomes_municipais_ibge",origem,"IBGE Localidades: nome e UF oficiais. População não incluída."))
        faltantes = sorted(presentes.keys() - municipios.keys())
        sobras = sorted(municipios.keys() - presentes.keys())
        db.commit()
    return {"nomes_atualizados":len(correspondentes),"sem_correspondencia_no_ibge":faltantes,"somente_no_ibge":sobras,
            "fonte":origem}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",type=Path,default=Path("data/app/como_eu_fico.sqlite"))
    p.add_argument("--json",type=Path,help="Arquivo JSON oficial baixado anteriormente, para execução offline")
    a=p.parse_args()
    if not a.db.is_file():
        p.error("Banco não encontrado: "+str(a.db))
    if a.json:
        dados=json.loads(a.json.read_text(encoding="utf-8"))
        origem=str(a.json)
    else:
        with urllib.request.urlopen(urllib.request.Request(URL,headers={"User-Agent":"ComoEuFico/1.0"}),timeout=45) as response:
            dados=json.load(response)
        origem=URL
    print(json.dumps(carregar_nomes(a.db,dados,origem),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
