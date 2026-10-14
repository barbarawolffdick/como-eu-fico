import csv
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from app.integrar_fontes import importar

class IntegrarFontesTest(unittest.TestCase):
    def test_ibge_atualiza_e_rejeita_populacao_sem_ano(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); banco=root/"app.sqlite"; ibge=root/"ibge.csv"
            with sqlite3.connect(banco) as cx:
                cx.executescript("""
                CREATE TABLE municipios(codigo_ibge TEXT PRIMARY KEY,nome TEXT,uf TEXT,populacao INTEGER,ano_populacao INTEGER);
                CREATE TABLE origem_dados(dominio TEXT PRIMARY KEY,arquivo TEXT,nota TEXT);
                INSERT INTO municipios(codigo_ibge) VALUES ('3550308');
                """)
            ibge.write_text("codigo_ibge,nome,uf,populacao,ano_populacao\n3550308,São Paulo,SP,11000000,2022\n",encoding="utf-8")
            self.assertEqual(importar(banco,ibge_csv=ibge)["ibge_municipios"],1)
            ibge.write_text("codigo_ibge,nome,uf,populacao,ano_populacao\n3550308,São Paulo,SP,123,\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"População sem ano"):
                importar(banco,ibge_csv=ibge)
            with sqlite3.connect(banco) as cx:
                self.assertEqual(cx.execute("SELECT populacao FROM municipios").fetchone()[0],11000000)


    def test_populacao_validada_preserva_nomes_e_recusa_hash_alterado(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            db = root / "app.sqlite"
            csv_path = root / "municipios_populacao_2026.csv"
            codes = [str(1000000 + i) for i in range(5571)]
            with sqlite3.connect(db) as cx:
                cx.executescript("""
                    CREATE TABLE municipios(codigo_ibge TEXT PRIMARY KEY,nome TEXT,uf TEXT,populacao INTEGER,ano_populacao INTEGER);
                    CREATE TABLE origem_dados(dominio TEXT PRIMARY KEY,arquivo TEXT,nota TEXT);
                """)
                cx.executemany("INSERT INTO municipios(codigo_ibge,nome,uf) VALUES (?, ?, ?)",
                               [(c, "Nome IBGE", "SP") for c in codes])
            with csv_path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["codigo_ibge", "municipio", "uf", "populacao_estimada_2026"])
                writer.writerows((c, "Nome TSE", "RJ", 1000 + i) for i, c in enumerate(codes))
            meta = {"resultado":"PASS", "fonte":"IBGE SIDRA", "tabela":6579,
                    "variavel":9324, "ano_referencia":2026, "municipios":5571,
                    "url":"https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/2026?formato=json",
                    "sha256_saida":hashlib.sha256(csv_path.read_bytes()).hexdigest()}
            (root / "validacao.json").write_text(json.dumps(meta), encoding="utf-8")
            self.assertEqual(importar(db,populacao_csv=csv_path)["populacao_municipios"],5571)
            with sqlite3.connect(db) as cx:
                self.assertEqual(cx.execute(
                    "SELECT nome,uf,populacao,ano_populacao FROM municipios WHERE codigo_ibge=?",
                    (codes[0],)).fetchone(),("Nome IBGE","SP",1000,2026))
                self.assertEqual(cx.execute("SELECT COUNT(*) FROM municipios WHERE populacao IS NOT NULL").fetchone()[0],5571)
            csv_path.write_text(csv_path.read_text(encoding="utf-8")+"\\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash"):
                importar(db,populacao_csv=csv_path)

    def test_tse_requer_snapshot_real_validado(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); banco=root/"app.sqlite"; tse=root/"snapshot"
            tse.mkdir()
            with sqlite3.connect(banco) as cx:
                cx.execute("CREATE TABLE municipios(codigo_ibge TEXT PRIMARY KEY)")
            with self.assertRaises(FileNotFoundError):
                importar(banco,tse_dir=tse)

if __name__=="__main__":
    unittest.main()
