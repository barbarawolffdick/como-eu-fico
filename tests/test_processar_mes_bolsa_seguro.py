import sqlite3
import tempfile
import unittest
from pathlib import Path
from scripts.processar_mes_bolsa_seguro import backup

class BackupTests(unittest.TestCase):
    def test_backup_copia_consistente_e_independente(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"origem.sqlite"
            dest=Path(d)/"backup.sqlite"
            with sqlite3.connect(source) as cx:
                cx.execute("CREATE TABLE t (n INTEGER)")
                cx.execute("INSERT INTO t VALUES(5)")
            backup(source,dest)
            with sqlite3.connect(dest) as cx:
                self.assertEqual(cx.execute("SELECT n FROM t").fetchone()[0],5)
                self.assertEqual(cx.execute("PRAGMA integrity_check").fetchone()[0],"ok")
            with sqlite3.connect(source) as cx:
                cx.execute("INSERT INTO t VALUES(8)")
            with sqlite3.connect(dest) as cx:
                self.assertEqual(cx.execute("SELECT COUNT(*) FROM t").fetchone()[0],1)

if __name__=="__main__":unittest.main()
