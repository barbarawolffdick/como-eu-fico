import unittest
from scripts.auditar_amostra_bolsa_familia import audit_bytes, value

HEADER="MÊS COMPETÊNCIA;MÊS REFERÊNCIA;UF;CÓDIGO MUNICÍPIO SIAFI;NOME MUNICÍPIO;CPF FAVORECIDO;NIS FAVORECIDO;NOME FAVORECIDO;VALOR PARCELA\n"
def sample(rows):
    return (HEADER+"\n".join(rows)+"\n").encode("utf-8")

class AuditTest(unittest.TestCase):
    def test_aggregate_without_personal_data(self):
        b=sample(["202401;202401;SP;7107;São Paulo;123;555;Pessoa A;600,00",
                  "202312;202401;SP;7107;São Paulo;456;666;Pessoa B;200,25"])
        r=audit_bytes(b,"202401","official.csv")
        self.assertEqual(r["status"],"PASS")
        self.assertEqual(r["total_centavos"],80025)
        self.assertEqual(r["agregado_municipal"][0]["parcelas"],2)
        self.assertNotIn("Pessoa A",str(r))
        self.assertEqual(r["meses_competencia"],["202312","202401"])
    def test_wrong_month_is_blocked(self):
        r=audit_bytes(sample(["202401;202402;SP;7107;São Paulo;123;555;Pessoa A;600,00"]),"202401","x.csv")
        self.assertEqual(r["status"],"BLOCKED")
    def test_missing_amount_is_blocked(self):
        r=audit_bytes(sample(["202401;202401;SP;7107;São Paulo;123;555;Pessoa A;..."]),"202401","x.csv")
        self.assertEqual(r["status"],"BLOCKED")
    def test_invalid_number(self):
        with self.assertRaises(ValueError): value("NaN")

if __name__=="__main__":unittest.main()
