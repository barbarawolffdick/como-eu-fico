import sqlite3
import tempfile
import unittest
from pathlib import Path
from scripts.auditar_serie_bolsa_familia import audit

class SerieTests(unittest.TestCase):
    def test_serie_e_variacao_municipal(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"test.sqlite"
            with sqlite3.connect(path) as db:
                db.executescript("""
                CREATE TABLE origem (mes_competencia TEXT, parcelas INTEGER, valor_centavos INTEGER, municipios INTEGER);
                CREATE TABLE parcelas_municipais (mes_competencia TEXT, mes_referencia TEXT, codigo_ibge TEXT, valor_centavos INTEGER, quantidade_parcelas INTEGER);
                """)
                for y in (2025,2026):
                    for m in range(1,13):
                        mes=f"{y}{m:02d}"
                        if not "202501"<=mes<="202608":continue
                        codes=["3550308"]+(["5101837"] if mes>="202510" else [])
                        db.execute("INSERT INTO origem VALUES(?,?,?,?)",(mes,len(codes),len(codes)*100,len(codes)))
                        for code in codes:
                            db.execute("INSERT INTO parcelas_municipais VALUES(?,?,?,?,?)",(mes,mes,code,100,1))
            r=audit(path)
            self.assertEqual(len(r["serie"]),20)
            self.assertEqual(r["primeira_presenca_boa_esperanca_do_norte"],"202510")
            self.assertEqual(len(r["mudancas_conjunto_municipal"]),1)
            self.assertEqual(r["serie"][0]["percentual_parcelas_referencia_anterior"],0)
            self.assertEqual(r["status"],"PASS_COM_RESSALVAS")

if __name__=="__main__": unittest.main()
