"""Completa ausências cartográficas MDS com consultas tabulares reconciliadas.

python -m scripts.complementar_pessoas_mds --corrigir-periodo
Não consulta registros pessoais nem reprocessa TSE/CGU.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from scripts.publicar_saude_piloto import ROOT, obter

AUSENCIAS_MAPA = ("1504752", "4212650", "4220000", "4314548", "5006275", "5101837")
CONTROLES = ("3550308", "1302603", "2611606", "3304557", "4314902")
CAMPOS = ("(case when coalesce(t.n_pess_070_140_cad_pbf,0) + coalesce(t.n_",
          "n_pess_140_272_cad_pbf",
          "(t.n_pess_cad_pbf - (t.n_pess_070_cad_pbf + t.n_pess_070_140_ca")
PERIODO = "202609"
CACHE = ROOT / "data/raw/mds/tabular-pessoas"


def extrair(html, codigo, municipio, periodo=PERIODO):
    """Lê o JSON público do gráfico, nunca executa JavaScript da fonte."""
    from scripts.publicar_pessoas_mds import norm
    blocos = re.findall(r"var strJsondados = '(.*?)';", html.decode("utf-8"), re.S)
    if len(blocos) != 1:
        raise ValueError("Bloco tabular MDS ausente ou ambíguo")
    linhas = json.loads(blocos[0])
    referencia = f"{periodo[:4]}-{periodo[4:]}-01"
    if not isinstance(linhas, list) or not linhas:
        raise ValueError("Série MDS vazia")
    vistos = set()
    for r in linhas:
        if str(r.get("codigo")) != (codigo[:6] if codigo else "0"):
            raise ValueError("Código municipal MDS divergente")
        if codigo and (r.get("sigla") != municipio["uf"] or norm(r.get("nome")) != norm(municipio["nome"])):
            raise ValueError("Identidade municipal MDS divergente")
        if not codigo and r.get("nome") != "Brasil":
            raise ValueError("Controle não corresponde ao Brasil")
        if r.get("mes_ano") in vistos:
            raise ValueError("Competência MDS duplicada")
        vistos.add(r.get("mes_ano"))
    selecionadas = [r for r in linhas if r.get("mes_ano") == referencia]
    if len(selecionadas) != 1:
        raise ValueError("Competência MDS não disponível")
    r = selecionadas[0]
    valores = [r.get(k) for k in (*CAMPOS, "n_pess_cad_pbf")]
    if any(type(v) is not int or v < 0 for v in valores):
        raise ValueError("Contagem MDS ausente, negativa ou não inteira")
    if sum(valores[:3]) != valores[3]:
        raise ValueError("Faixas MDS não reconciliam com o total de pessoas")
    return {"codigo_fonte": r["codigo"], "nome_fonte": r["nome"], "uf": r["sigla"],
            "referencia": referencia, "pessoas": valores[3], "faixas": valores[:3]}


def completar(documento, cadastro, consultas, corrigir_periodo=False):
    """Só publica após controles territoriais, temporais e de contagem."""
    if documento["periodo"] != PERIODO and not (corrigir_periodo and documento["periodo"] == "202608"):
        raise ValueError("Período de origem exige revisão explícita")
    if set(documento["registros"]) != set(cadastro) or len(cadastro) != 5571:
        raise ValueError("Cadastro municipal incompleto")
    ausentes = {c for c, r in documento["registros"].items() if r["pessoas"] is None}
    if not ausentes.issubset(AUSENCIAS_MAPA):
        raise ValueError("Nova ausência cartográfica exige investigação")
    resultado = deepcopy(documento)
    evidencias = {}
    for codigo in ("", *CONTROLES, *AUSENCIAS_MAPA):
        bruto, origem = consultas[codigo]
        if hashlib.sha256(bruto).hexdigest() != origem["sha256"]:
            raise ValueError("Hash da consulta tabular não confere")
        if origem["url"] != documento["pagina_fonte"] + (f"&ag=m&codigo={codigo}" if codigo else ""):
            raise ValueError("URL tabular não corresponde ao recorte declarado")
        dado = extrair(bruto, codigo, cadastro.get(codigo))
        evidencias[codigo or "brasil"] = {**origem, **dado}
        if codigo in CONTROLES:
            if dado["pessoas"] != documento["registros"][codigo]["pessoas"]:
                raise ValueError("Mapa e série tabular divergem na cidade de controle")
        elif codigo:
            registro = resultado["registros"][codigo]
            if registro["pessoas"] is not None and registro["pessoas"] != dado["pessoas"]:
                raise ValueError("Complemento diverge de valor já publicado")
            pop = cadastro[codigo]["populacao"]
            if type(pop) is not int or pop <= 0 or dado["pessoas"] > pop:
                raise ValueError("Denominador IBGE inválido ou cobertura acima de 100%")
            registro.update(pessoas=dado["pessoas"], populacao=pop,
                            cobertura_pct=round(100 * dado["pessoas"] / pop, 4))
    nacional = evidencias["brasil"]
    if len(documento["proveniencia"]) != 3:
        raise ValueError("São necessárias as três faixas do mapa")
    totais_faixas = [p["total_na_resposta"] + sum(evidencias[c]["faixas"][i] for c in AUSENCIAS_MAPA)
                    for i, p in enumerate(documento["proveniencia"])]
    if totais_faixas != nacional["faixas"]:
        raise ValueError("Mapa e complemento não fecham com as três faixas nacionais")
    total = sum(r["pessoas"] for r in resultado["registros"].values())
    if total != nacional["pessoas"]:
        raise ValueError("Total municipal não fecha com o Brasil na mesma competência")
    periodo_anterior = documento.get("periodo_solicitado_na_coleta_original", documento["periodo"])
    resultado.update(periodo=PERIODO, municipios_com_dado=len(cadastro), municipios_sem_dado=[],
        periodo_solicitado_na_coleta_original=periodo_anterior,
        data_validacao_tabular=datetime.now(timezone.utc).isoformat(),
        complemento_tabular={"periodo": PERIODO, "codigos_complementados": list(AUSENCIAS_MAPA),
            "controles": list(CONTROLES), "consultas": evidencias,
            "validacao": {"status": "PASS", "total_pessoas": total, "totais_faixas": totais_faixas,
                          "municipios": len(cadastro)}},
        metodo="Soma de três faixas disjuntas MDS. Seis ausências cartográficas completadas por código municipal; competência e totais reconciliados com a série tabular nacional.")
    return resultado


def consultar(documento, cadastro, cache=CACHE, atualizar=False, corrigir_periodo=False):
    consultas = {}
    for codigo in ("", *CONTROLES, *AUSENCIAS_MAPA):
        url = documento["pagina_fonte"] + (f"&ag=m&codigo={codigo}" if codigo else "")
        consultas[codigo] = obter(url, cache, atualizar)
    return completar(documento, cadastro, consultas, corrigir_periodo)


def salvar(documento, destino):
    temporario = destino.with_suffix(".tmp")
    temporario.write_text(json.dumps(documento, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporario.replace(destino)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corrigir-periodo", action="store_true")
    parser.add_argument("--atualizar", action="store_true")
    parser.add_argument("--cache", type=Path, default=CACHE)
    parser.add_argument("--saida", type=Path, default=ROOT / "data/public/pessoas_mds.json")
    args = parser.parse_args()
    documento = json.loads(args.saida.read_text())
    cadastro = {r["codigo_ibge"]: r for r in json.loads((ROOT / "data/public/rankings_2026.json").read_text())["registros"]}
    resultado = consultar(documento, cadastro, args.cache, args.atualizar, args.corrigir_periodo)
    salvar(resultado, args.saida)
    print(json.dumps(resultado["complemento_tabular"]["validacao"], ensure_ascii=False))


if __name__ == "__main__":
    main()
