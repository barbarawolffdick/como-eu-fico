"""Regressões sobre amostras oficiais reais; nenhuma escrita nas fontes."""
import copy
import json
from pathlib import Path
import unittest

from scripts.publicar_saude_piloto import (
    PILOTO, centavos, extrair_aps, extrair_fns, extrair_pmmb, ponte_ibge,
)

ROOT = Path(__file__).resolve().parents[1]
AMOSTRA = json.loads((ROOT / "tests/fixtures/saude_piloto.json").read_text())
CADASTRO = {r["codigo_ibge"]: r for r in json.loads((ROOT / "data/public/rankings_2026.json").read_text())["registros"]}


class SaudePilotoTest(unittest.TestCase):
    def test_fundo_estadual_nao_infla_repasse_municipal(self):
        dados, _ = extrair_fns(AMOSTRA["fns"], CADASTRO)
        sp = dados["3550308"]
        self.assertEqual(sp["municipal"]["valor_liquido_centavos"], 4_132_013_550)
        self.assertEqual(sp["estadual_sediado_na_cidade"]["valor_liquido_centavos"], 26_775_000)
        self.assertIsNone(dados["5101837"]["municipal"])

    def test_montante_ausente_permanece_nulo(self):
        rows = copy.deepcopy(AMOSTRA["fns"])
        rows[0][1]["VL_LIQUIDO"] = None
        dados, _ = extrair_fns(rows, CADASTRO)
        self.assertIsNone(dados["3550308"]["municipal"]["valor_liquido_centavos"])

    def test_duplicacao_financeira_impede_publicacao(self):
        rows = AMOSTRA["fns"] + [AMOSTRA["fns"][0]]
        with self.assertRaisesRegex(ValueError, "duplicada"):
            extrair_fns(rows, CADASTRO)

    def test_ponte_territorial_ambigua_impede_juncao(self):
        with self.assertRaisesRegex(ValueError, "ambígua"):
            ponte_ibge({**CADASTRO, "3550309": {}})

    def test_competencia_cnes_nao_vira_parcela(self):
        dados = extrair_aps(AMOSTRA["aps"], "3550308", "202610")
        self.assertEqual(dados["parcela"], "202610")
        self.assertEqual(dados["competencia_cnes"], "202608")
        self.assertEqual(dados["equipes"][0]["financiadas"], 1693)
        self.assertNotEqual(dados["equipes"][0]["homologadas"], dados["equipes"][0]["financiadas"])

    def test_aps_multiplo_processo_nao_soma_equipes(self):
        doc = copy.deepcopy(AMOSTRA["aps"])
        doc["pagamentos"] += copy.deepcopy(doc["pagamentos"])
        with self.assertRaisesRegex(ValueError, "reconciliação"):
            extrair_aps(doc, "3550308", "202610")

    def test_filtro_municipal_da_fonte_precisa_ser_respeitado(self):
        with self.assertRaisesRegex(ValueError, "Filtro municipal"):
            extrair_pmmb(AMOSTRA["pmmb"], "2611606")

    def test_profissionais_sao_estoque_na_ultima_data(self):
        dados = extrair_pmmb(AMOSTRA["pmmb"], "3550308")
        self.assertEqual(dados["ultimo"], {"data_referencia": "2026-10-05", "profissionais_ativos": 163})
        self.assertEqual(len(dados["serie"]), 2)
        vazio = extrair_pmmb({"pmmb_serie_historica": []}, "5101837")
        self.assertIsNone(vazio["ultimo"])
        self.assertIn("Ausência não é zero", vazio["motivo"])

    def test_snapshot_publicado_confere_somas_periodos_e_ausencias(self):
        snapshot = json.loads((ROOT / "data/public/saude_piloto.json").read_text())
        self.assertEqual(set(snapshot["registros"]), set(PILOTO))
        self.assertEqual(snapshot["natureza"], "observado")
        self.assertEqual(snapshot["registros"]["3550308"]["fns"]["municipal"]["valor_liquido_centavos"], 70_188_363_340)
        for codigo, row in snapshot["registros"].items():
            self.assertEqual(row["municipio"]["codigo_ibge"], codigo)
            self.assertEqual(row["fns"]["periodo_fim"], "202607")
            for tipo in ("municipal", "estadual_sediado_na_cidade"):
                valor = row["fns"][tipo]
                if valor is not None:
                    self.assertEqual(valor["valor_liquido_centavos"], sum(x["valor_liquido_centavos"] for x in valor["componentes"]))
            for origem in row["proveniencia"].values():
                self.assertEqual(len(origem["sha256"]), 64)
                self.assertIn("saude.gov.br", origem["url"])
        self.assertIsNone(snapshot["registros"]["5101837"]["mais_medicos"]["ultimo"])

    def test_centavos_sem_arredondamento_de_dados_ausentes(self):
        self.assertIsNone(centavos(None))
        self.assertEqual(centavos(751501.38), 75_150_138)
        with self.assertRaises(ValueError):
            centavos("NaN")


if __name__ == "__main__":
    unittest.main()
