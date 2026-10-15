"""Protege correspondências MDS/IBGE explícitas e impede matching aproximado."""
import json
import unittest
from pathlib import Path
from scripts.publicar_pessoas_mds import norm

ROOT=Path(__file__).resolve().parents[1]
class CorrespondenciaMDSTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=json.loads((ROOT/"data/public/rankings_2026.json").read_text(encoding="utf-8"))["registros"]
        cls.aliases=json.loads((ROOT/"data/referencia/correspondencia_mds_ibge_2026.json").read_text(encoding="utf-8"))["aliases"]

    def test_catalogo_univoco_e_documentado(self):
        codes={r["codigo_ibge"]:r for r in self.rows}
        source=set()
        destination=set()
        for alias in self.aliases:
            key=(alias["uf"],alias["nome_mds_normalizado"])
            self.assertNotIn(key,source)
            source.add(key)
            code=alias["codigo_ibge"]
            self.assertNotIn(code,destination)
            destination.add(code)
            self.assertRegex(code,r"^\d{7}$")
            self.assertEqual(codes[code]["uf"],alias["uf"])
            self.assertEqual(codes[code]["nome"],alias["nome_ibge"])
            self.assertTrue(alias["evidencia_oficial"].startswith("https://"))
            self.assertEqual(alias["fonte_codigo_ibge"],"https://www.ibge.gov.br/explica/codigos-dos-municipios.php")
            self.assertNotEqual(norm(alias["nome_ibge"]),alias["nome_mds_normalizado"])
        self.assertEqual(len(source),11)

    def test_cobertura_original_e_novos_alvos(self):
        old=json.loads((ROOT/"data/public/pessoas_mds.json").read_text(encoding="utf-8"))
        self.assertEqual(old["municipios_ibge"],5571)
        missing=set(old["municipios_sem_dado"])
        codes={a["codigo_ibge"] for a in self.aliases}
        # Funciona antes e depois da regeneração do snapshot.
        self.assertTrue(codes.issubset(set(old["registros"])))
        self.assertTrue(missing.isdisjoint(codes) or codes.issubset(missing))
        self.assertEqual(missing,set())
        self.assertEqual(old["municipios_com_dado"],5571)

if __name__=="__main__":
    unittest.main()
