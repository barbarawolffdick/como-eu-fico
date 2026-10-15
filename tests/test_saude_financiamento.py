"""Regressões financeiras e territoriais sobre linhas reais das fontes oficiais."""
import copy
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import unittest

from scripts.publicar_financiamento_saude import (
    dinheiro, extrair_cnes, extrair_equipamento, extrair_leitos, extrair_siops,
    percentual, resumir_fns, soma_validada, validar,
)

ROOT = Path(__file__).resolve().parents[1]
CADASTRO = {r["codigo_ibge"]: r for r in json.loads((ROOT / "data/public/rankings_2026.json").read_text())["registros"]}
AMOSTRA = json.loads((ROOT / "tests/fixtures/financiamento_saude.json").read_text())
SNAPSHOT = json.loads((ROOT / "data/public/financiamento_saude.json").read_text())


class FinanciamentoSaudeTest(unittest.TestCase):
    def test_centavos_de_csv_e_xlsx_e_ausencia(self):
        self.assertEqual(dinheiro("1.234,56"), 123456)
        self.assertEqual(dinheiro(1234.56), 123456)
        self.assertIsNone(dinheiro("-"))
        self.assertIsNone(soma_validada([100, None]))
        self.assertIsNone(soma_validada([]))
        self.assertEqual(soma_validada([0]), 0)

    def test_emenda_e_subconjunto_sem_somar_novamente(self):
        dados, _ = resumir_fns(AMOSTRA["fns"], CADASTRO, 2026, 7)
        municipal = dados["3550308"]["municipal"]
        esperado = sum(dinheiro(r["VL_LIQUIDO"]) for _, r in AMOSTRA["fns"] if r["TP_REPASSE"] == "MUNICIPAL" and str(r["CO_MUNICIPIO_IBGE"]) == "355030")
        self.assertEqual(municipal["valor_centavos"], esperado)
        self.assertEqual(municipal["valor_centavos"], sum(g["valor_centavos"] for g in municipal["grupos"]))
        self.assertLessEqual(municipal["emendas"]["valor_centavos"], municipal["valor_centavos"])

    def test_agencia_nao_e_receita_da_prefeitura(self):
        dados, _ = resumir_fns(AMOSTRA["fns"], CADASTRO, 2026, 7)
        brasilia = dados["5300108"]
        self.assertIsNone(brasilia["municipal"])
        self.assertEqual(brasilia["outros_destinatarios_sediados_na_cidade"]["valor_centavos"], 66054200)

    def test_fns_duplicado_ou_periodo_errado_bloqueia(self):
        with self.assertRaisesRegex(ValueError, "duplicada"):
            resumir_fns(AMOSTRA["fns"] + [AMOSTRA["fns"][0]], CADASTRO, 2026, 7)
        with self.assertRaisesRegex(ValueError, "fora do período"):
            resumir_fns(AMOSTRA["fns"], CADASTRO, 2025, 12)

    def test_siops_nao_soma_contas_filhas_ou_fases(self):
        dados, _ = extrair_siops(AMOSTRA["siops"], CADASTRO)
        r = dados["1100015"]
        # O mesmo valor também aparece em contas filhas, dotações e outras fases.
        self.assertEqual(r["fases"]["Despesas Liquidadas"]["total_centavos"], 102297663)
        self.assertEqual(r["fases"]["Despesas Pagas"]["total_centavos"], 102297663)
        self.assertIsNone(dados["5300108"])
        self.assertIsNone(r["fases"]["Despesas Liquidadas"]["percentual_fonte_federal_faf"])

    def test_siops_duplicado_ou_fonte_nova_bloqueia(self):
        row = next(r for r in AMOSTRA["siops"] if r[1]["Codigo"] == "3.0.00.00.00.00" and r[1]["Fase"] == "Despesas Liquidadas")
        with self.assertRaisesRegex(ValueError, "duplicado"):
            extrair_siops(AMOSTRA["siops"] + [row], CADASTRO)
        novo = copy.deepcopy(row)
        novo[1]["Fonte"] = "Fonte sem classificação validada"
        with self.assertRaisesRegex(ValueError, "classificação"):
            extrair_siops([novo], CADASTRO)

    def test_cnes_exclui_inativos_e_ponte_exige_uf(self):
        dados, _ = extrair_cnes(AMOSTRA["cnes"], CADASTRO)
        expected = sum(not r["CO_MOTIVO_DESAB"] and r["CO_AMBULATORIAL_SUS"] == "SIM" for _, r in AMOSTRA["cnes"])
        self.assertEqual(sum(r["estabelecimentos_sus_ambulatorial"] for r in dados.values() if r), expected)
        novo = copy.deepcopy(AMOSTRA["cnes"])
        novo[0][1]["CO_UF"] = "99"
        with self.assertRaisesRegex(ValueError, "UF CNES"):
            extrair_cnes(novo, CADASTRO)

    def test_leitos_mantem_zero_literal_sem_criar_linha_ausente(self):
        dados, _ = extrair_leitos(AMOSTRA["leitos"], CADASTRO)
        self.assertGreater(dados["2602902"]["leitos_sus"], 0)
        self.assertIsNone(dados["1504752"])
        self.assertTrue(any(r["leitos_sus"] == 0 for r in dados["2602902"]["unidades"]))

    def test_tabnet_reconcilia_totais_e_preserva_tracos(self):
        raw = (ROOT / "tests/fixtures/equipamentos_tabnet.html").read_bytes()
        registros, controle = extrair_equipamento(raw, CADASTRO)
        self.assertEqual(len(registros), 5571)
        self.assertEqual(controle["totais_controle"][0], 6874)
        self.assertIsNone(registros["1504752"][0]["valor"])
        self.assertEqual(registros["1504752"][4]["valor"], 6)
        with self.assertRaisesRegex(ValueError, "Total Tabnet"):
            extrair_equipamento(raw.replace(b';6874;', b';6875;'), CADASTRO)
        with self.assertRaisesRegex(ValueError, "Referência"):
            extrair_equipamento(raw.replace(b'Ago/2026', b'Jul/2026'), CADASTRO)

    def test_percentual_sem_base_ou_zero_nao_e_fabricado(self):
        self.assertIsNone(percentual(100, None))
        self.assertIsNone(percentual(100, 0))
        self.assertEqual(percentual(0, 100), 0)
        self.assertEqual(percentual(-10, 100), -10)

    def test_snapshot_nacional_reconcilia_e_preserva_a_aps(self):
        validar(SNAPSHOT, CADASTRO)
        self.assertEqual(len(SNAPSHOT["registros"]), 5571)
        self.assertEqual(SNAPSHOT["cobertura"]["fns_2026"], 5569)
        self.assertEqual(SNAPSHOT["cobertura"]["siops"], 5569)
        self.assertEqual(SNAPSHOT["cobertura"]["cnes"], 5571)
        self.assertEqual(SNAPSHOT["cobertura"]["leitos"], 3560)
        aps = json.loads((ROOT / "data/public/saude_municipal.json").read_text())
        for codigo, r in SNAPSHOT["registros"].items():
            self.assertEqual([p["ano"] for p in r["fns"] if p["completo"]], [2024, 2025])
            self.assertFalse(r["fns"][-1]["completo"])
            valor = r["fns"][-1]["municipal"]
            if valor:
                vaps = aps["registros"][codigo]["fns"]["municipal"]
                if vaps:
                    grupo_aps = next(g for g in valor["grupos"] if g["nome"] == "ATENÇÃO PRIMÁRIA")
                    self.assertEqual(grupo_aps["valor_centavos"], vaps["valor_liquido_centavos"])
                esperado = int((Decimal(valor["valor_centavos"]) / r["municipio"]["populacao"]).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
                self.assertEqual(r["centavos_por_habitante"], esperado)
        self.assertIsNone(SNAPSHOT["registros"]["5300108"]["centavos_por_habitante"])
        self.assertIsNone(SNAPSHOT["registros"]["5101837"]["variacao_anual_2024_2025_percentual"])

    def test_fontes_e_parametros_sao_rastreaveis(self):
        for nome, origem in SNAPSHOT["fontes"].items():
            self.assertEqual(len(origem["sha256"]), 64)
            self.assertTrue(origem["url"].startswith("https://"))
            if nome in ("equipamentos_em_uso", "estabelecimentos_com_equipamento_sus"):
                self.assertEqual(origem["metodo"], "POST")
                self.assertEqual(origem["parametros"]["Arquivos"], "eqbr2608.dbf")
        moju = SNAPSHOT["registros"]["1504752"]["equipamentos"]
        self.assertIsNone(moju["equipamentos_em_uso"][0]["valor"])
        self.assertEqual(moju["equipamentos_em_uso"][1]["valor"], 2)
        self.assertEqual(moju["estabelecimentos_com_equipamento_sus"][4]["valor"], 3)


if __name__ == "__main__":
    unittest.main()
