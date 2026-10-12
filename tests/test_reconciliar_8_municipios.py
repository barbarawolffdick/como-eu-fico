import csv
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.reconciliar_8_municipios import TARGETS, reconcile, norm

VHEAD = "ANO_ELEICAO;NR_TURNO;TP_ABRANGENCIA;SG_UF;NM_MUNICIPIO;CD_MUNICIPIO;NR_ZONA;NR_SECAO;DS_CARGO;NR_VOTAVEL;NM_VOTAVEL;QT_VOTOS"
DHEAD = "ANO_ELEICAO;NR_TURNO;TP_ABRANGENCIA;SG_UF;NM_MUNICIPIO;CD_MUNICIPIO;NR_ZONA;NR_SECAO;DS_CARGO;QT_VOTOS_NOMINAIS;QT_COMPARECIMENTO;QT_ABSTENCOES"
ISSUES = ["uf", "municipio_origem", "codigo_ibge", "regra"]
PROCESSED = ["uf","municipio_origem","codigo_ibge","votos_lula","votos_flavio","votos_validos","arquivo_origem","linha_origem"]

def csvfile(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer=csv.DictWriter(file,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

class ReconciliaTest(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.issues=self.root/"quality"/"inconsistencias_eleitorais.csv"
        self.tse=self.root/"raw"
        self.tse.mkdir()
        originals=[]
        processed=[]
        votes=[VHEAD]
        details=[DHEAD]
        for number,(uf,mun) in enumerate(sorted(TARGETS),1):
            ibge=str(1000000+number)
            originals.append(dict(uf=uf,municipio_origem=mun,codigo_ibge=ibge,regra="votos_candidatos"))
            processed.append(dict(uf=uf,municipio_origem=mun,codigo_ibge=ibge,votos_lula="10",votos_flavio="20",votos_validos="20",arquivo_origem="f.csv",linha_origem=str(number+1)))
            prefix=f"2026;1;F;{uf};{mun};{number};1;1;Presidente"
            votes.append(prefix+";13;LUIZ INACIO LULA DA SILVA;12")
            votes.append(prefix+";22;FLAVIO BOLSONARO;21")
            details.append(prefix+";40;50;10")
        csvfile(self.issues,ISSUES,originals)
        csvfile(self.root/"processed"/"eleicoes_2026_municipios.csv",PROCESSED,processed)
        with zipfile.ZipFile(self.tse/"votacao_secao_2026_BR.zip","w") as z:
            z.writestr("votacao_secao_2026_BR.csv","\n".join(votes)+"\n")
        with zipfile.ZipFile(self.tse/"detalhe_votacao_secao_2026.zip","w") as z:
            z.writestr("detalhe_votacao_secao_2026_BRASIL.csv","\n".join(details)+"\n")

    def test_compara_oito_sem_concluir_validos(self):
        rows,_=reconcile(self.issues,self.tse)
        self.assertEqual(len(rows),8)
        self.assertTrue(all(x["dif_lula"]==2 for x in rows))
        self.assertTrue(all(x["dif_flavio"]==1 for x in rows))
        self.assertTrue(all(x["tse_votos_validos"]=="" for x in rows))
        self.assertTrue(all(x["status"]=="INCONCLUSIVO" for x in rows))

    def test_nome_flavio_no_tse_2026(self):
        from scripts.reconciliar_8_municipios import classify
        self.assertEqual(classify("FLAVIO NANTES BOLSONARO"), "flavio")
        self.assertEqual(classify("FLAVIO BOLSONARO"), "flavio")
        self.assertIsNone(classify("OUTRO CANDIDATO"))

    def test_nao_aceita_selecao_incompleta(self):
        self.issues.write_text("uf,municipio_origem,codigo_ibge,regra\nBA,CRISTOPOLIS,1,votos_candidatos\n")
        with self.assertRaises(ValueError):
            reconcile(self.issues,self.tse)

    def test_detecta_duplicacao_votavel_na_mesma_secao(self):
        path=self.tse/"votacao_secao_2026_BR.zip"
        with zipfile.ZipFile(path) as z:
            content=z.read("votacao_secao_2026_BR.csv").decode()
        path.unlink()
        with zipfile.ZipFile(path,"w") as z:
            z.writestr("votacao_secao_2026_BR.csv",content+content.splitlines()[1]+"\n")
        with self.assertRaisesRegex(ValueError,"Duplicação"):
            reconcile(self.issues,self.tse)

if __name__=="__main__":
    unittest.main()
