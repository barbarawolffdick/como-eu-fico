"""Série anual de INSS e FPM com IPCA, sem rede nem openpyxl."""
import copy
import json
from pathlib import Path
import unittest

from scripts.publicar_dinheiro_federal_serie import ipca_medio_anual, montar_serie, validar_serie

ROOT = Path(__file__).resolve().parents[1]
SERIE = json.loads((ROOT / "data/public/dinheiro_federal_serie.json").read_text())


def documento_ipca(meses_2024=12):
    serie = {f"2023{m:02d}": str(6000 + m) for m in range(1, 13)}
    serie |= {f"2024{m:02d}": str(6300 + m) for m in range(1, meses_2024 + 1)}
    return [{"id": "2266", "resultados": [{"series": [{"serie": serie}]}]}]


class SerieTest(unittest.TestCase):
    def test_ipca_e_a_media_dos_doze_meses(self):
        medias = ipca_medio_anual(documento_ipca(), [2023, 2024])
        self.assertAlmostEqual(medias["2023"], 6006.5)
        self.assertAlmostEqual(medias["2024"], 6306.5)

    def test_ano_sem_doze_meses_de_ipca_interrompe(self):
        with self.assertRaises(ValueError):
            ipca_medio_anual(documento_ipca(meses_2024=11), [2023, 2024])

    def test_ano_recusado_fica_nulo_e_nao_vira_zero(self):
        cadastro = {"2307304": {}, "2605459": {}}
        doc = montar_serie([2023, 2024], cadastro,
                           {2023: {"2307304": {"total": 10}, "2605459": {"total": 5}}, 2024: None},
                           {2023: {"2307304": 7}, 2024: None},
                           {"2023": {"inss": "completo", "fpm": "completo"}, "2024": {"inss": "recusado: x", "fpm": "incompleto: y"}},
                           {"2023": 1.0, "2024": 1.1}, {})
        self.assertEqual(doc["registros"]["2307304"]["inss"], {"2023": 10, "2024": None})
        self.assertIsNone(doc["registros"]["2605459"]["fpm"]["2023"])  # sem FPM no ano completo: nulo
        self.assertIsNone(doc["registros"]["2307304"]["fpm"]["2024"])

    def test_publicacao_coerente_com_a_situacao(self):
        cadastro = {c: {} for c in SERIE["registros"]}
        validar_serie(SERIE, cadastro)
        errado = copy.deepcopy(SERIE)
        ano_recusado = next(a for a in errado["anos"] if errado["situacao"][a]["fpm"] != "completo")
        next(iter(errado["registros"].values()))["fpm"][ano_recusado] = 1
        with self.assertRaises(ValueError):
            validar_serie(errado, cadastro)

    def test_juazeiro_confere_com_a_fonte(self):
        r = SERIE["registros"]["2307304"]
        self.assertEqual(r["inss"]["2025"], 85834798989)
        self.assertEqual(r["fpm"]["2025"], 15584922874)
        self.assertEqual(SERIE["situacao"]["2025"], {"inss": "completo", "fpm": "completo"})


if __name__ == "__main__":
    unittest.main()
