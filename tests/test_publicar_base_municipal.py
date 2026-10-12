import csv
import json
import tempfile
import unittest
from pathlib import Path
from scripts.publicar_base_municipal import publish

class PublishTest(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.source=self.root/"source"
        self.source.mkdir()
        self.dest=self.root/"curated"
        (self.source/"validacao.json").write_text(json.dumps({"resultados_municipais":"PASS",
            "consistencia_eleitoral":"PASS","correspondencia":"PASS"}))
        with (self.source/"municipios.csv").open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["codigo_ibge","votos_validos"])
            w.writeheader()
            for i in range(5571):
                w.writerow({"codigo_ibge":str(1000000+i),"votos_validos":i+1})
        with (self.source/"candidatos_municipios.csv").open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["codigo_ibge","votos"])
            w.writeheader()
            for i in range(5571):
                w.writerow({"codigo_ibge":str(1000000+i),"votos":i+1})
    def test_publica_snapshot_com_manifesto(self):
        result=publish(self.source,self.dest)
        self.assertEqual(result["municipios"],5571)
        self.assertTrue((self.dest/"manifesto.json").is_file())
        self.assertEqual(len(result["arquivos_sha256"]),3)
    def test_impede_snapshot_duplicado(self):
        publish(self.source,self.dest)
        with self.assertRaises(FileExistsError):
            publish(self.source,self.dest)
    def test_divergencia_candidatos_bloqueia(self):
        path=self.source/"candidatos_municipios.csv"
        content=path.read_text()
        path.write_text(content.replace("1000000,1","1000000,99",1))
        with self.assertRaisesRegex(ValueError,"Composição municipal"):
            publish(self.source,self.dest)
        self.assertFalse(self.dest.exists())
    def test_validacao_obrigatoria(self):
        (self.source/"validacao.json").write_text('{"resultados_municipais":"BLOQUEADO"}')
        with self.assertRaisesRegex(ValueError,"Validação insuficiente"):
            publish(self.source,self.dest)
if __name__=="__main__":
    unittest.main()
