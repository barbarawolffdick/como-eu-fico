"""Confere regras para votos válidos usando apenas dados sintéticos."""
import unittest
import zipfile
from tests.test_reconciliar_8_municipios import ReconciliaTest
from scripts.conferir_validos_8_municipios import verify

class ValidVotesTests(ReconciliaTest):
    def test_sem_categorias_nao_certifica_votos_validos(self):
        checks=verify(self.tse)
        self.assertTrue(all(result["status"]=="INCONCLUSIVO" for result in checks.values()))
        self.assertTrue(all(result["votos_validos"] is None for result in checks.values()))

    def test_compativel_em_cada_secao(self):
        path=self.tse/"votacao_secao_2026_BR.zip"
        with zipfile.ZipFile(path) as z:
            lines=z.read("votacao_secao_2026_BR.csv").decode().splitlines()
        augmented=[lines[0]]
        for line in lines[1:]:
            augmented.append(line)
            if ";22;FLAVIO BOLSONARO;" in line:
                prefix=line.rsplit(";",3)[0]
                augmented.extend([prefix+";55;OUTRO CANDIDATO;7",
                                  prefix+";95;VOTO BRANCO;5",
                                  prefix+";96;VOTO NULO;5"])
        path.unlink()
        with zipfile.ZipFile(path,"w") as z:
            z.writestr("votacao_secao_2026_BR.csv","\n".join(augmented)+"\n")
        detail=self.tse/"detalhe_votacao_secao_2026.zip"
        with zipfile.ZipFile(detail) as z:
            content=z.read("detalhe_votacao_secao_2026_BRASIL.csv").decode()
        content=content.replace("QT_ABSTENCOES\n", "QT_ABSTENCOES;QT_VOTOS_BRANCOS;QT_VOTOS_NULOS;QT_VOTOS_LEGENDA;QT_VOTOS_ANULADOS_APU_SEP\n")
        content=content.replace(";40;50;10\n", ";40;50;10;5;5;0;0\n")
        detail.unlink()
        with zipfile.ZipFile(detail,"w") as z:
            z.writestr("detalhe_votacao_secao_2026_BRASIL.csv",content)
        checks=verify(self.tse)
        self.assertTrue(all(result["status"]=="PASS" for result in checks.values()))
        self.assertTrue(all(result["votos_validos"]==40 for result in checks.values()))

if __name__=="__main__":
    unittest.main()
