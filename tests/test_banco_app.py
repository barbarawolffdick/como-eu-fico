import csv
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from app.database import criar_banco

class BancoAppTests(unittest.TestCase):
    def test_cria_banco_integrado_sem_alterar_fontes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tse = root / "tse"
            tse.mkdir()
            (tse / "validacao.json").write_text(json.dumps({
                "resultados_municipais": "PASS", "consistencia_eleitoral": "PASS",
                "correspondencia": "PASS"
            }), encoding="utf-8")
            (tse / "municipios.csv").write_text(
                "codigo_ibge,votos_validos,municipio,uf\n3550308,10,Sao Paulo,SP\n",
                encoding="utf-8")
            (tse / "candidatos_municipios.csv").write_text(
                "codigo_ibge,numero_candidato,votos\n3550308,13,6\n3550308,22,4\n",
                encoding="utf-8")
            src = root / "bolsa.sqlite"
            with sqlite3.connect(src) as cx:
                cx.executescript("""
                CREATE TABLE origem(mes_competencia TEXT, parcelas INTEGER, valor_centavos INTEGER);
                CREATE TABLE parcelas_municipais(
                    mes_competencia TEXT, mes_referencia TEXT, codigo_ibge TEXT,
                    valor_centavos INTEGER, quantidade_parcelas INTEGER);
                INSERT INTO origem VALUES('202501',3,50000);
                INSERT INTO parcelas_municipais VALUES('202501','202501','3550308',30000,2);
                INSERT INTO parcelas_municipais VALUES('202501','202412','3550308',20000,1);
                """)
            dest = root / "app.sqlite"
            summary = criar_banco(tse, src, dest)
            self.assertEqual(summary["parcelas"], 3)
            with sqlite3.connect(dest) as cx:
                self.assertEqual(cx.execute("SELECT COUNT(*) FROM municipios").fetchone()[0], 1)
                self.assertEqual(cx.execute("SELECT SUM(votos) FROM votos_presidenciais").fetchone()[0], 10)
                self.assertEqual(cx.execute("SELECT parcelas,valor_centavos FROM bolsa_familia_mensal").fetchone(), (3, 50000))
            with self.assertRaises(FileExistsError):
                criar_banco(tse, src, dest)


    def test_banco_cgu_real_sem_snapshot_eleitoral(self):
        from app.database import criar_banco_bolsa
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "cgu.sqlite"
            dest = root / "app.sqlite"
            with sqlite3.connect(source) as cx:
                cx.executescript("""
                    CREATE TABLE origem(mes_competencia TEXT, parcelas INTEGER, valor_centavos INTEGER);
                    CREATE TABLE parcelas_municipais(
                        mes_competencia TEXT, mes_referencia TEXT, codigo_ibge TEXT,
                        valor_centavos INTEGER, quantidade_parcelas INTEGER);
                    INSERT INTO origem VALUES('202501',2,15000);
                    INSERT INTO parcelas_municipais VALUES('202501','202501','3550308',15000,2);
                """)
            result = criar_banco_bolsa(source, dest)
            self.assertEqual(result["municipios"], 1)
            with sqlite3.connect(dest) as cx:
                self.assertEqual(cx.execute("SELECT SUM(parcelas) FROM bolsa_familia").fetchone()[0], 2)
                self.assertEqual(cx.execute("SELECT COUNT(*) FROM votos_presidenciais").fetchone()[0], 0)
            with self.assertRaises(FileExistsError):
                criar_banco_bolsa(source, dest)

if __name__ == "__main__":
    unittest.main()
