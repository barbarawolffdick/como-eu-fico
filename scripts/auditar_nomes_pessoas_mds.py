"""Diagnóstico de municípios MDS sem correspondência com IBGE.
Candidatos por distância servem APENAS à investigação, nunca ao pareamento.
"""
import json
from pathlib import Path
from scripts.publicar_pessoas_mds import norm

ROOT=Path(__file__).resolve().parents[1]
mds=json.loads((ROOT/"data/public/pessoas_mds.json").read_text(encoding="utf-8"))
rows=json.loads((ROOT/"data/public/rankings_2026.json").read_text(encoding="utf-8"))["registros"]
bycode={r["codigo_ibge"]:r for r in rows}

def edit(a,b):
    last=list(range(len(b)+1))
    for i,char in enumerate(a):
        curr=[i+1]
        for j,other in enumerate(b):
            curr.append(min(last[j+1]+1,curr[j]+1,last[j]+(char!=other)))
        last=curr
    return last[-1]

out={"faltantes_ibge":[{"codigo_ibge":code,"nome_ibge":bycode[code]["nome"],"uf":bycode[code]["uf"]} for code in mds["municipios_sem_dado"]],
     "nomes_mds_sem_identificador":[]}
for uf,name in mds["nomes_mds_sem_correspondencia"]:
    options=sorted(
        ({"codigo_ibge":r["codigo_ibge"],"nome_ibge":r["nome"],"uf":r["uf"],"distancia":edit(name,norm(r["nome"]))}
         for r in rows if r["uf"]==uf),
        key=lambda x:(x["distancia"],x["codigo_ibge"])
    )[:3]
    out["nomes_mds_sem_identificador"].append({"uf":uf,"nome_mds_normalizado":name,"candidatos_na_base_ibge":options})
print(json.dumps(out,ensure_ascii=False,indent=2))
