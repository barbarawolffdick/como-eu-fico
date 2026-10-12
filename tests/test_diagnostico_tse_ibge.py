"""Testes sintéticos: inventário oficial e separação de erros de local e voto."""
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.inspecionar_correspondencia_tse_ibge import inspect
from scripts.construir_base_tse_ibge import connect
from scripts.diagnosticar_base_tse import report

class StageTest(unittest.TestCase):
    def test_inventario_nao_inventa_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"municipios.zip"
            with zipfile.ZipFile(path,"w") as z:
                z.writestr("oficial.csv", "CAMPO_A;CAMPO_B\n1;2\n")
            result=inspect(path)
            member=result["arquivos"][0]
            self.assertEqual(member["colunas"], ["CAMPO_A","CAMPO_B"])
            self.assertEqual(member["amostra"], ["1","2"])
            self.assertEqual(len(result["sha256"]), 64)

    def test_erro_apenas_local_nao_falha_eleitoral(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=connect(Path(tmp)/"temp.sqlite")
            try:
                db.execute("INSERT INTO votos VALUES (?,?,?,?,?,?,?,?,?)",
                           ("SP","71072","SAO PAULO","1","1","20","13","LULA",8))
                db.execute("INSERT INTO votos VALUES (?,?,?,?,?,?,?,?,?)",
                           ("SP","71072","SAO PAULO","1","1","20","95","VOTO BRANCO",1))
                db.execute("INSERT INTO votos VALUES (?,?,?,?,?,?,?,?,?)",
                           ("SP","71072","SAO PAULO","1","1","20","96","VOTO NULO",1))
                db.execute("INSERT INTO apuracao VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           ("SP","71072","SAO PAULO","1","1","10",12,10,2,8,1,1,0,0))
                r=report(db)
                self.assertEqual(r["consistencia_eleitoral"],"PASS")
                self.assertEqual(r["identificacao_locais"],"PENDENTE")
                self.assertEqual(r["publicacao"],"BLOQUEADA")
                db.execute("UPDATE apuracao SET nominais=7")
                r=report(db)
                self.assertEqual(r["consistencia_eleitoral"],"FAIL")
            finally:
                db.close()

if __name__=="__main__":
    unittest.main()
