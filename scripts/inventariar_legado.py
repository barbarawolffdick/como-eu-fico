#!/usr/bin/env python3
"""Inventário local NÃO DESTRUTIVO de artefatos antigos e atuais."""
import argparse
import json
import subprocess
from pathlib import Path

CLASSES={
 "ativos":["scripts/construir_base_tse_ibge.py","scripts/aplicar_codigos_oficiais_tse_ibge.py",
           "scripts/diagnosticar_base_tse.py","scripts/inspecionar_correspondencia_tse_ibge.py",
           "scripts/publicar_base_municipal.py",
           "data/reference/municipios_ibge.csv","data/reference/tse_ibge/municipio_tse_ibge.zip",
           "data/tse_oficial/eleicoes_2026.sqlite","data/tse_oficial/codigos_oficiais/"],
 "investigacao_encerrada":["scripts/reconciliar_8_municipios.py","scripts/conferir_validos_8_municipios.py",
           "data/quality/reconciliacao_8_municipios.csv","data/quality/reconciliacao_8_municipios_validos.csv"],
 "legado_sem_uso_no_pipeline":["dados-municipios/","scripts/mapear_municipios.py",
           "scripts/consolidar_eleicoes.py","data/processed/eleicoes_2026_municipios.csv",
           "data/reference/municipios_mapeados.csv"],
 "auditoria_auxiliar":["scripts/validar_tse_2026.py","scripts/inspecionar_tse_2026.py",
           "scripts/baixar_tse_2026.py","scripts/diagnosticar_ambiente.py"]
}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,default=Path("inventario-limpeza.json"))
    a=p.parse_args()
    if a.out.exists(): p.error("Inventário já existe; escolha outro --out")
    tracked=set(subprocess.check_output(["git","ls-files"],text=True).splitlines())
    rows=[]
    for classification,paths in CLASSES.items():
        for target in paths:
            path=Path(target)
            matching=[x for x in tracked if x==target or x.startswith(target.rstrip("/")+"/")]
            rows.append({"caminho":target,"categoria":classification,
                         "existe_localmente":path.exists(),
                         "arquivos_rastreados_git":len(matching),
                         "observacao":"NÃO excluído"})
    other=[x for x in tracked if not any(x==p or x.startswith(p.rstrip("/")+"/")
                                 for group in CLASSES.values() for p in group)]
    report={"acao":"inventario_apenas","nenhum_arquivo_alterado":True,
            "itens_classificados":rows,"arquivos_rastreados_nao_classificados":other}
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Inventário criado: {a.out}; nenhuma exclusão realizada. Outros arquivos rastreados: {len(other)}")
if __name__=="__main__":
    main()
