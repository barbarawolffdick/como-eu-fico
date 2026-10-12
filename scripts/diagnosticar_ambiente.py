#!/usr/bin/env python3
"""Diagnóstico somente leitura. Não executa git pull, checkout ou correções."""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CHECKED_PATH = "scripts/inspecionar_tse_2026.py"
EXPECTED_BRANCH = "feat/reconciliacao-tse-2026"

def git(*args):
    p = subprocess.run(["git", *args], capture_output=True, text=True, timeout=15, check=False)
    return {"exit_code": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output", default="diagnostico-ambiente.json")
    a=parser.parse_args()
    root=Path.cwd()
    checks={
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "cwd":str(root),
      "python":sys.version,
      "file_checked":CHECKED_PATH,
      "file_exists":(root/CHECKED_PATH).is_file(),
      "git_root":git("rev-parse","--show-toplevel"),
      "branch_local":git("branch","--show-current"),
      "head_local":git("rev-parse","HEAD"),
      "status_porcelain":git("status","--porcelain"),
      "remote_branch_reference":git("rev-parse","--verify","refs/remotes/origin/"+EXPECTED_BRANCH),
      "file_in_local_HEAD":git("ls-tree","-r","--name-only","HEAD","--",CHECKED_PATH),
      "file_in_remote_tracking_ref":git("ls-tree","-r","--name-only","refs/remotes/origin/"+EXPECTED_BRANCH,"--",CHECKED_PATH),
      "expected_branch":EXPECTED_BRANCH,
      "notes":[
        "A existência do arquivo na branch remota do GitHub não implica que ele exista no checkout local.",
        "Este diagnóstico NÃO consulta a rede, NÃO atualiza refs e NÃO executa comandos corretivos.",
        "As observações deste JSON não identificam, por si só, uma causa única."
      ]
    }
    dest=Path(a.output)
    dest.write_text(json.dumps(checks,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(checks,ensure_ascii=False,indent=2))
    print("Diagnóstico salvo em:",dest)
if __name__=="__main__":
    main()
