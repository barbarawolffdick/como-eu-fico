"""Testes sintéticos do validador; nenhum dado real é inventado."""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.validar_tse_2026 import FILES, run, write_evidence

VOTE_HEADER = "ANO_ELEICAO;NR_TURNO;TP_ABRANGENCIA;SG_UF;CD_MUNICIPIO;NR_ZONA;NR_SECAO;CD_CARGO;DS_CARGO;NR_VOTAVEL;QT_VOTOS;NR_LOCAL_VOTACAO"
DETAIL_HEADER = "ANO_ELEICAO;NR_TURNO;TP_ABRANGENCIA;SG_UF;CD_MUNICIPIO;NR_ZONA;NR_SECAO;CD_CARGO;DS_CARGO;QT_APTOS;QT_COMPARECIMENTO;QT_ABSTENCOES;QT_VOTOS_NOMINAIS;QT_VOTOS_BRANCOS;QT_VOTOS_NULOS;NR_LOCAL_VOTACAO"
VOTE_ROW = "2026;1;F;SP;123;2;3;1;Presidente;13;55;70"
DETAIL_ROW = "2026;1;F;SP;123;2;3;1;Presidente;100;80;20;70;5;5;70"

class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.resources = []

    def zipped(self, name, member, contents):
        path = self.root / name
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(member, contents.encode("latin-1"))
        self.resources.append({"download": {"file": str(path),
                                             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}})

    def finish(self):
        (self.root / "manifest.json").write_text(json.dumps({"resources": self.resources}))

    def make_files(self, duplicate=False):
        self.zipped(FILES["votos"], "votacao_secao_2026_BR.csv",
                    VOTE_HEADER + "\n" + VOTE_ROW + "\n")
        detail = DETAIL_HEADER + "\n" + DETAIL_ROW + "\n"
        if duplicate:
            detail += DETAIL_ROW + "\n"
        self.zipped(FILES["detalhe"], "detalhe_votacao_secao_2026_BRASIL.csv", detail)
        self.zipped(FILES["munzona"], "sample.csv", detail)
        self.finish()

    def test_fixture_valida_mantem_reconciliacao_inconclusiva(self):
        self.make_files()
        tests = run(self.root)
        self.assertFalse([t for t in tests if t["status"] == "FAIL"])
        self.assertEqual(next(t for t in tests if t["teste"] == "unicidade_detalhe")["status"], "PASS")
        self.assertEqual(next(t for t in tests if t["teste"] == "reconciliacao")["status"], "INCONCLUSIVO")

    def test_hash_modificado_eh_falha(self):
        self.make_files()
        with (self.root / FILES["votos"]).open("ab") as handle:
            handle.write(b"alterado")
        tests = run(self.root)
        self.assertEqual(next(t for t in tests if t["teste"] == "hash_votos")["status"], "FAIL")

    def test_exportacao_evidencia_individual(self):
        self.zipped(FILES["votos"], "votacao_secao_2026_BR.csv",
                    VOTE_HEADER + "\n" + VOTE_ROW + "\n")
        changed = DETAIL_ROW.replace(";100;80;20;70;", ";101;80;20;70;")
        self.zipped(FILES["detalhe"], "detalhe_votacao_secao_2026_BRASIL.csv",
                    DETAIL_HEADER + "\n" + changed + "\n")
        self.zipped(FILES["munzona"], "sample.csv", DETAIL_HEADER + "\n" + DETAIL_ROW + "\n")
        self.finish()
        evidence = []
        result = run(self.root, evidence=evidence)
        self.assertEqual(next(x for x in result if x["teste"] == "aritmetica_detalhe")["status"], "FAIL")
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["diferenca"], 1)
        self.assertEqual(evidence[0]["linha_csv"], 2)
        target = self.root / "evidencia.csv"
        write_evidence(target, evidence)
        with target.open(encoding="utf-8", newline="") as handle:
            records = list(__import__("csv").DictReader(handle))
        self.assertEqual(records[0]["QT_APTOS"], "101")
        self.assertEqual(records[0]["diferenca"], "1")

    def test_secao_duplicada_eh_falha(self):
        self.make_files(duplicate=True)
        tests = run(self.root)
        self.assertEqual(next(t for t in tests if t["teste"] == "unicidade_detalhe")["status"], "FAIL")

if __name__ == "__main__":
    unittest.main()
