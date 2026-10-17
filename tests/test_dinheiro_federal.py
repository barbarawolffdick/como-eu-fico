"""Controles do dinheiro federal na economia local (PIB, INSS, FPM), sem rede e sem openpyxl."""
import copy
from decimal import Decimal
import json
from pathlib import Path
import unittest

from scripts.publicar_dinheiro_federal import (
    ALIASES_FPM, FpmIncompleto, centavos_planilha, consolidar_fpm, contem, escolher_abas_inss, estimar_pib, extrair_aba_inss,
    extrair_pib, fpm_por_municipio, ler_fpm_csv, montar_documento, pib_nacional_anual, urls_fpm, validar_publicacao, valor_fpm,
)

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = json.loads((ROOT / "data/public/dinheiro_federal.json").read_text())
SNAPSHOT_2025 = json.loads((ROOT / "data/public/dinheiro_federal_2025.json").read_text())
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


def fpm_csv(linhas, mes="03", coluna_ano="ANO"):
    corpo = f"Município;UF;{coluna_ano};Mês;1º Decêndio;2º Decêndio;3º Decêndio;Item transferência;Transferência;\n"
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

    def test_ruido_de_soma_em_ponto_flutuante_e_relativo_ao_valor(self):
        # INSS 2019, São Paulo: célula de R$ 47,8 bilhões com 0,096 centavo de ruído (somas feitas pela fonte).
        self.assertEqual(centavos_planilha(47784604809.59096), 4_778_460_480_959)
        # O mesmo ruído absoluto num valor de R$ 1 milhão não é ruído de ponto flutuante: recusa.
        with self.assertRaises(ValueError):
            centavos_planilha(1000000.0002)

    def test_linha_de_total_sem_rotulo_concilia(self):
        # 2019–2022: "Total" na coluna do código e nome vazio; também aceita linha sem rótulo algum.
        cab = ["Cod. IBGE", "Nome "] + TITULO[2:]
        for rotulo in ("Total", None):
            registros, val = extrair_aba_inss(planilha([[2700102, "Água Branca", "Alagoas", *GRUPOS],
                                                        [rotulo, None, None, *GRUPOS]], cab), True, CADASTRO)
            self.assertEqual(set(registros), {"2700102"})
            self.assertEqual(val["conciliacao_brasil"], {"total_brasil": 20, "residuo_nao_alocado": 0})

    def test_total_sem_rotulo_que_nao_concilia_ou_repetido_interrompe(self):
        cab = ["Cod. IBGE", "Nome "] + TITULO[2:]
        mun = [2700102, "Água Branca", "Alagoas", *GRUPOS]
        with self.assertRaises(ValueError):
            extrair_aba_inss(planilha([mun, ["Total", None, None, *GRUPOS[:-1], 21]], cab), True, CADASTRO)
        with self.assertRaises(ValueError):
            extrair_aba_inss(planilha([mun, ["Total", None, None, *GRUPOS], [None, None, None, *GRUPOS]], cab), True, CADASTRO)

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


class FpmAnosTest(unittest.TestCase):
    """Defeitos da série 2019–2025 do Tesouro (levantados em 17/10/2026)."""
    BASE = FpmTest.BASE

    def arquivos(self, por_mes=None):
        por_mes = por_mes or {}
        return [({"url": f"u{m:02d}", "sha256": f"{m:02d}"}, ler_fpm_csv(fpm_csv(por_mes.get(f"{m:02d}", self.BASE), f"{m:02d}")))
                for m in range(1, 13)]

    def test_cabecalho_com_ano_minusculo_e_mes_sem_zero(self):
        # 2021-08: "Ano" no cabeçalho e mês "8".
        (ano, mes), celulas = ler_fpm_csv(fpm_csv(self.BASE, "8", coluna_ano="Ano"))
        self.assertEqual((ano, mes), ("2023", "08"))
        self.assertEqual(celulas[("Água Branca", "AL", "FPM", "FPM")], (10000, 5000, 2500))

    def test_formato_misto_de_2021_08(self):
        formatos = set()
        self.assertEqual(valor_fpm(" 509914.99 ", formatos), 50_991_499)
        self.assertEqual(valor_fpm(" 1.234.567,89 ", formatos), 123_456_789)
        self.assertEqual(valor_fpm(" 99,5 ", formatos), 9_950)
        self.assertEqual(valor_fpm(" -   ", formatos), 0)
        self.assertEqual(formatos, {"ponto_decimal", "virgula_decimal", "traco_zero"})
        for ambiguo in ("1.234", "12.345.678", "1,234.56", "R$ 10", "1.5e3"):
            with self.assertRaises(ValueError, msg=ambiguo):
                valor_fpm(ambiguo, set())

    def test_mes_com_terceiro_decendio_zerado_e_recusado(self):
        # 2019-09, 2024-01/02/08/10/11: o Tesouro publicou o mês antes do último crédito e nunca substituiu.
        parcial = [(n, uf, a, b, "0", i, t) for n, uf, a, b, _, i, t in self.BASE]
        with self.assertRaises(FpmIncompleto) as erro:
            consolidar_fpm(self.arquivos({"09": parcial}), 2023)
        self.assertEqual(list(erro.exception.problemas), ["09"])
        self.assertIn("3º decêndio", erro.exception.problemas["09"])

    def test_versao_completa_encadeada_supera_a_parcial(self):
        parcial = [(n, uf, a, b, "0", i, t) for n, uf, a, b, _, i, t in self.BASE]
        arquivos = [({"url": "parcial", "sha256": "p"}, ler_fpm_csv(fpm_csv(parcial, "09")))] + self.arquivos()
        escolhidos, descartados = consolidar_fpm(arquivos, 2023)
        self.assertEqual(escolhidos["09"][0]["url"], "u09")
        self.assertEqual([d["url"] for d in descartados], ["parcial"])

    def test_mes_sem_credito_de_fpm_e_recusado(self):
        # 2019-10: arquivo com outras transferências, mas nenhum FPM/FPM.
        sem_fpm = [linha for linha in self.BASE if (linha[5], linha[6]) != ("FPM", "FPM")]
        with self.assertRaises(FpmIncompleto) as erro:
            consolidar_fpm(self.arquivos({"10": sem_fpm}), 2023)
        self.assertEqual(list(erro.exception.problemas), ["10"])

    def test_valores_sem_ponto_decimal_sao_recusados_e_nunca_reescalados(self):
        # 2024-09: 726048468 significando 7260484.68. O mês é recusado; nada é dividido por 100.
        sem_ponto = [(n, uf, *(str(int(float(x) * 100)) for x in (a, b, c)), i, t) for n, uf, a, b, c, i, t in self.BASE]
        with self.assertRaises(FpmIncompleto) as erro:
            consolidar_fpm(self.arquivos({"09": sem_ponto}), 2023)
        self.assertEqual(list(erro.exception.problemas), ["09"])
        self.assertIn("100.00×", erro.exception.problemas["09"])

    def test_variacao_legitima_entre_meses_passa(self):
        dobro = [(n, uf, *(f"{float(x) * 2:.2f}" for x in (a, b, c)), i, t) for n, uf, a, b, c, i, t in self.BASE]
        escolhidos, _ = consolidar_fpm(self.arquivos({"12": dobro}), 2023)
        self.assertEqual(len(escolhidos), 12)

    def test_relatorio_lista_todos_os_meses_recusados(self):
        # 2022-10 ausente e 2021-08 ilegível viram "mês ausente"; todos os problemas saem juntos.
        parcial = [(n, uf, a, b, "0", i, t) for n, uf, a, b, _, i, t in self.BASE]
        arquivos = [a for a in self.arquivos({"02": parcial}) if a[1][0][1] != "10"]
        with self.assertRaises(FpmIncompleto) as erro:
            consolidar_fpm(arquivos, 2023)
        self.assertEqual(sorted(erro.exception.problemas), ["02", "10"])
        self.assertIn("2023-10: mês ausente", str(erro.exception))

    def test_arquivos_do_ano_seguinte_entram_porque_o_nome_pode_adiantar_o_mes(self):
        base = "https://x/transferenciamensalmunicipios"
        catalogo = {"result": {"resources": [{"url": f"{base}{n}.csv"} for n in ("202412", "202501", "202512", "202601", "202602", "202603")]}}
        self.assertEqual([u[-10:-4] for u in urls_fpm(catalogo, 2025)], ["202501", "202512", "202601", "202602"])


def documento_trimestral(serie):
    return [{"id": "585", "unidade": "Milhões de Reais", "resultados": [{
        "classificacoes": [{"id": "11255", "nome": "Setores e subsetores", "categoria": {"90707": "PIB a preços de mercado"}}],
        "series": [{"localidade": {"id": "1"}, "serie": serie}]}]}]


class PibEstimadoTest(unittest.TestCase):
    SERIE = {"202301": "2581018", "202302": "2727580", "202303": "2769445", "202304": "2865301",
             "202501": "3024723", "202502": "3200345", "202503": "3235708", "202504": "3277790"}

    def test_ano_sem_pib_municipal_publicado_interrompe_com_instrucao(self):
        with self.assertRaisesRegex(ValueError, "--pib estimado"):
            extrair_pib([], 2025)

    def test_fator_vem_das_contas_trimestrais(self):
        doc = documento_trimestral(self.SERIE)
        self.assertEqual(pib_nacional_anual(doc, 2023), Decimal("10943344"))
        nacional_base, nacional_ano = pib_nacional_anual(doc, 2023), pib_nacional_anual(doc, 2025)
        # Base municipal que soma o PIB nacional de 2023 (em centavos), com um município sem PIB.
        base = {"2700102": 1_094_334_400_000_000 - 104_634_300_000, "1100148": 104_634_300_000, "5101837": None}
        estimado, fator = estimar_pib(base, nacional_base, nacional_ano)
        self.assertEqual(fator, Decimal("1.164047"))
        self.assertEqual(estimado["1100148"], 121_799_200_000)  # 1.046.343 mil × 1,164047, arredondado a mil reais
        self.assertIsNone(estimado["5101837"])

    def test_trimestre_faltando_ou_base_incoerente_interrompe(self):
        serie = dict(self.SERIE)
        del serie["202504"]
        with self.assertRaises(ValueError):
            pib_nacional_anual(documento_trimestral(serie), 2025)
        with self.assertRaises(ValueError):  # base municipal em mil reais em vez de centavos
            estimar_pib({"2700102": 10_943_344_000}, Decimal("10943344"), Decimal("12738566"))

    def cadastro(self):
        return {c: {**m, "regiao": "R", "regiao_imediata": {"id": "1", "nome": "X"}} for c, m in CADASTRO.items()}

    def test_estimativa_fica_em_campo_proprio_e_rotulado(self):
        cadastro = self.cadastro()
        referencia = {"natureza": "estimado", "ano": 2025, "ano_base": 2023, "fator": "1.164047"}
        estimado = {c: 100_000 for c in cadastro} | {"5101837": None}
        doc = montar_documento(2025, cadastro, {}, {}, {}, {}, {}, {}, referencia, estimado)
        validar_publicacao(doc, cadastro)
        r = doc["registros"]["2700102"]
        self.assertIsNone(r["pib_centavos"])
        self.assertEqual(r["pib_estimado_centavos"], 100_000)
        self.assertIn("estimativa", r["ausencias"]["pib"])
        self.assertIn("ESTIMATIVA", doc["definicoes"]["pib_estimado_centavos"])
        self.assertEqual(doc["natureza"], "fluxos observados; PIB estimado")
        self.assertIn("não há estimativa", doc["registros"]["5101837"]["ausencias"]["pib"])

    def test_estimativa_nao_se_disfarca_de_observado(self):
        cadastro = self.cadastro()
        referencia = {"natureza": "estimado", "ano": 2025, "ano_base": 2023, "fator": "1.164047"}
        doc = montar_documento(2025, cadastro, {}, {}, {}, {}, {}, {}, referencia, {c: 100_000 for c in cadastro})
        misturado = copy.deepcopy(doc)
        misturado["registros"]["2700102"]["pib_centavos"] = 100_000
        del misturado["registros"]["2700102"]["ausencias"]["pib"]
        misturado["cobertura"]["pib"] = 1
        with self.assertRaises(ValueError):
            validar_publicacao(misturado, cadastro)
        observado = montar_documento(2023, cadastro, {c: 1 for c in cadastro}, {}, {}, {}, {}, {})
        observado["registros"]["2700102"]["pib_estimado_centavos"] = 1
        with self.assertRaises(ValueError):
            validar_publicacao(observado, cadastro)


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
        self.assertEqual(SNAPSHOT["pib_referencia"], {"natureza": "observado", "ano": 2023})


class Snapshot2025Test(unittest.TestCase):
    def test_fluxos_de_2025_completos_e_pib_rotulado_como_estimativa(self):
        publicados = json.loads((ROOT / "data/public/rankings_2026.json").read_text())["registros"]
        validar_publicacao(SNAPSHOT_2025, {r["codigo_ibge"]: {} for r in publicados})
        self.assertEqual(SNAPSHOT_2025["ano"], 2025)
        self.assertEqual(SNAPSHOT_2025["cobertura"], {"pib": 0, "inss": 5571, "fpm": 5570, "pib_estimado": 5570})
        ref = SNAPSHOT_2025["pib_referencia"]
        self.assertEqual((ref["natureza"], ref["ano_base"], ref["fator"]), ("estimado", 2023, "1.164047"))
        self.assertTrue(all(r["pib_centavos"] is None and "pib" in r["ausencias"] for r in SNAPSHOT_2025["registros"].values()))
        self.assertEqual(sorted(SNAPSHOT_2025["fontes"]["fpm"]["meses"]), [f"{m:02d}" for m in range(1, 13)])

    def test_municipio_instalado_em_2025_tem_fluxos_mas_nao_pib(self):
        r = SNAPSHOT_2025["registros"]["5101837"]
        self.assertIsNotNone(r["inss"])
        self.assertIsNotNone(r["fpm"])
        self.assertIsNone(r["pib_estimado_centavos"])
        self.assertEqual(set(r["ausencias"]), {"pib"})

    def test_estimativa_preserva_o_pib_de_2023_vezes_o_fator(self):
        for codigo in ("3550308", "2307304"):
            base = SNAPSHOT["registros"][codigo]["pib_centavos"]
            esperado = int((Decimal(base) * Decimal("1.164047") / 100_000).quantize(Decimal(1))) * 100_000
            self.assertEqual(SNAPSHOT_2025["registros"][codigo]["pib_estimado_centavos"], esperado)


if __name__ == "__main__":
    unittest.main()
