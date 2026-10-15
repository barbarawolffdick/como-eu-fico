"""Regressões da ausência cartográfica e do período incorreto do mapa MDS."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from scripts.complementar_pessoas_mds import AUSENCIAS_MAPA, CAMPOS, completar, extrair

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests/fixtures/pessoas_mds_tabular.json").read_text())
PUBLICADO = json.loads((ROOT / "data/public/pessoas_mds.json").read_text())
CADASTRO = {r["codigo_ibge"]: r for r in json.loads((ROOT / "data/public/rankings_2026.json").read_text())["registros"]}


def html(codigo):
    return ("<script>var strJsondados = '" + json.dumps(FIXTURE["consultas"][codigo]["linhas"], ensure_ascii=False) + "';</script>").encode()


def consultas():
    return {c: (html(c), {"url": PUBLICADO["pagina_fonte"] + (f"&ag=m&codigo={c}" if c else ""),
                         "sha256": hashlib.sha256(html(c)).hexdigest()}) for c in FIXTURE["consultas"]}


class ComplementoMDSTests(unittest.TestCase):
    def base(self):
        d = deepcopy(PUBLICADO)
        d["periodo"] = "202608"
        for c in AUSENCIAS_MAPA:
            d["registros"][c].update(pessoas=None, cobertura_pct=None)
        d["municipios_com_dado"] = 5565
        d["municipios_sem_dado"] = list(AUSENCIAS_MAPA)
        return d

    def test_periodos_reais_distintos_na_mesma_serie(self):
        self.assertEqual(extrair(html("3550308"), "3550308", CADASTRO["3550308"], "202608")["pessoas"], 1650898)
        self.assertEqual(extrair(html("3550308"), "3550308", CADASTRO["3550308"])["pessoas"], 1652769)

    def test_seis_complementos_fecham_nacional_e_preservam_demais(self):
        base = self.base()
        final = completar(base, CADASTRO, consultas(), corrigir_periodo=True)
        self.assertEqual(final["municipios_com_dado"], 5571)
        self.assertEqual(final["municipios_sem_dado"], [])
        self.assertEqual(final["periodo"], "202609")
        self.assertEqual(final["complemento_tabular"]["validacao"]["total_pessoas"], 49645630)
        for c, r in base["registros"].items():
            if c not in AUSENCIAS_MAPA:
                self.assertEqual(final["registros"][c], r)
        self.assertIsNone(base["registros"]["1504752"]["pessoas"])

    def test_correcao_de_periodo_exige_opcao_explicita(self):
        with self.assertRaisesRegex(ValueError, "Período"):
            completar(self.base(), CADASTRO, consultas())

    def test_identidade_e_competencia_nao_podem_ser_trocadas(self):
        for c, cadastro, periodo in [("4212650", CADASTRO["4212650"], "202609"),
                                     ("1504752", CADASTRO["4212650"], "202609"),
                                     ("1504752", CADASTRO["1504752"], "202607")]:
            with self.subTest(c=c, periodo=periodo), self.assertRaises(ValueError):
                extrair(html("1504752"), c, cadastro, periodo)

    def test_faixa_ausente_e_duplicidade_bloqueiam(self):
        linhas = deepcopy(FIXTURE["consultas"]["1504752"]["linhas"])
        for valor in (None, -1, 1.5, True):
            linhas[-1][CAMPOS[0]] = valor
            bruto = ("var strJsondados = '" + json.dumps(linhas) + "';").encode()
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                extrair(bruto, "1504752", CADASTRO["1504752"])
        with self.assertRaises(ValueError):
            extrair(html("1504752") * 2, "1504752", CADASTRO["1504752"])

    def test_mistura_temporal_e_total_divergente_bloqueiam(self):
        d = self.base()
        d["registros"]["3550308"]["pessoas"] = 1650898  # agosto, não setembro
        with self.assertRaisesRegex(ValueError, "controle"):
            completar(d, CADASTRO, consultas(), True)
        d = self.base()
        d["proveniencia"][0]["total_na_resposta"] += 1
        with self.assertRaisesRegex(ValueError, "três faixas"):
            completar(d, CADASTRO, consultas(), True)

    def test_hash_corrompido_bloqueia(self):
        fontes = consultas()
        fontes[""][1]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Hash"):
            completar(self.base(), CADASTRO, fontes, True)

    def test_coberturas_das_seis_cidades_preservam_denominador(self):
        for c in AUSENCIAS_MAPA:
            r = PUBLICADO["registros"][c]
            self.assertEqual(r["populacao"], CADASTRO[c]["populacao"])
            self.assertEqual(r["cobertura_pct"], round(100 * r["pessoas"] / r["populacao"], 4))
            self.assertGreater(r["pessoas"], 0)


if __name__ == "__main__":
    unittest.main()
