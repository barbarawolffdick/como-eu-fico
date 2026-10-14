"""Carregamento transacional de TSE e cadastro IBGE no SQLite do aplicativo."""
import argparse
import csv
import json
import hashlib
import sqlite3
from pathlib import Path

def ler(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream)

def campo(linha, nomes, obrigatorio=True):
    for nome in nomes:
        if linha.get(nome) not in ("", None):
            return linha[nome].strip()
    if obrigatorio:
        raise ValueError("Coluna ausente: " + repr(nomes))
    return None

def carregar_populacao(db, csv_path):
    """Carrega somente população IBGE a partir de snapshot municipal validado."""
    validacao = csv_path.parent / "validacao.json"
    if not validacao.is_file():
        raise FileNotFoundError("Validação de população ausente: " + str(validacao))
    meta = json.loads(validacao.read_text(encoding="utf-8"))
    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    if not (meta.get("resultado") == "PASS"
            and meta.get("fonte") == "IBGE SIDRA"
            and meta.get("tabela") == 6579
            and meta.get("variavel") == 9324
            and meta.get("ano_referencia") == 2026
            and meta.get("municipios") == 5571
            and meta.get("sha256_saida") == digest):
        raise ValueError("Snapshot de população IBGE não validado ou hash divergente")
    existentes = {r[0] for r in db.execute("SELECT codigo_ibge FROM municipios")}
    if len(existentes) != 5571:
        raise ValueError("Banco operacional sem 5571 municípios")
    populacoes = {}
    for row in ler(csv_path):
        codigo = campo(row, ("codigo_ibge",))
        valor = campo(row, ("populacao_estimada_2026",))
        if (len(codigo) != 7 or not codigo.isascii() or not codigo.isdigit()
                or codigo in populacoes or not valor.isascii() or not valor.isdigit()
                or int(valor) <= 0):
            raise ValueError("População IBGE inválida/duplicada: " + codigo)
        populacoes[codigo] = int(valor)
    if set(populacoes) != existentes:
        raise ValueError("Cobertura territorial da população não corresponde ao banco")
    db.executemany(
        "UPDATE municipios SET populacao=?,ano_populacao=2026 WHERE codigo_ibge=?",
        [(valor, codigo) for codigo, valor in populacoes.items()]
    )
    db.execute("INSERT OR REPLACE INTO origem_dados(dominio,arquivo,nota) VALUES(?,?,?)",
               ("populacao_ibge", meta.get("url", str(csv_path)),
                "Estimativa municipal IBGE SIDRA 6579/9324; 1º de julho de 2026; "
                "SHA-256 do CSV: " + digest))
    return len(populacoes)


def importar(db_path, tse_dir=None, ibge_csv=None, populacao_csv=None):
    if not db_path.is_file():
        raise FileNotFoundError(db_path)
    if not tse_dir and not ibge_csv and not populacao_csv:
        raise ValueError("Informe TSE e/ou IBGE")
    with sqlite3.connect(db_path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")
        result = {}
        if ibge_csv:
            codes = set()
            for row in ler(ibge_csv):
                code = campo(row, ("codigo_ibge","codigo","cod_ibge"))
                name = campo(row, ("nome","nome_municipio","municipio"))
                uf = campo(row, ("uf","sigla_uf"))
                population = campo(row, ("populacao","população"), False)
                year = campo(row, ("ano_populacao","ano"), False)
                if len(code)!=7 or not code.isascii() or not code.isdigit() or len(uf)!=2 or code in codes:
                    raise ValueError("IBGE duplicado/inválido: "+code)
                if (population is None)!=(year is None):
                    raise ValueError("População sem ano de referência: "+code)
                if population is not None and (int(population)<0 or int(year)<1900):
                    raise ValueError("População/ano inválidos: "+code)
                updated = db.execute(
                    "UPDATE municipios SET nome=?,uf=?,populacao=?,ano_populacao=? WHERE codigo_ibge=?",
                    (name,uf,int(population) if population else None,int(year) if year else None,code))
                if updated.rowcount!=1:
                    raise ValueError("IBGE ausente no banco CGU: "+code)
                codes.add(code)
            if not codes:
                raise ValueError("IBGE vazio")
            db.execute("INSERT OR REPLACE INTO origem_dados VALUES(?,?,?)",
                       ("territorio",str(ibge_csv),"Cadastro IBGE; população e ano quando disponíveis"))
            result["ibge_municipios"]=len(codes)
        if populacao_csv:
            result["populacao_municipios"] = carregar_populacao(db, populacao_csv)
        if tse_dir:
            for name in ("municipios.csv","candidatos_municipios.csv","validacao.json"):
                if not (tse_dir/name).is_file():
                    raise FileNotFoundError(tse_dir/name)
            quality=json.loads((tse_dir/"validacao.json").read_text(encoding="utf-8"))
            for key in ("resultados_municipais","consistencia_eleitoral","correspondencia"):
                if quality.get(key)!="PASS":
                    raise ValueError("TSE não validado: "+key)
            totals={}
            for row in ler(tse_dir/"municipios.csv"):
                code=campo(row,("codigo_ibge",))
                if len(code)!=7 or not code.isascii() or not code.isdigit() or code in totals:
                    raise ValueError("Município TSE inválido: "+code)
                totals[code]=int(campo(row,("votos_validos",)))
                if totals[code]<0:
                    raise ValueError("Votos negativos")
            if len(totals)!=5571:
                raise ValueError("TSE incompleto: "+str(len(totals)))
            db.execute("DELETE FROM votos_presidenciais WHERE eleicao=2026 AND turno=1")
            calculated={}
            for row in ler(tse_dir/"candidatos_municipios.csv"):
                code=campo(row,("codigo_ibge",))
                candidate=campo(row,("numero_candidato","numero","nr_votavel","sq_candidato","nome_urna","nome_candidato"))
                votes=int(campo(row,("votos",)))
                if code not in totals or votes<0:
                    raise ValueError("Voto inválido: "+code)
                db.execute("INSERT INTO votos_presidenciais(codigo_ibge,eleicao,turno,candidato,votos,detalhes_json) VALUES (?,?,?,?,?,?)",
                           (code,2026,1,candidate,votes,json.dumps(row,ensure_ascii=False)))
                calculated[code]=calculated.get(code,0)+votes
            if calculated!=totals:
                raise ValueError("Votos TSE não reconciliados")
            db.execute("INSERT OR REPLACE INTO origem_dados VALUES(?,?,?)",
                       ("eleitoral",str(tse_dir),"TSE 2026, primeiro turno; snapshot validado"))
            result["tse_municipios"]=len(totals)
        if db.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("Chave estrangeira inválida")
        db.commit()
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--db",type=Path,required=True)
    parser.add_argument("--tse",type=Path)
    parser.add_argument("--ibge",type=Path)
    parser.add_argument("--populacao",type=Path,help="CSV validado de população IBGE 2026; não modifica nomes/UF")
    args=parser.parse_args()
    print(json.dumps(importar(args.db,args.tse,args.ibge,args.populacao),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
