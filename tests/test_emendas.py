"""Emendas parlamentares por município, sem rede."""
import io
import json
from pathlib import Path
import unittest

from scripts.publicar_emendas import (
    COLUNAS, agregar, ano_da_emenda, eh_fundo_saude, ler_favorecidos, limpar_autor, limpar_favorecido,
    montar_documento, partido_na_data, valor,
)

ROOT = Path(__file__).resolve().parents[1]
CADASTRO = {"2307304": {"nome": "Juazeiro do Norte", "uf": "CE"}, "2400208": {"nome": "Assú", "uf": "RN"}}


def linha(**campos):
    base = {c: "" for c in COLUNAS} | {"Código da Emenda": "202512340001", "Tipo de Emenda": "Emenda Individual - Transferências Especiais",
                                         "Ano/Mês": "202503", "UF Favorecido": "CE", "Município Favorecido": "JUAZEIRO DO NORTE",
                                         "Favorecido": "FUNDO MUNICIPAL DE SAUDE DE JUAZEIRO DO NORTE", "Valor Recebido": "1.000,50",
                                         "Nome do Autor da Emenda": "FULANA DE TAL"}
    return base | campos


def csv_de(linhas):
    texto = ";".join(COLUNAS) + "\n" + "".join(";".join(l[c] for c in COLUNAS) + "\n" for l in linhas)
    return io.BytesIO(texto.encode("latin-1"))


class EmendasTest(unittest.TestCase):
    def test_valor_em_formato_brasileiro(self):
        self.assertEqual(valor("1.174.954,00"), 117495400)
        self.assertEqual(valor(""), 0)

    def test_so_linhas_do_ano_e_colunas_conferidas(self):
        linhas = list(ler_favorecidos(csv_de([linha(), linha(**{"Ano/Mês": "202412"})]), 2025))
        self.assertEqual(len(linhas), 1)
        with self.assertRaises(ValueError):
            list(ler_favorecidos(io.BytesIO("a;b\n1;2\n".encode("latin-1")), 2025))

    def test_limpezas(self):
        self.assertEqual(limpar_favorecido("1201FUNDO MUNICIPAL DE SAUDE"), "FUNDO MUNICIPAL DE SAUDE")
        self.assertEqual(limpar_favorecido(",FUNDO X"), "FUNDO X")
        self.assertEqual(limpar_autor("ALINE GURGEL (EX-PARLAMENTAR JOSE, NOS TERMOS ART. 78)"), "ALINE GURGEL")
        self.assertEqual(ano_da_emenda("202312340001"), 2023)
        self.assertIsNone(ano_da_emenda("Sem informação"))
        self.assertTrue(eh_fundo_saude("FUNDO MUNICIPAL DE SAÚDE DE X"))
        self.assertFalse(eh_fundo_saude("FUNDO MUNICIPAL DE ASSISTENCIA SOCIAL"))

    def test_agrega_por_autor_com_alias_e_sem_semelhanca(self):
        linhas = [linha(), linha(**{"Valor Recebido": "500,00", "Favorecido": "APAE"}),
                  linha(**{"UF Favorecido": "RN", "Município Favorecido": "AÇU"}),  # nome antigo revisado
                  linha(**{"Município Favorecido": "JUAZEIRO"}),  # não vira Juazeiro do Norte
                  linha(**{"Município Favorecido": ""})]
        por_cidade, validacao = agregar(linhas, CADASTRO)
        a = por_cidade["2307304"]["FULANA DE TAL"]
        self.assertEqual((a["valor_centavos"], a["saude_centavos"], a["tipo"]), (150050, 100050, "Emenda Individual"))
        self.assertIn("2400208", por_cidade)
        self.assertEqual(validacao["linhas_sem_municipio"], 1)
        self.assertEqual(validacao["municipios_sem_correspondencia"], {"JUAZEIRO-CE": 100050})

    def test_partido_da_epoca(self):
        filiacoes = [("2019-02-01T10:00", "PDT"), ("2024-04-05T10:00", "PSB")]
        self.assertEqual(partido_na_data(filiacoes, 2023), "PDT")
        self.assertEqual(partido_na_data(filiacoes, 9999), "PSB")
        self.assertIsNone(partido_na_data(filiacoes, 2018))

    def test_bancada_sem_partido_e_mudanca_registrada(self):
        por_cidade, validacao = agregar([linha(**{"Código da Emenda": "202312340001"}),
                                         linha(**{"Nome do Autor da Emenda": "BANCADA DO CEARA", "Tipo de Emenda": "Emenda de Bancada"})], CADASTRO)
        partidos = {"FULANA DE TAL": {"filiacoes": [("2019-02-01", "PDT"), ("2024-04-05", "PSB")], "casa": "Câmara"},
                    "BANCADA DO CEARA": {"filiacoes": [("2019-02-01", "PT")], "casa": "Câmara"}}
        doc = montar_documento(2025, CADASTRO, por_cidade, partidos, validacao, {})
        autores = {a["autor"]: a for a in doc["registros"]["2307304"]["autores"]}
        self.assertEqual((autores["FULANA DE TAL"]["partido"], autores["FULANA DE TAL"]["partido_atual"]), ("PDT", "PSB"))
        self.assertIsNone(autores["BANCADA DO CEARA"]["partido"])
        self.assertNotIn("2400208", doc["registros"])  # sem emenda: ausente, não zero

    def test_juazeiro_confere_com_o_fundo_nacional_de_saude(self):
        doc = json.loads((ROOT / "data/public/emendas_2025.json").read_text())
        r = doc["registros"]["2307304"]
        self.assertEqual(r["saude_centavos"], 255719200)
        self.assertEqual(r["total_centavos"], sum(a["valor_centavos"] for a in r["autores"]))
        fernanda = next(a for a in r["autores"] if a["autor"] == "FERNANDA PESSOA")
        self.assertEqual((fernanda["partido"], fernanda["partido_atual"]), ("União", "PSD"))


if __name__ == "__main__":
    unittest.main()
