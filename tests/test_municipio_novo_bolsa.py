import tempfile
import unittest
from pathlib import Path
from scripts.ingerir_bolsa_familia import bridge

class MunicipioNovoTests(unittest.TestCase):
    def test_boa_esperanca_do_norte_2025(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"ponte.csv"
            path.write_text("1234;000;Municipio Teste;SP;3550308\n",encoding="latin-1")
            mapping=bridge(path)
            self.assertEqual(mapping[("MT","1182")],"5101837")
            self.assertEqual(mapping[("SP","1234")],"3550308")

    def test_conflito_nao_e_sobrescrito(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"ponte.csv"
            path.write_text("1182;000;Municipio Incorreto;MT;5100000\n",encoding="latin-1")
            with self.assertRaises(ValueError):
                bridge(path)

if __name__=="__main__": unittest.main()
