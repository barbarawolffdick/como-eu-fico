#!/usr/bin/env python3
"""Desvincula SOMENTE os resumos antigos do Git; nunca apaga arquivos locais."""
import argparse
import subprocess
from pathlib import Path

LEGACY="dados-municipios/"
def git(*args):
    return subprocess.check_output(["git",*args],text=True).strip()
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--apply",action="store_true",help="Remove do ÍNDICE Git (mantém arquivos no Mac)")
    args=p.parse_args()
    repo=Path(git("rev-parse","--show-toplevel"))
    source=repo/LEGACY
    if not source.is_dir():
        p.error("Pasta legado ausente: "+str(source))
    tracked=git("ls-files","--",LEGACY).splitlines()
    if not tracked:
        print("Nenhum arquivo histórico rastreado; nada a fazer.")
        return
    print(f"Arquivos históricos rastreados: {len(tracked)}")
    print("Operação: retirar dados-municipios/ do índice Git sem apagar nenhum arquivo local.")
    if not args.apply:
        print("Prévia apenas. Para executar, use --apply.")
        return
    branch=git("branch","--show-current")
    if branch!="chore/consolidar-base-eleitoral":
        p.error("Branch inesperada; esperado chore/consolidar-base-eleitoral")
    if git("status","--porcelain"):
        p.error("Há alterações locais; revise/guarde antes de desvincular os arquivos")
    subprocess.run(["git","rm","-q","--cached","-r","--",LEGACY],cwd=repo,check=True)
    after=git("ls-files","--",LEGACY).splitlines()
    if after: raise RuntimeError(f"Restam {len(after)} entradas no índice")
    count=sum(1 for path in tracked if (repo/path).is_file())
    print(f"Removidos do índice: {len(tracked)}; cópias locais ainda existentes: {count}")
    print("Revise: git diff --cached --stat")
    print("Depois, para registrar: git commit -m 'chore: desvincula resumos eleitorais antigos'")
    print("E publicar: git push")
if __name__=="__main__":
    main()
