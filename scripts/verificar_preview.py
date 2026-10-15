"""Valida um deploy Vercel contra os snapshots locais, sem novas ingestões."""
import argparse
import concurrent.futures
import hashlib
import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    args = parser.parse_args()
    url = urlparse(args.url)
    if url.scheme != "https" or not url.hostname or not url.hostname.endswith(".vercel.app") or url.path not in ("", "/"):
        parser.error("Informe somente a origem HTTPS do deploy vercel.app.")
    root = Path(__file__).resolve().parent.parent

    def consultar(path):
        resultado = subprocess.run([
            "npx", "--yes", "vercel@64.2.0", "curl", path,
            "--deployment", args.url, "--scope", "barbaras-projects-f33a375a",
            "--", "--fail", "--silent", "--show-error", "--max-time", "30",
        ], cwd=root, text=True, capture_output=True, timeout=60, check=True)
        return path, resultado.stdout

    paths = ["/", "/explorar", "/analises", "/fontes", "/api/fontes",
             "/api/municipios?q=3550308", "/api/municipios/3550308",
             "/api/rankings?metrica=valor_habitante&uf=SP&vencedor=13",
             "/api/cobertura?municipio=3550308", "/api/cobertura?municipio=1504752",
             "/api/analises", "/api/mudanca-familias", "/api/mudanca-parcelas"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        respostas = dict(pool.map(consultar, paths))
    for path, titulo in [("/", "Encontre seu município"), ("/explorar", "Alcance do Bolsa Família"),
                         ("/analises", "Relações territoriais"), ("/fontes", "Fontes e metodologia")]:
        assert titulo in respostas[path], path
    dados = {p: json.loads(body) for p, body in respostas.items() if p.startswith("/api/")}
    fontes = dados["/api/fontes"]
    for arquivo in fontes["arquivos"]:
        sha256 = hashlib.sha256((root / "data/public" / arquivo["arquivo"]).read_bytes()).hexdigest()
        assert arquivo["sha256"] == sha256, arquivo["arquivo"]
    assert dados["/api/municipios?q=3550308"][0]["codigo_ibge"] == "3550308"
    detalhe = dados["/api/municipios/3550308"]
    assert detalhe["votos_presidenciais"] and detalhe["bolsa_familia"]
    assert dados["/api/cobertura?municipio=3550308"]["disponivel"] is True
    ausente = dados["/api/cobertura?municipio=1504752"]
    assert ausente["disponivel"] is False and ausente["municipio"]["pessoas"] is None
    ranking = dados["/api/rankings?metrica=valor_habitante&uf=SP&vencedor=13"]["resultados"]
    assert len(ranking) == 10 and all(x["uf"] == "SP" and x["vencedor"] == "13" for x in ranking)
    assert all(a["centavos_por_habitante"] >= b["centavos_por_habitante"] for a, b in zip(ranking, ranking[1:]))
    assert dados["/api/analises"]["universo"] > 0
    for path in ("/api/mudanca-familias", "/api/mudanca-parcelas"):
        mudanca = dados[path]
        assert sum(x["total"] for x in mudanca["porVencedor"]) == mudanca["municipios"] > 0
    print(json.dumps({"resultado": "PASS", "url": args.url, "commit": fontes["commit"],
                      "rotas": len(paths), "snapshots_conferidos": len(fontes["arquivos"]),
                      "municipios_com_cobertura": fontes["pessoas"]["municipios_com_dado"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
