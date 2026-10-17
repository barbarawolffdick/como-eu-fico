"""Controles do dinheiro federal na economia local (PIB, INSS, FPM), sem rede e sem openpyxl."""
import copy
import json
from pathlib import Path
import unittest

from scripts.publicar_dinheiro_federal import (
    ALIASES_FPM, centavos_planilha, consolidar_fpm, contem, escolher_abas_inss, extrair_aba_inss, extrair_pib,
    fpm_por_municipio, ler_fpm_csv, validar_publicacao,
)

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = json.loads((ROOT / "data/public/dinheiro_federal.json").read_text())
CADASTRO = {
    "2700102": {"nome": "Água Branca", "uf": "AL"}, "1100148": {"nome": "Nova Brasilândia D'Oeste", "uf": "RO"},
    "5101837": {"nome": "Boa Esperança do Norte", "uf": "MT"}, "2400208": {"nome": "Assú", "uf": "RN"},
    "2705903": {"nome": "Olho d'Água Grande", "uf": "AL"},
}
TITULO = ["Nome ", "Código IBGE", "UF", "Benefícios do Regime Geral de Previdência Social", None, None, None, None, None, None, None,
          "Benefícios assistenciais e de legislação específica", "Total"]
SUB1 = [None, None, None, "Aposentadorias", None, None, None, "Pensões por morte", "Auxílios", "Outros benefícios previdenciários",
        "Total de benefícios previdenciários", None, None]
SUB2 = [None, None, None, "Total de Aposentadorias", "Aposentadorias por idade", "Aposentadorias por invalidez",
        "Aposentadorias por tempo de contribuição", None, None, None, None, None, None]
# 10 grupos coerentes: aposentadorias = 6+3+1; previdenciário = 10+4+2+1; total = 17+3
GRUPOS = [10, 6, 3, 1, 4, 2, 1, 17, 3, 20]


def planilha(linhas, cabecalho=TITULO):
    return [[None] * 13, ["Quantidade de benefícios emitidos pelo INSS"] + [None] * 12, [None] * 13, [None] * 13,
            cabecalho, SUB1, SUB2] + linhas + [["Fontes: INSS / Síntese"] + [None] * 12, [1, "População judicial de X"] + [None] * 11]


def fpm_csv(linhas, mes="03"):
    corpo = "Município;UF;ANO;Mês;1º Decêndio;2º Decêndio;3º Decêndio;Item transferência;Transferência;\n"
    corpo += "".join(f"{n};{uf};2023;{mes};{a};{b};{c};{item};{transf};\n" for n, uf, a, b, c, item, transf in linhas)
    return corpo.encode("latin-1")


class PibTest(unittest.TestCase):
    def documento(self, valor):
        return [{"id": "37", "unidade": "Mil Reais", "resultados": [{"series": [
            {"localidade": {"id": "2700102"}, "serie": {"2023": "1046343"}},
            {"localidade": {"id": "5101837"}, "serie": {"2023": valor}}]}]}]

    def test_mil_reais_vira_centavos_e_nao_numerico_fica_nulo(self):
        pib = extrair_pib(self.documento("..."), 2023)
        self.assertEqual(pib["2700102"], 104_634_300_000)
        self.assertIsNone(pib["5101837"])

    def test_unidade_inesperada_interrompe(self):
        doc = self.documento("1")
        doc[0]["unidade"] = "Reais"
        with self.assertRaises(ValueError):
            extrair_pib(doc, 2023)


class InssTest(unittest.TestCase):
    def test_leiaute_antigo_com_codigo_na_primeira_coluna(self):
        cab = ["Cod. IBGE", "Nome "] + TITULO[2:]
        registros, val = extrair_aba_inss(planilha([["2700102", "Água Branca", "Alagoas", *GRUPOS]], cab), True, CADASTRO)
        self.assertEqual(registros["2700102"]["total"], 20)
        self.assertIsNone(val["conciliacao_brasil"])

    def test_coluna_do_codigo_vem_dos_dados_mesmo_com_rotulo_invertido(self):
        cab = ["Código IBGE", "Nome "] + TITULO[2:]  # clientela 2024: rótulo diz código, dado traz nome
        registros, _ = extrair_aba_inss(planilha([["Água Branca", 2700102, "AL", *GRUPOS]], cab), True, CADASTRO)
        self.assertIn("2700102", registros)

    def test_municipio_com_brasil_no_nome_nao_e_a_linha_de_total(self):
        linhas = [["Nova Brasilândia D'Oeste", 1100148, "RO", *GRUPOS], ["BRASIL", "#N/A", "#N/A", *GRUPOS]]
        registros, val = extrair_aba_inss(planilha(linhas), True, CADASTRO)
        self.assertIn("1100148", registros)
        self.assertEqual(val["conciliacao_brasil"], {"total_brasil": 20, "residuo_nao_alocado": 0})

    def test_linha_brasil_que_nao_concilia_interrompe(self):
        brasil = [*GRUPOS[:-1], 21]
        with self.assertRaises(ValueError):
            extrair_aba_inss(planilha([["Água Branca", 2700102, "AL", *GRUPOS], ["BRASIL", "#N/A", "#N/A", *brasil]]), True, CADASTRO)

    def test_soma_interna_inconsistente_interrompe(self):
        errado = list(GRUPOS)
        errado[1] = 7
        with self.assertRaises(ValueError):
            extrair_aba_inss(planilha([["Água Branca", 2700102, "AL", *errado]]), True, CADASTRO)

    def test_codigo_em_branco_so_por_nome_e_uf_identicos(self):
        registros, val = extrair_aba_inss(planilha([["Água Branca", 2700102, "AL", *GRUPOS],
                                                    ["Boa Esperança do Norte", " ", "MT", *GRUPOS]]), True, CADASTRO)
        self.assertIn("5101837", registros)
        self.assertEqual(val["codigos_por_nome_exato"][0]["codigo_ibge"], "5101837")
        with self.assertRaises(ValueError):
            extrair_aba_inss(planilha([["Água Branca", 2700102, "AL", *GRUPOS],
                                       ["Boa Esperanca Norte", " ", "MT", *GRUPOS]]), True, CADASTRO)

    def test_mudanca_de_leiaute_interrompe(self):
        sub1 = list(SUB1)
        sub1[7] = "Pensões"
        with self.assertRaises(ValueError):
            extrair_aba_inss([[None] * 13, TITULO, sub1, SUB2, ["Água Branca", 2700102, "AL", *GRUPOS]], True, CADASTRO)

    def test_ruido_de_ponto_flutuante_arredonda_e_fracao_real_recusa(self):
        self.assertEqual(centavos_planilha(37453268658.229996), 3_745_326_865_823)
        self.assertEqual(centavos_planilha("10.5"), 1050)
        with self.assertRaises(ValueError):
            centavos_planilha(1234.565)

    def test_abas_nos_tres_leiautes(self):
        self.assertEqual(escolher_abas_inss(["Quantidade - dez19", "Valor (R$) - dez19", "Valor (R$) - 2019"], 2019),
                         ("Quantidade - dez19", "Valor (R$) - 2019"))
        self.assertEqual(escolher_abas_inss(["Qtd_dez2025", "Valor_R$_dez25", "Valor_Médio_R$_dez24", "Valor_Total_2025"], 2025),
                         ("Qtd_dez2025", "Valor_Total_2025"))


class FpmTest(unittest.TestCase):
    BASE = [("Água Branca", "AL", "100.00", "50.00", "25.00", "FPM", "FPM"),
            ("Água Branca", "AL", "20.00", "10.00", "5.00", "FPM", "FUNDEB"),
            ("Água Branca", "AL", "999.00", "0", "0", "ICMS", "FUNDEB"),
            ("Açu", "RN", "10.00", "0", "0", "FPM", "FPM"),
            ("Olho D Água Grande", "AL", "1.00", "1.00", "1.00", "FPM", "FPM")]

    def ano(self, base=None, mes_alterado=None):
        arquivos = []
        for m in range(1, 13):
            mes = f"{m:02d}"
            linhas = base if mes == mes_alterado else self.BASE
            arquivos.append(({"url": f"u{mes}", "sha256": mes}, ler_fpm_csv(fpm_csv(linhas, mes))))
        return arquivos

    def test_mes_vem_do_conteudo_e_mistura_interrompe(self):
        (ano, mes), celulas = ler_fpm_csv(fpm_csv(self.BASE, "07"))
        self.assertEqual((ano, mes), ("2023", "07"))
        self.assertEqual(celulas[("Água Branca", "AL", "FPM", "FPM")], (10000, 5000, 2500))
        misturado = fpm_csv(self.BASE, "07") + "Açu;RN;2023;08;1;0;0;FPM;FPM;\n".encode("latin-1")
        with self.assertRaises(ValueError):
            ler_fpm_csv(misturado)

    def test_soma_so_fpm_creditado_e_usa_aliases_revisados(self):
        escolhidos, descartados = consolidar_fpm(self.ano(), 2023)
        fpm = fpm_por_municipio(escolhidos, CADASTRO)
        self.assertEqual(fpm["2700102"], 12 * 17500)  # sem FUNDEB nem ICMS
        self.assertEqual(fpm["2400208"], 12 * 1000)  # Açu → Assú
        self.assertEqual(fpm["2705903"], 12 * 300)  # apóstrofo
        self.assertEqual(descartados, [])
        self.assertEqual(ALIASES_FPM[("Açu", "RN")], "2400208")

    def test_versao_parcial_do_mes_e_descartada_e_registrada(self):
        parcial = [(n, uf, a, b, "0", i, t) for n, uf, a, b, _, i, t in self.BASE]
        arquivos = self.ano() + [({"url": "parcial", "sha256": "p"}, ler_fpm_csv(fpm_csv(parcial, "03")))]
        escolhidos, descartados = consolidar_fpm(arquivos, 2023)
        self.assertEqual(escolhidos["03"][0]["url"], "u03")
        self.assertEqual([d["url"] for d in descartados], ["parcial"])

    def test_versoes_divergentes_interrompem(self):
        divergente = [(n, uf, "1.00" if i == "FPM" and t == "FPM" else a, b, c, i, t) for n, uf, a, b, c, i, t in self.BASE]
        arquivos = self.ano() + [({"url": "x", "sha256": "x"}, ler_fpm_csv(fpm_csv(divergente, "03")))]
        with self.assertRaises(ValueError):
            consolidar_fpm(arquivos, 2023)

    def test_mes_ausente_interrompe(self):
        with self.assertRaises(ValueError):
            consolidar_fpm(self.ano()[:-1], 2023)

    def test_nome_sem_correspondencia_interrompe_sem_semelhanca(self):
        base = self.BASE + [("Agua Brnca", "AL", "1", "0", "0", "FPM", "FPM")]
        escolhidos, _ = consolidar_fpm(self.ano(base, "05"), 2023)
        with self.assertRaises(ValueError):
            fpm_por_municipio(escolhidos, CADASTRO)

    def test_contem_exige_valores_identicos_onde_ja_havia_valor(self):
        self.assertTrue(contem({"a": (1, 2, 3)}, {"a": (1, 2, 0)}))
        self.assertFalse(contem({"a": (1, 2, 3)}, {"a": (1, 9, 0)}))


class SnapshotTest(unittest.TestCase):
    def test_publicacao_cobre_o_cadastro_e_declara_ausencias(self):
        publicados = json.loads((ROOT / "data/public/rankings_2026.json").read_text())["registros"]
        validar_publicacao(SNAPSHOT, {r["codigo_ibge"]: {} for r in publicados})
        self.assertEqual(SNAPSHOT["cobertura"], {"pib": 5570, "inss": 5570, "fpm": 5569})
        self.assertEqual(set(SNAPSHOT["registros"]["2605459"]["ausencias"]), {"fpm"})  # Fernando de Noronha
        self.assertEqual(set(SNAPSHOT["registros"]["5101837"]["ausencias"]), {"pib", "inss", "fpm"})  # instalado em 2025

    def test_ausencia_sem_motivo_e_recusada(self):
        doc = copy.deepcopy(SNAPSHOT)
        doc["registros"]["2605459"]["ausencias"] = {}
        with self.assertRaises(ValueError):
            validar_publicacao(doc, {c: {} for c in doc["registros"]})

    def test_totais_conciliam_com_as_fontes(self):
        r = SNAPSHOT["registros"].values()
        inss = sum(x["inss"]["valor_ano_centavos"]["total"] for x in r if x["inss"])
        self.assertEqual(inss, SNAPSHOT["validacao"]["inss"]["valor_ano"]["conciliacao_brasil"]["total_brasil"])
        self.assertEqual(SNAPSHOT["validacao"]["inss"]["valor_ano"]["conciliacao_brasil"]["residuo_nao_alocado"], 0)
        self.assertEqual(sum(x["fpm"]["valor_ano_centavos"] for x in r if x["fpm"]), 15_204_387_551_999)
        self.assertEqual(sorted(SNAPSHOT["fontes"]["fpm"]["meses"]), [f"{m:02d}" for m in range(1, 13)])

    def test_fluxos_ficam_separados(self):
        exemplo = SNAPSHOT["registros"]["2307304"]
        self.assertEqual(set(exemplo), {"municipio", "regiao_imediata", "regiao", "pib_centavos", "inss", "fpm", "ausencias"})
        self.assertIn("órgão pagador", SNAPSHOT["definicoes"]["inss.valor_ano_centavos"])


if __name__ == "__main__":
    unittest.main()
