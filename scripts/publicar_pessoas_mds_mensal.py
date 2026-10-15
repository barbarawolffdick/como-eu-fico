"""Publica contagens mensais tabulares verificadas, sem refazer ingestões TSE/CGU.

O recorte histórico é parcial e explicitamente identificado. Outras cidades podem
ser consultadas individualmente pelo endpoint, com a mesma validação.
"""
import json
from datetime import datetime, timezone
from scripts.complementar_pessoas_mds import AUSENCIAS_MAPA, CONTROLES, CACHE, extrair
from scripts.publicar_saude_piloto import ROOT, obter


def main():
    base = json.loads((ROOT / "data/public/pessoas_mds.json").read_text())
    cadastro = {r["codigo_ibge"]: r for r in json.loads((ROOT / "data/public/rankings_2026.json").read_text())["registros"]}
    codigos = sorted(set((*AUSENCIAS_MAPA, *CONTROLES, "3138203", "5300108")))
    registros = {}
    for codigo in codigos:
        url = base["pagina_fonte"] + f"&ag=m&codigo={codigo}"
        bruto, origem = obter(url, CACHE)
        periodos = {p: extrair(bruto, codigo, cadastro[codigo], p)["pessoas"] for p in ("202608", "202609")}
        if periodos["202609"] != base["registros"][codigo]["pessoas"]:
            raise ValueError("Revisão da fonte: reconciliar com o snapshot de setembro antes de publicar")
        registros[codigo] = {"periodos": periodos, "proveniencia": origem}
    resultado = {"esquema": 1, "status": "PARCIAL", "unidade": "pessoas_em_familias_beneficiarias",
                 "municipios_cadastro": len(cadastro), "municipios_com_dado": len(registros),
                 "periodos": ["202608", "202609"], "data_geracao": datetime.now(timezone.utc).isoformat(),
                 "metodo": "Série tabular por código IBGE; total reconciliado com três faixas disjuntas em cada competência.",
                 "registros": registros}
    destino = ROOT / "data/public/pessoas_mds_mensal.json"
    temporario = destino.with_suffix(".tmp")
    temporario.write_text(json.dumps(resultado, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporario.replace(destino)
    print(json.dumps({"municipios": len(registros), "periodos": resultado["periodos"], "status": "PARCIAL"}))


if __name__ == "__main__":
    main()
