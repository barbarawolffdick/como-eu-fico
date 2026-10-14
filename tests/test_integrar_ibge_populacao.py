import unittest
from scripts.integrar_ibge_populacao import population,join

class PopulationTests(unittest.TestCase):
    def test_valida_periodo_codigo_e_populacao(self):
        payload=[{"D1C":"Município (Código)","D2C":"Variável (Código)","D3C":"Ano (Código)","V":"Valor"},
                 {"D1C":"3550308","D2C":"9324","D3C":"2026","V":"12000000"}]
        self.assertEqual(population(payload),{"3550308":12000000})
    def test_bloqueia_ano_errado(self):
        with self.assertRaisesRegex(ValueError,"período"):
            population([{"D1C":"","D2C":"","D3C":"","V":""},{"D1C":"3550308","D2C":"9324","D3C":"2025","V":"123"}])
    def test_bloqueia_ausencia_de_dados(self):
        with self.assertRaises(ValueError):
            population([{"D1C":"","D2C":"","D3C":"","V":""},{"D1C":"3550308","D2C":"9324","D3C":"2026","V":"..."}])
    def test_bloqueia_cobertura_parcial(self):
        data=[{"codigo_ibge":str(1000000+i),"votos_validos":"10"} for i in range(5571)]
        with self.assertRaisesRegex(ValueError,"Cobertura"):
            join(data,{data[0]["codigo_ibge"]:100})
    def test_nao_muda_votos_e_mantem_codigo(self):
        data=[{"codigo_ibge":str(1000000+i),"votos_validos":"10"} for i in range(5571)]
        populations={r["codigo_ibge"]:100+i for i,r in enumerate(data)}
        result=join(data,populations)
        self.assertEqual(result[0]["votos_validos"],"10")
        self.assertEqual(result[0]["populacao_estimada_2026"],100)
        self.assertEqual(len(result),5571)

if __name__=="__main__":
    unittest.main()
