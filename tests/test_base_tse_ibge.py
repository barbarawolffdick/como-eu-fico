"""Testes isolados do pipeline nacional sem dados reais."""
import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path
from scripts.construir_base_tse_ibge import connect, norm, map_ibge, audit, load_ibge

class BaseTseTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db=connect(Path(self.tmp.name)/"test.sqlite")
        self.addCleanup(self.db.close)
        self.ibge=Path(self.tmp.name)/"municipios_ibge.csv"
        self.ibge.write_text("codigo_ibge,uf,municipio_ibge\n3550308,SP,São Paulo\n",encoding="utf-8")
        load_ibge(self.db,self.ibge)
    def insert_pair(self,nominais=8,brancos=1,nulos=1,local="10"):
        self.db.execute("INSERT INTO votos VALUES (?,?,?,?,?,?,?,?,?)",("SP","71072","SAO PAULO","1","1",local,"13","LULA",nominais))
        self.db.execute("INSERT INTO votos VALUES (?,?,?,?,?,?,?,?,?)",("SP","71072","SAO PAULO","1","1",local,"95","VOTO BRANCO",brancos))
        self.db.execute("INSERT INTO votos VALUES (?,?,?,?,?,?,?,?,?)",("SP","71072","SAO PAULO","1","1",local,"96","VOTO NULO",nulos))
        self.db.execute("INSERT INTO apuracao VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        ("SP","71072","SAO PAULO","1","1",local,12,10,2,8,1,1,0,0))
    def test_nome_ibge_normalizado(self):
        self.insert_pair()
        self.assertEqual(map_ibge(self.db),[])
        self.assertEqual(self.db.execute("SELECT codigo_ibge FROM municipios_tse_ibge").fetchone()[0],"3550308")
    def test_composicao_detecta_divergencia(self):
        self.insert_pair(nominais=7)
        self.assertTrue(any(x["regra"]=="composicao_secao" for x in audit(self.db)))
    def test_composicao_valida(self):
        self.insert_pair()
        self.assertEqual(audit(self.db),[])
    def test_falta_ibge_bloqueia_correspondencia(self):
        self.db.execute("INSERT INTO apuracao VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        ("BA","123","MUNICIPIO INEXISTENTE","1","1","10",12,10,2,8,1,1,0,0))
        self.db.execute("INSERT INTO votos VALUES (?,?,?,?,?,?,?,?,?)",
                        ("BA","123","MUNICIPIO INEXISTENTE","1","1","10","13","LULA",8))
        issues=map_ibge(self.db)
        self.assertEqual(len(issues),1)
        self.assertEqual(issues[0]["motivo"],"sem_correspondencia_ibge")
    def test_chave_votacao_duplicada_falha(self):
        self.insert_pair()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO votos VALUES (?,?,?,?,?,?,?,?,?)",
                            ("SP","71072","SAO PAULO","1","1","10","13","LULA",8))
if __name__=="__main__":
    unittest.main()
