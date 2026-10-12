"""Testa correspondência oficial de códigos sem depender de nomes e rede."""
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.construir_base_tse_ibge import connect
from scripts.aplicar_codigos_oficiais_tse_ibge import mapping_from_zip,validate

class OfficialCodesTests(unittest.TestCase):
    def test_csv_oficial_com_acentos_latin1(self):
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/"codigos.zip"
            content=("SG_UF;CD_MUNICIPIO_TSE;CD_MUNICIPIO_IBGE;NM_MUNICIPIO_TSE;NM_MUNICIPIO_IBGE\n"
                     "SP;071013;3550001;São Luís do Paraitinga;São Luís do Paraitinga\n")
            with zipfile.ZipFile(file,"w") as z:
                z.writestr("municipio_tse_ibge.csv",content.encode("latin-1"))
            mapping=mapping_from_zip(file)
            self.assertEqual(mapping[("SP","71013")][0],"3550001")

    def test_codigo_tse_com_zero_a_esquerda(self):
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/"codigos.zip"
            with zipfile.ZipFile(file,"w") as z:
                z.writestr("municipio_tse_ibge.csv",
                    "SG_UF;CD_MUNICIPIO_TSE;CD_MUNICIPIO_IBGE;NM_MUNICIPIO_TSE;NM_MUNICIPIO_IBGE\n"
                    "AC;01007;1200138;Bujari;Bujari\n")
            mapping=mapping_from_zip(file)
            self.assertEqual(mapping[("AC","1007")][0],"1200138")

    def test_identificacao_por_codigo_com_nome_diferente(self):
        with tempfile.TemporaryDirectory() as temp:
            db=connect(Path(temp)/"test.sqlite")
            try:
                db.execute("INSERT INTO ibge VALUES (?,?,?,?)",("1200138","AC","Bujari","BUJARI"))
                db.execute("INSERT INTO apuracao VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           ("AC","1007","BUJARY","1","1","20",12,10,2,8,1,1,0,0))
                pairs,problems=validate(db,{("AC","1007"):("1200138","Bujari")})
                self.assertEqual(problems,[])
                self.assertEqual(pairs[0][3],"1200138")
            finally:
                db.close()

    def test_codigo_inexistente_impede_publicacao(self):
        with tempfile.TemporaryDirectory() as temp:
            db=connect(Path(temp)/"test.sqlite")
            try:
                db.execute("INSERT INTO ibge VALUES (?,?,?,?)",("1200138","AC","Bujari","BUJARI"))
                db.execute("INSERT INTO apuracao VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           ("AC","1007","BUJARI","1","1","20",12,10,2,8,1,1,0,0))
                pairs,problems=validate(db,{})
                self.assertEqual(pairs,[])
                self.assertTrue(any(p["motivo"]=="sem_codigo_na_tabela_oficial" for p in problems))
            finally:
                db.close()

if __name__=="__main__":
    unittest.main()
