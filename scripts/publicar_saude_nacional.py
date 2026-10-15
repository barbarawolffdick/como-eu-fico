"""Publica saúde para o cadastro municipal completo, sem ingestões TSE/CGU.

Reutiliza caches verificados e só substitui a saída após validar as três fontes.
"""
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import time
import urllib.error
import urllib.parse
import zipfile

from scripts.publicar_saude_piloto import (
    APS, FNS_URL, ROOT, codigo_seis, extrair_aps, extrair_fns, inteiro, obter, ponte_ibge,
)

PMMB_ZIP = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/MaisMedicos/csv/ppf_mais_medicos.csv.zip"
CATALOGO_PMMB = "https://dadosabertos.saude.gov.br/dataset/provimento-federal-programa-mais-medicos"


def obter_com_retentativas(url, cache, atualizar=False):
    for tentativa in range(3):
        try:
            return obter(url, cache, atualizar)
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or tentativa == 2:
                raise
        except (urllib.error.URLError, TimeoutError):
            if tentativa == 2:
                raise
        time.sleep(2 ** tentativa)


def indexar_aps(doc, cadastro, parcela):
    ponte = ponte_ibge(cadastro)
    grupos = defaultdict(list)
    for linha in doc["pagamentos"]:
        seis = codigo_seis(linha["coMunicipioIbge"])
        codigo = ponte.get(seis)
        if codigo is None:
            raise ValueError(f"Município APS fora do cadastro: {seis}")
        if linha["sgUf"] != cadastro[codigo]["uf"]:
            raise ValueError("UF APS incompatível com cadastro")
        grupos[codigo].append(linha)
    # extrair_aps impede a soma de múltiplos processos e confere a parcela.
    return {codigo: extrair_aps({"data": doc["data"], "pagamentos": grupos[codigo]}, codigo, parcela)
            for codigo in cadastro}


def extrair_pmmb_nacional(linhas, cadastro):
    ponte = ponte_ibge(cadastro)
    municipais = {}
    excluidos = []
    total = 0
    for numero, linha in linhas:
        total += 1
        nivel = linha["nivel"]
        if nivel in ("DSEI", "ESTADUAL"):
            # Estas unidades não são municípios; não ratear nem somar aos municipais.
            excluidos.append({"linha_origem": numero, "nivel": nivel, "codigo_fonte": linha["co_ibge"],
                              "nome": linha["municipio_dsei"], "uf": linha["uf"]})
            continue
        if nivel != "MUNICIPAL":
            raise ValueError("Nível territorial inesperado no PMMB")
        seis = codigo_seis(linha["co_ibge"])
        codigo = ponte.get(seis)
        if codigo is None:
            raise ValueError(f"Município PMMB fora do cadastro: {seis}")
        if linha["uf"] != cadastro[codigo]["uf"]:
            raise ValueError("UF PMMB incompatível com cadastro")
        if codigo in municipais:
            raise ValueError("PMMB duplicado por município")
        data = datetime.strptime(linha["dt_referencia"], "%Y-%m-%d").date().isoformat()
        if data > datetime.now(timezone.utc).date().isoformat():
            raise ValueError("PMMB com observação futura")
        valor = linha["total_ocupadas"]
        municipais[codigo] = {"data_referencia": data, "vagas_ocupadas": inteiro(None if valor == "" else valor),
                              "linha_origem": numero}
    if not municipais:
        raise ValueError("Arquivo PMMB sem observações municipais")
    referencias = sorted({r["data_referencia"] for r in municipais.values()})
    if len(referencias) != 1:
        raise ValueError("Consolidado PMMB mistura referências; exige reconciliação")
    registros = {codigo: {"ultimo": municipais.get(codigo), "indicador": "total_ocupadas",
        "motivo": None if codigo in municipais else "O arquivo oficial não contém observações para esta cidade. Ausência não é zero."}
        for codigo in cadastro}
    return registros, {"linhas_na_fonte": total, "linhas_municipais": len(municipais),
        "referencias": referencias, "registros_nao_municipais_separados": excluidos}


def cobertura(registros):
    seletores = {
        "fns": lambda r: r["fns"]["municipal"] is not None and r["fns"]["municipal"]["valor_liquido_centavos"] is not None,
        "aps": lambda r: r["aps"] is not None and all(e["homologadas"] is not None and e["financiadas"] is not None for e in r["aps"]["equipes"]),
        "mais_medicos": lambda r: r["mais_medicos"]["ultimo"] is not None and r["mais_medicos"]["ultimo"]["vagas_ocupadas"] is not None,
    }
    return {fonte: {"com_dado": sum(bool(pred(r)) for r in registros.values()),
                    "sem_dado": [c for c, r in registros.items() if not pred(r)]}
            for fonte, pred in seletores.items()}


def validar_publicacao(documento, cadastro):
    registros = documento["registros"]
    if set(registros) != set(cadastro) or documento["municipios_referencia"] != len(cadastro):
        raise ValueError("Publicação não cobre todo o cadastro municipal")
    if documento["cobertura"] != cobertura(registros):
        raise ValueError("Cobertura declarada não confere com registros")
    for codigo, r in registros.items():
        if r["municipio"] != {k: cadastro[codigo][k] for k in ("codigo_ibge", "nome", "uf")}:
            raise ValueError("Identificação municipal inconsistente")
        for tipo in ("municipal", "estadual_sediado_na_cidade"):
            resumo = r["fns"][tipo]
            if resumo is not None:
                valores = [c["valor_liquido_centavos"] for c in resumo["componentes"]]
                esperado = None if None in valores else sum(valores)
                if resumo["valor_liquido_centavos"] != esperado:
                    raise ValueError("Soma dos componentes FNS inconsistente")


def guardar_fonte_local(path, url, cache):
    dados = path.read_bytes()
    meta = {"url": url, "sha256": hashlib.sha256(dados).hexdigest(),
            "data_extracao": datetime.now(timezone.utc).isoformat(), "reutilizado": True}
    cache.mkdir(parents=True, exist_ok=True)
    chave = hashlib.sha256(url.encode()).hexdigest()
    (cache / f"{chave}.raw").write_bytes(dados)
    (cache / f"{chave}.json").write_text(json.dumps(meta, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=ROOT / "data/raw/saude/nacional")
    parser.add_argument("--saida", type=Path, default=ROOT / "data/public/saude_municipal.json")
    parser.add_argument("--atualizar", action="store_true")
    args = parser.parse_args()
    import openpyxl

    cadastro = {r["codigo_ibge"]: r for r in json.loads((ROOT / "data/public/rankings_2026.json").read_text())["registros"]}
    _, origem_fns = obter_com_retentativas(FNS_URL, args.cache, args.atualizar)
    print("FNS: validando planilha nacional…", flush=True)
    path = args.cache / f"{hashlib.sha256(FNS_URL.encode()).hexdigest()}.raw"
    with path.open("rb") as arquivo:
        wb = openpyxl.load_workbook(arquivo, read_only=True, data_only=True)
        try:
            it = wb.active.iter_rows(values_only=True)
            headers = next(it)
            fns, validacao_fns = extrair_fns(((i, dict(zip(headers, r))) for i, r in enumerate(it, 2)), cadastro, tuple(cadastro))
        finally:
            wb.close()
    validacao_fns["linhas_municipios_cadastro"] = validacao_fns.pop("linhas_piloto")

    b, origem_parcelas = obter_com_retentativas(APS + "/data/parcelas?ano=2026", args.cache, args.atualizar)
    hoje = datetime.now(timezone.utc).strftime("%Y%m")
    parcela = max(p for p in json.loads(b) if isinstance(p, str) and len(p) == 6 and p.isdigit() and p <= hoje)
    qs = urllib.parse.urlencode({"nuParcelaInicio": parcela, "nuParcelaFim": parcela,
                                "tipoRelatorio": "COMPLETO", "unidadeGeografica": "MUNICIPIO"})
    b, origem_aps = obter_com_retentativas(APS + "/financiamento/pagamento?" + qs, args.cache, args.atualizar)
    aps = indexar_aps(json.loads(b), cadastro, parcela)
    print(f"APS: {sum(r is not None for r in aps.values())} cidades na parcela {parcela}.", flush=True)

    b, origem_pmmb = obter_com_retentativas(PMMB_ZIP, args.cache, args.atualizar)
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        membros = z.namelist()
        if membros != ["ppf_mais_medicos.csv"]:
            raise ValueError("Conteúdo inesperado no ZIP PMMB")
        with z.open(membros[0]) as raw:
            leitor = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"), delimiter=";")
            pmmb, validacao_pmmb = extrair_pmmb_nacional(enumerate(leitor, 2), cadastro)
    registros = {c: {"municipio": {k: m[k] for k in ("codigo_ibge", "nome", "uf")},
        "fns": fns[c], "aps": aps[c], "mais_medicos": pmmb[c],
        "proveniencia": {"fns": origem_fns, "aps": origem_aps, "mais_medicos": origem_pmmb}}
        for c, m in sorted(cadastro.items())}
    documento = {"esquema": 2, "status": "NACIONAL", "data_geracao": datetime.now(timezone.utc).isoformat(),
        "municipios_referencia": len(cadastro), "unidade_territorial": "municipio_ibge_7_digitos", "natureza": "observado",
        "fonte_parcelas": origem_parcelas,
        "fontes": {"fns": origem_fns, "aps": origem_aps, "mais_medicos": origem_pmmb},
        "validacao": {"fns": validacao_fns, "mais_medicos": validacao_pmmb},
        "cobertura": cobertura(registros), "registros": registros}
    validar_publicacao(documento, cadastro)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    temp = args.saida.with_suffix(".tmp")
    temp.write_text(json.dumps(documento, ensure_ascii=False, separators=(",", ":")) + "\n")
    temp.replace(args.saida)
    print(json.dumps({"arquivo": str(args.saida), "municipios": len(registros), "cobertura": documento["cobertura"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
