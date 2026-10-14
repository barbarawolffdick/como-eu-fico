"""Banco operacional SQLite do Como Eu Fico.

Carrega apenas agregados municipais. Bases TSE/CGU originais não são modificadas.
"""
import argparse
import csv
import json
import sqlite3
from pathlib import Path

DDL = """
PRAGMA foreign_keys=ON;
CREATE TABLE municipios (
  codigo_ibge TEXT PRIMARY KEY CHECK(length(codigo_ibge)=7),
  nome TEXT, uf TEXT, populacao INTEGER, ano_populacao INTEGER
);
CREATE TABLE votos_presidenciais (
  codigo_ibge TEXT NOT NULL REFERENCES municipios(codigo_ibge),
  eleicao INTEGER NOT NULL DEFAULT 2026,
  turno INTEGER NOT NULL DEFAULT 1,
  candidato TEXT NOT NULL,
  votos INTEGER NOT NULL CHECK(votos>=0),
  detalhes_json TEXT NOT NULL,
  PRIMARY KEY(codigo_ibge, eleicao, turno, candidato)
);
CREATE TABLE bolsa_familia (
  codigo_ibge TEXT NOT NULL REFERENCES municipios(codigo_ibge),
  mes_competencia TEXT NOT NULL CHECK(length(mes_competencia)=6),
  mes_referencia TEXT NOT NULL CHECK(length(mes_referencia)=6),
  parcelas INTEGER NOT NULL CHECK(parcelas>=0),
  valor_centavos INTEGER NOT NULL,
  PRIMARY KEY(codigo_ibge, mes_competencia, mes_referencia)
);
CREATE INDEX idx_bolsa_competencia ON bolsa_familia(mes_competencia, codigo_ibge);
CREATE VIEW bolsa_familia_mensal AS
 SELECT codigo_ibge, mes_competencia, SUM(parcelas) parcelas,
        SUM(valor_centavos) valor_centavos
 FROM bolsa_familia GROUP BY codigo_ibge, mes_competencia;
CREATE TABLE origem_dados (dominio TEXT PRIMARY KEY, arquivo TEXT NOT NULL, nota TEXT);
"""

def linhas_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        yield from csv.DictReader(file)

def nome_candidato(row):
    for field in ("numero_candidato", "numero", "nr_votavel", "sq_candidato", "nome_urna", "nome_candidato"):
        if row.get(field):
            return str(row[field]).strip()
    raise ValueError("Snapshot TSE sem identificador de candidato")

def criar_banco(tse_dir, bolsa_db, saida):
    """Cria um banco novo; falha se faltar fonte ou destino já existir."""
    for filename in ("municipios.csv", "candidatos_municipios.csv", "validacao.json"):
        if not (tse_dir / filename).is_file():
            raise FileNotFoundError(tse_dir / filename)
    if not bolsa_db.is_file():
        raise FileNotFoundError(bolsa_db)
    if saida.exists():
        raise FileExistsError(saida)
    status = json.loads((tse_dir / "validacao.json").read_text(encoding="utf-8"))
    for key in ("resultados_municipais", "consistencia_eleitoral", "correspondencia"):
        if status.get(key) != "PASS":
            raise ValueError("Snapshot eleitoral não validado: " + key)
    saida.parent.mkdir(parents=True, exist_ok=True)
    temp = saida.with_suffix(saida.suffix + ".part")
    try:
        with sqlite3.connect(temp) as app, sqlite3.connect(
            bolsa_db.resolve().as_uri() + "?mode=ro", uri=True
        ) as beneficios:
            app.executescript(DDL)
            expected = {}
            for row in linhas_csv(tse_dir / "municipios.csv"):
                code = row["codigo_ibge"]
                if len(code) != 7 or not code.isascii() or not code.isdigit():
                    raise ValueError("IBGE inválido no TSE: " + repr(code))
                validos = int(row["votos_validos"])
                if validos < 0 or code in expected:
                    raise ValueError("Votos ou município inválidos: " + code)
                expected[code] = validos
                app.execute(
                    "INSERT INTO municipios(codigo_ibge,nome,uf) VALUES (?,?,?)",
                    (code, row.get("municipio") or row.get("nome_municipio"),
                     row.get("uf") or row.get("sigla_uf")),
                )
            votes = {}
            for row in linhas_csv(tse_dir / "candidatos_municipios.csv"):
                code = row["codigo_ibge"]
                votos = int(row["votos"])
                if code not in expected or votos < 0:
                    raise ValueError("Voto eleitoral inválido: " + code)
                candidate = nome_candidato(row)
                app.execute(
                    "INSERT INTO votos_presidenciais(codigo_ibge,candidato,votos,detalhes_json) VALUES (?,?,?,?)",
                    (code, candidate, votos, json.dumps(row, ensure_ascii=False)),
                )
                votes[code] = votes.get(code, 0) + votos
            if votes != expected:
                raise ValueError("Totais de votos não conciliados")
            if beneficios.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("SQLite CGU inválido")
            month_totals = {}
            for mes, ref, code, cents, count in beneficios.execute(
                "SELECT mes_competencia, mes_referencia, codigo_ibge, valor_centavos, "
                "quantidade_parcelas FROM parcelas_municipais"
            ):
                if code not in expected:
                    raise ValueError("Município CGU ausente no TSE: " + code)
                if count < 0:
                    raise ValueError("Quantidade de parcelas negativa")
                app.execute("INSERT INTO bolsa_familia VALUES (?,?,?,?,?)",
                            (code, mes, ref, count, cents))
                old = month_totals.get(mes, (0, 0))
                month_totals[mes] = (old[0] + count, old[1] + cents)
            source_totals = dict(
                (m, (n, v)) for m, n, v in beneficios.execute(
                    "SELECT mes_competencia, parcelas, valor_centavos FROM origem"
                )
            )
            if not source_totals or month_totals != source_totals:
                raise ValueError("Totais CGU não conciliados")
            app.executemany("INSERT INTO origem_dados VALUES (?,?,?)", [
                ("eleitoral", str(tse_dir), "TSE 2026, primeiro turno; snapshot validado"),
                ("bolsa_familia", str(bolsa_db), "CGU: parcelas e valores por competência/referência"),
            ])
            if app.execute("PRAGMA foreign_key_check").fetchone():
                raise ValueError("Falha de chave estrangeira")
            app.commit()
            result = {"municipios": len(expected), "competencias": len(source_totals),
                      "parcelas": sum(x[0] for x in source_totals.values()),
                      "valor_centavos": sum(x[1] for x in source_totals.values())}
        temp.replace(saida)
        return result
    finally:
        temp.unlink(missing_ok=True)


def criar_banco_bolsa(bolsa_db, saida):
    """Cria o banco operacional com CGU real; votos/IBGE são carregados depois."""
    if not bolsa_db.is_file():
        raise FileNotFoundError(bolsa_db)
    if saida.exists():
        raise FileExistsError(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    temp = saida.with_suffix(saida.suffix + ".part")
    try:
        with sqlite3.connect(bolsa_db.resolve().as_uri() + "?mode=ro", uri=True) as cgu, sqlite3.connect(temp) as app:
            if cgu.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Banco CGU inválido")
            app.executescript(DDL)
            app.executemany("INSERT INTO municipios(codigo_ibge) VALUES (?)",
                            cgu.execute("SELECT DISTINCT codigo_ibge FROM parcelas_municipais ORDER BY codigo_ibge"))
            app.executemany("INSERT INTO bolsa_familia VALUES (?,?,?,?,?)",
                            cgu.execute("SELECT codigo_ibge,mes_competencia,mes_referencia,quantidade_parcelas,valor_centavos FROM parcelas_municipais"))
            expected = dict((m,(q,v)) for m,q,v in cgu.execute(
                "SELECT mes_competencia,parcelas,valor_centavos FROM origem"))
            found = dict((m,(q,v)) for m,q,v in app.execute(
                "SELECT mes_competencia,SUM(parcelas),SUM(valor_centavos) FROM bolsa_familia GROUP BY mes_competencia"))
            if not expected or found != expected:
                raise ValueError("Totais CGU divergentes")
            if app.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Chave estrangeira inválida")
            app.execute("INSERT INTO origem_dados VALUES(?,?,?)",
                        ("bolsa_familia",str(bolsa_db),"CGU: dados reais por competência e referência"))
            app.commit()
            result = {"municipios":app.execute("SELECT COUNT(*) FROM municipios").fetchone()[0],
                      "competencias":len(expected),
                      "parcelas":sum(x[0] for x in expected.values()),
                      "valor_centavos":sum(x[1] for x in expected.values())}
        temp.replace(saida)
        return result
    finally:
        temp.unlink(missing_ok=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tse", type=Path, default=Path("data/curated/eleicoes_2026_t1"))
    p.add_argument("--bolsa", type=Path, required=True)
    p.add_argument("--saida", type=Path, default=Path("data/app/como_eu_fico.sqlite"))
    a = p.parse_args()
    result = criar_banco(a.tse, a.bolsa, a.saida) if (a.tse / "municipios.csv").is_file() else criar_banco_bolsa(a.bolsa, a.saida)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
