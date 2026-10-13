import unittest
from scripts.processar_lote_bolsa import months

class BatchTests(unittest.TestCase):
    def test_tres_meses(self):
        self.assertEqual(months("202503",3),["202503","202504","202505"])
    def test_transicao_de_ano(self):
        self.assertEqual(months("202512",3),["202512","202601","202602"])
    def test_limite_final(self):
        self.assertEqual(months("202609",1),["202609"])
        with self.assertRaises(ValueError):months("202609",2)
    def test_maximo_tres(self):
        with self.assertRaises(ValueError):months("202503",4)

if __name__=="__main__":unittest.main()
