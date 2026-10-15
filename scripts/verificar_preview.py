"""Valida um deploy Vercel contra os snapshots locais, sem novas ingestões."""
import argparse
import concurrent.futures
import hashlib
import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--publico", action="store_true", help="Verificar acesso público, sem autenticação.")
    args = parser.parse_args()
    url = urlparse(args.url)
    if url.scheme != "https" or not url.hostname or not url.hostname.endswith(".vercel.app") or url.path not in ("", "/"):
        parser.error("Informe somente a origem HTTPS do deploy vercel.app.")
    root = Path(__file__).resolve().parent.parent
    headers = {}
    if not args.publico:
        resultado = subprocess.run([
            "npx", "--yes", "vercel@64.2.0", "project", "token", "como-eu-fico",
            "--scope", "barbaras-projects-f33a375a", "--json",
        ], cwd=root, text=True, capture_output=True, timeout=60, check=True)

        def tokens(value):
            if isinstance(value, str) and value.startswith("eyJ") and value.count(".") == 2:
                return [value]
            if isinstance(value, dict):
                return [token for item in value.values() for token in tokens(item)]
            return []

        encontrados = tokens(json.loads(resultado.stdout))
        assert len(encontrados) == 1, "Token temporário não identificado; nenhuma credencial foi exibida."
        headers["x-vercel-trusted-oidc-idp-token"] = encontrados[0]

    class MesmaOrigem(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            if urlparse(newurl).netloc != url.netloc:
                raise RuntimeError("Redirecionamento para fora do deploy; autenticação não aceita.")
            return super().redirect_request(req, fp, code, msg, hdrs, newurl)

    def consultar(path):
        req = Request(args.url.rstrip("/") + path, headers=headers)
        with build_opener(MesmaOrigem()).open(req, timeout=30) as resposta:
            return path, resposta.read().decode("utf-8")

    paths = ["/", "/explorar", "/analises", "/fontes", "/api/fontes",
             "/api/municipios?q=3550308", "/api/municipios/3550308",
             "/api/rankings?metrica=valor_habitante&uf=SP&vencedor=13",
             "/api/cobertura?municipio=3550308", "/api/cobertura?municipio=1504752",
             "/api/analises", "/api/mudanca-familias", "/api/mudanca-parcelas",
             "/api/saude/3550308", "/api/saude/5101837", "/api/saude/1504752"]
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
    assert dados["/api/saude/3550308"]["disponivel"] is True
    assert dados["/api/saude/3550308"]["dados"] == json.loads((root / "data/public/saude_municipal.json").read_text())["registros"]["3550308"]
    assert dados["/api/saude/5101837"]["dados"]["mais_medicos"]["ultimo"]["vagas_ocupadas"] == 0
    assert dados["/api/saude/1504752"]["disponivel"] is True
    assert fontes["saude"]["municipios_referencia"] == fontes["municipios"]
    for path in ("/api/mudanca-familias", "/api/mudanca-parcelas"):
        mudanca = dados[path]
        assert sum(x["total"] for x in mudanca["porVencedor"]) == mudanca["municipios"] > 0
    print(json.dumps({"resultado": "PASS", "url": args.url, "commit": fontes["commit"],
                      "rotas": len(paths), "snapshots_conferidos": len(fontes["arquivos"]),
                      "municipios_com_cobertura": fontes["pessoas"]["municipios_com_dado"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
