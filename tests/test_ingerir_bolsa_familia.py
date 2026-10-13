import csv
import io
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.ingerir_bolsa_familia import bridge,transform,write_month

HEADER='MÊS COMPETÊNCIA;MÊS REFERÊNCIA;UF;CÓDIGO MUNICÍPIO SIAFI;NOME MUNICÍPIO;CPF FAVORECIDO;NIS FAVORECIDO;NOME FAVORECIDO;VALOR PARCELA\n'
class PipelineTests(unittest.TestCase):
    def test_streaming_mapping_and_independent_sqlite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            ponte=root/"tabmun.csv"
            ponte.write_text("0001;05893631000109;MUNICIPIO TESTE;RO;1100106\n",encoding="latin-1")
            mapping=bridge(ponte)
            self.assertEqual(mapping[("RO","0001")],"1100106")
            arc=root/"202501.zip"
            with zipfile.ZipFile(arc,"w",zipfile.ZIP_DEFLATED) as z:
                z.writestr("202501_NovoBolsaFamilia.csv",HEADER+
                 '202501;202501;RO;0001;TESTE;;;PESSOA A;600,00\n'+
                 '202501;202412;RO;0001;TESTE;;;PESSOA B;200,25\n')
            groups,meta=transform(arc,mapping,"202501",{"parcelas":2,"total_centavos":80025,"municipios_ibge":1})
            self.assertEqual(meta["meses_referencia"],["202412","202501"])
            self.assertEqual(len(groups),2)
            db=root/"beneficios.sqlite"
            write_month(db,"202501",groups,meta,"ziphash","bridgehash")
            with sqlite3.connect(db) as cx:
                self.assertEqual(cx.execute("SELECT SUM(valor_centavos), SUM(quantidade_parcelas) FROM parcelas_municipais").fetchone(),(80025,2))
                self.assertEqual(cx.execute("SELECT codigo_ibge FROM parcelas_municipais LIMIT 1").fetchone()[0],"1100106")
            with self.assertRaisesRegex(ValueError,"já ingerida"):
                write_month(db,"202501",groups,meta,"ziphash","bridgehash")
    def test_invalid_month_and_missing_mapping_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            arc=Path(tmp)/"x.zip"
            with zipfile.ZipFile(arc,"w") as z:
                z.writestr("x.csv",HEADER+'202501;202501;RO;0001;TESTE;;;PESSOA;600,00\n')
            with self.assertRaisesRegex(ValueError,"sem ponte"):
                transform(arc,{},"202501")
            with self.assertRaisesRegex(ValueError,"competência"):
                transform(arc,{("RO","0001"):"1100106"},"202502")
if __name__=="__main__": unittest.main()
