import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import server


class ServerStartupTests(unittest.TestCase):
    def test_missing_db_reports_actionable_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(server, "DB", Path(tmp) / "missing.sqlite"):
                result = TestClient(server.app).get("/api/health")
                self.assertEqual(result.status_code, 503)
                self.assertIn("git lfs pull", result.json()["detail"])

    def test_lfs_pointer_reports_actionable_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.sqlite"
            path.write_text("version https://git-lfs.github.com/spec/v1\\noid sha256:123\\nsize 123\\n", encoding="utf-8")
            with patch.object(server, "DB", path):
                result = TestClient(server.app).get("/api/health")
                self.assertEqual(result.status_code, 503)
                self.assertIn("ponteiro", result.json()["detail"])

    def test_rankings_financeiros_e_populacao(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.sqlite"
            with sqlite3.connect(path) as db:
                db.executescript("""
                CREATE TABLE municipios(codigo_ibge TEXT PRIMARY KEY,nome TEXT,uf TEXT,populacao INTEGER,ano_populacao INTEGER);
                CREATE TABLE votos_presidenciais(codigo_ibge TEXT,eleicao INTEGER,turno INTEGER,candidato TEXT,votos INTEGER);
                CREATE TABLE bolsa_familia(mes_competencia TEXT,codigo_ibge TEXT,parcelas INTEGER,valor_centavos INTEGER);
                CREATE VIEW bolsa_familia_mensal AS SELECT codigo_ibge,mes_competencia,parcelas,valor_centavos FROM bolsa_familia;
                CREATE TABLE origem_dados(dominio TEXT,arquivo TEXT,nota TEXT);
                """)
                db.executemany("INSERT INTO municipios VALUES(?,?,?,NULL,NULL)",
                               [(str(1000000+i),"Teste","SP") for i in range(5570)]+[("3550308","São Paulo","SP")])
                db.execute("INSERT INTO votos_presidenciais VALUES('3550308',2026,1,'13',100)")
                db.execute("INSERT INTO votos_presidenciais VALUES('3550308',2026,1,'22',50)")
                db.execute("INSERT INTO bolsa_familia VALUES('202601','3550308',2,80000)")
            with patch.object(server,"DB",path):
                client=TestClient(server.app)
                resp=client.get("/api/rankings?metrica=valor_total")
                self.assertEqual(resp.status_code,200)
                self.assertEqual(resp.json()["resultados"][0]["valor_centavos"],80000)
                self.assertEqual(resp.json()["resultados"][0]["vencedor"],"13")
                self.assertFalse(client.get("/api/rankings?metrica=valor_habitante").json()["disponivel"])
                self.assertEqual(client.get("/api/rankings?inicio=202701").status_code,422)
                with sqlite3.connect(path) as db:
                    db.execute("UPDATE municipios SET populacao=200,ano_populacao=2026 WHERE codigo_ibge='3550308'")
                relative=client.get("/api/rankings?metrica=valor_habitante").json()
                self.assertTrue(relative["disponivel"])
                self.assertEqual(relative["resultados"][0]["centavos_por_habitante"],400)

    def test_healthy_database_and_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.sqlite"
            with sqlite3.connect(path) as db:
                db.executescript("""
                    CREATE TABLE municipios(codigo_ibge TEXT PRIMARY KEY, nome TEXT, uf TEXT, populacao INTEGER, ano_populacao INTEGER);
                    CREATE TABLE votos_presidenciais(codigo_ibge TEXT, eleicao INTEGER, turno INTEGER, candidato TEXT, votos INTEGER);
                    CREATE TABLE bolsa_familia(mes_competencia TEXT, codigo_ibge TEXT, parcelas INTEGER, valor_centavos INTEGER);
                    CREATE VIEW bolsa_familia_mensal AS SELECT codigo_ibge,mes_competencia,parcelas,valor_centavos FROM bolsa_familia;
                    CREATE TABLE origem_dados(dominio TEXT, arquivo TEXT, nota TEXT);
                """)
                db.executemany("INSERT INTO municipios(codigo_ibge,nome,uf) VALUES (?,?,?)",
                               [(str(1000000+i), "Teste", "SP") for i in range(5570)]
                               + [("3550308", "São Paulo", "SP")])
                db.execute("INSERT INTO votos_presidenciais VALUES('3550308',2026,1,'13',100)")
                db.execute("INSERT INTO bolsa_familia VALUES('202501','3550308',1,60000)")
            with patch.object(server, "DB", path):
                client = TestClient(server.app)
                self.assertEqual(client.get("/api/health").json()["status"], "ok")
                self.assertEqual(client.get("/").status_code, 200)
                self.assertEqual(client.get("/api/municipios?q=3550308").json()[0]["nome"], "São Paulo")
                response = client.get("/api/municipios/3550308")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["votos_presidenciais"][0]["votos"], 100)


if __name__ == "__main__":
    unittest.main()
