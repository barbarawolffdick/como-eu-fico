"""Controles nacionais com amostras agregadas oficiais, sem chamadas de rede."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.publicar_saude_nacional import (
    cobertura, extrair_pmmb_nacional, indexar_aps, validar_publicacao,
)
from scripts.publicar_saude_piloto import obter

ROOT = Path(__file__).resolve().parents[1]
CADASTRO = {r["codigo_ibge"]: r for r in json.loads((ROOT / "data/public/rankings_2026.json").read_text())["registros"]}
AMOSTRA = json.loads((ROOT / "tests/fixtures/saude_nacional.json").read_text())
PILOTO = json.loads((ROOT / "tests/fixtures/saude_piloto.json").read_text())
SNAPSHOT = json.loads((ROOT / "data/public/saude_municipal.json").read_text())


class SaudeNacionalTest(unittest.TestCase):
    def test_mais_medicos_exclui_estadual_e_dsei_sem_ratear(self):
        registros, validacao = extrair_pmmb_nacional(AMOSTRA["linhas_pmmb"], CADASTRO)
        self.assertEqual(registros["3550308"]["ultimo"]["vagas_ocupadas"], 163)
        self.assertEqual(validacao["linhas_municipais"], 2)
        self.assertEqual({x["nivel"] for x in validacao["registros_nao_municipais_separados"]}, {"DSEI", "ESTADUAL"})

    def test_zero_explicito_difere_de_linha_ausente(self):
        registros, _ = extrair_pmmb_nacional(AMOSTRA["linhas_pmmb"], CADASTRO)
        self.assertEqual(registros["5101837"]["ultimo"]["vagas_ocupadas"], 0)
        self.assertIsNone(registros["2611606"]["ultimo"])
        self.assertIn("Ausência não é zero", registros["2611606"]["motivo"])

    def test_valor_vazio_nao_vira_zero(self):
        linhas = copy.deepcopy(AMOSTRA["linhas_pmmb"])
        for _, r in linhas:
            if r["nivel"] == "MUNICIPAL":
                r["total_ocupadas"] = ""
        registros, _ = extrair_pmmb_nacional(linhas, CADASTRO)
        self.assertIsNone(registros["3550308"]["ultimo"]["vagas_ocupadas"])

    def test_duplicata_municipal_interrompe_publicacao(self):
        linhas = AMOSTRA["linhas_pmmb"]
        municipal = next(x for x in linhas if x[1]["nivel"] == "MUNICIPAL")
        with self.assertRaisesRegex(ValueError, "duplicado"):
            extrair_pmmb_nacional(linhas + [municipal], CADASTRO)

    def test_codigo_ou_uf_inconsistente_interrompe_publicacao(self):
        for campo, valor in (("co_ibge", "999999"), ("uf", "XX"), ("nivel", "REGIONAL")):
            linhas = copy.deepcopy(AMOSTRA["linhas_pmmb"])
            next(r for _, r in linhas if r["nivel"] == "MUNICIPAL")[campo] = valor
            with self.subTest(campo=campo), self.assertRaises(ValueError):
                extrair_pmmb_nacional(linhas, CADASTRO)

    def test_datas_mistas_nao_fingem_periodo_equivalente(self):
        linhas = copy.deepcopy(AMOSTRA["linhas_pmmb"])
        next(r for _, r in linhas if r["nivel"] == "MUNICIPAL")["dt_referencia"] = "2026-10-08"
        with self.assertRaisesRegex(ValueError, "mistura referências"):
            extrair_pmmb_nacional(linhas, CADASTRO)

    def test_aps_nacional_nao_soma_processos_municipais(self):
        doc = copy.deepcopy(PILOTO["aps"])
        doc["pagamentos"] += copy.deepcopy(doc["pagamentos"])
        with self.assertRaisesRegex(ValueError, "múltiplos processos"):
            indexar_aps(doc, CADASTRO, "202610")

    def test_aps_ausente_nao_vira_equipe_zero(self):
        registros = indexar_aps(PILOTO["aps"], CADASTRO, "202610")
        self.assertIsNone(registros["5101837"])
        self.assertEqual(registros["3550308"]["competencia_cnes"], "202608")

    def test_cache_corrompido_nao_e_usado_nem_rebaixado_a_ausencia(self):
        import hashlib
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            url = "https://apidadosabertos.saude.gov.br/exemplo-nao-consultado"
            chave = hashlib.sha256(url.encode()).hexdigest()
            (path / f"{chave}.raw").write_bytes(b"corrompido")
            (path / f"{chave}.json").write_text(json.dumps({"url": url, "sha256": "0" * 64}))
            with self.assertRaisesRegex(ValueError, "corrompido"):
                obter(url, path)

    def test_snapshot_cobre_cadastro_e_confere_totais(self):
        validar_publicacao(SNAPSHOT, CADASTRO)
        self.assertEqual(SNAPSHOT["status"], "NACIONAL")
        self.assertEqual(SNAPSHOT["natureza"], "observado")
        self.assertEqual(len(SNAPSHOT["registros"]), 5571)
        self.assertEqual(SNAPSHOT["cobertura"], cobertura(SNAPSHOT["registros"]))
        self.assertEqual(SNAPSHOT["cobertura"]["fns"], {"com_dado": 5569, "sem_dado": ["2605459", "5300108"]})
        self.assertEqual(SNAPSHOT["cobertura"]["aps"]["com_dado"], 5571)
        self.assertEqual(SNAPSHOT["cobertura"]["mais_medicos"]["com_dado"], 5571)
        self.assertEqual(SNAPSHOT["validacao"]["fns"]["linhas_aps_na_fonte"], 59447)
        self.assertEqual(SNAPSHOT["validacao"]["mais_medicos"]["linhas_na_fonte"], 5631)
        for codigo, r in SNAPSHOT["registros"].items():
            self.assertEqual(r["municipio"]["codigo_ibge"], codigo)
            self.assertEqual(r["aps"]["parcela"], "202610")
            self.assertEqual(r["aps"]["competencia_cnes"], "202608")
            self.assertEqual(r["mais_medicos"]["ultimo"]["data_referencia"], "2026-10-09")
            self.assertGreater(r["mais_medicos"]["ultimo"]["linha_origem"], 1)

    def test_fns_e_aps_preservam_resultados_do_piloto(self):
        anterior = json.loads((ROOT / "data/public/saude_piloto.json").read_text())
        for codigo, antigo in anterior["registros"].items():
            novo = SNAPSHOT["registros"][codigo]
            self.assertEqual(novo["fns"], antigo["fns"])
            self.assertEqual(novo["aps"], antigo["aps"])

    def test_publicacao_incompleta_ou_cobertura_incorreta_e_rejeitada(self):
        documento = {**SNAPSHOT, "registros": dict(SNAPSHOT["registros"])}
        documento["registros"].pop("3550308")
        with self.assertRaisesRegex(ValueError, "todo o cadastro"):
            validar_publicacao(documento, CADASTRO)
        with self.assertRaisesRegex(ValueError, "Cobertura declarada"):
            validar_publicacao({**SNAPSHOT, "cobertura": {}}, CADASTRO)


if __name__ == "__main__":
    unittest.main()
