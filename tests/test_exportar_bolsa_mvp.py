import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path
from scripts.exportar_bolsa_mvp import exportar

class ExportarMvpTests(unittest.TestCase):
    def test_aggregates_and_reconciles(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beneficios.sqlite"
            output = Path(tmp) / "mvp.csv"
            with sqlite3.connect(db) as cx:
                cx.executescript("""
                    CREATE TABLE origem (mes_competencia TEXT, parcelas INTEGER, valor_centavos INTEGER);
                    CREATE TABLE parcelas_municipais (
                       mes_competencia TEXT, mes_referencia TEXT, codigo_ibge TEXT,
                       valor_centavos INTEGER, quantidade_parcelas INTEGER);
                    INSERT INTO origem VALUES ('202501', 3, 17000);
                    INSERT INTO parcelas_municipais VALUES ('202501','202501','3550308',10000,2);
                    INSERT INTO parcelas_municipais VALUES ('202501','202412','3550308',7000,1);
                """)
            result = exportar(db, output)
            self.assertEqual(result["parcelas"], 3)
            with output.open(encoding="utf-8", newline="") as src:
                rows = list(csv.DictReader(src))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["codigo_ibge"], "3550308")
            self.assertEqual(rows[0]["valor_centavos"], "17000")
            with self.assertRaises(FileExistsError):
                exportar(db, output)

    def test_blocks_divergent_total_without_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beneficios.sqlite"
            output = Path(tmp) / "mvp.csv"
            with sqlite3.connect(db) as cx:
                cx.executescript("""
                    CREATE TABLE origem (mes_competencia TEXT, parcelas INTEGER, valor_centavos INTEGER);
                    CREATE TABLE parcelas_municipais (
                      mes_competencia TEXT, mes_referencia TEXT, codigo_ibge TEXT,
                      valor_centavos INTEGER, quantidade_parcelas INTEGER);
                    INSERT INTO origem VALUES ('202501', 9, 9000);
                    INSERT INTO parcelas_municipais VALUES ('202501','202501','3550308',1000,1);
                """)
            with self.assertRaisesRegex(ValueError, "não reconcilia"):
                exportar(db, output)
            self.assertFalse(output.exists())

if __name__ == "__main__":
    unittest.main()
