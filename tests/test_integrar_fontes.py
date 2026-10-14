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
