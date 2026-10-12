#!/usr/bin/env python3
"""Reconcilia APENAS oito municípios; preserva fontes e bloqueia inferências ambíguas."""
import argparse
import csv
import io
import json
import re
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path

TARGETS = {
    ("BA", "CRISTOPOLIS"), ("MG", "PIEDADE DOS GERAIS"),
    ("MG", "SANTA CRUZ DE MINAS"), ("PA", "CACHOEIRA DO PIRIA"),
    ("PR", "ALVORADA DO SUL"), ("RJ", "CAMBUCI"),
    ("RJ", "PIRAI"), ("RJ", "TRAJANO DE MORAES"),
}
VOTE_MEMBER = "votacao_secao_2026_BR.csv"
DETAIL_MEMBER = "detalhe_votacao_secao_2026_BRASIL.csv"
OUT_FIELDS = [
    "uf", "municipio", "codigo_ibge", "codigo_municipio_tse",
    "secoes_votacao", "secoes_apuracao", "nome_lula_tse", "nome_flavio_tse",
    "origem_votos_lula", "tse_votos_lula", "dif_lula",
    "origem_votos_flavio", "tse_votos_flavio", "dif_flavio",
    "origem_votos_validos", "tse_votos_validos", "dif_validos",
    "tse_comparecimento", "tse_abstencoes", "status", "observacoes",
    "arquivo_origem", "linha_origem",
]

def norm(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(x for x in value if not unicodedata.combining(x))
    return re.sub(r"\s+", " ", value.strip().upper())

def required(row, fields, context):
    missing = set(fields) - set(row)
    if missing:
        raise ValueError(f"{context}: colunas ausentes: {sorted(missing)}")

def records(archive, member):
    if archive.namelist().count(member) != 1:
        raise ValueError(f"membro esperado não é único: {member}")
    with archive.open(member) as file:
        reader = csv.DictReader(io.TextIOWrapper(file, encoding="latin-1", newline=""), delimiter=";")
        for line, row in enumerate(reader, 2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"{member}, linha {line}: estrutura inválida")
            yield line, row

def integer(value, origin):
    if not str(value).isascii() or not str(value).isdigit():
        raise ValueError(f"{origin}: inteiro inválido: {value!r}")
    return int(value)

def scope(row):
    return (row["ANO_ELEICAO"] == "2026" and row["NR_TURNO"] == "1"
            and row["TP_ABRANGENCIA"] == "F" and norm(row["DS_CARGO"]) == "PRESIDENTE")

def section(row):
    return (row["SG_UF"], row["CD_MUNICIPIO"], row["NR_ZONA"], row["NR_SECAO"])

def classify(name):
    n = norm(name)
    if n in {"LUIZ INACIO LULA DA SILVA", "LULA"}:
        return "lula"
    if n == "FLAVIO BOLSONARO":
        return "flavio"
    return None

def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def reconcile(source, directory):
    with source.open(encoding="utf-8-sig", newline="") as handle:
        original = list(csv.DictReader(handle))
    if len(original) != 8:
        raise ValueError(f"Esperados exatamente 8 registros na lista de inconsistências, encontrados {len(original)}")
    by_target = {}
    for row in original:
        required(row, ["uf", "municipio_origem", "codigo_ibge", "regra"], "inconsistências")
        key = (row["uf"], norm(row["municipio_origem"]))
        if row["regra"] != "votos_candidatos" or key not in TARGETS or key in by_target:
            raise ValueError(f"Registro inesperado ou duplicado na seleção dos oito: {key} {row['regra']}")
        by_target[key] = row
    if set(by_target) != TARGETS:
        raise ValueError(f"Seleção incompleta: {sorted(TARGETS - set(by_target))}")
    summary = source.parent.parent / "processed" / "eleicoes_2026_municipios.csv"
    with summary.open(encoding="utf-8-sig", newline="") as handle:
        processed = list(csv.DictReader(handle))
    by_ibge = {}
    for row in processed:
        if row["codigo_ibge"] in {r["codigo_ibge"] for r in original}:
            if row["codigo_ibge"] in by_ibge:
                raise ValueError("Código IBGE duplicado: " + row["codigo_ibge"])
            by_ibge[row["codigo_ibge"]] = row
    if len(by_ibge) != 8:
        raise ValueError("Consolidação não contém exatamente os oito códigos IBGE")
    for key, issue in by_target.items():
        row = by_ibge[issue["codigo_ibge"]]
        if (row["uf"], norm(row["municipio_origem"])) != key:
            raise ValueError("Correspondência IBGE/origem divergente: " + str(key))

    candidate_votes = defaultdict(lambda: defaultdict(int))
    candidate_names = defaultdict(set)
    tse_codes = defaultdict(set)
    vote_sections = defaultdict(set)
    detail_sections = defaultdict(set)
    details = defaultdict(lambda: defaultdict(int))
    seen_detail = set()
    rows_per_candidate_section = set()
    unidentified = defaultdict(lambda: defaultdict(int))
    with zipfile.ZipFile(directory / "votacao_secao_2026_BR.zip") as archive:
        for lineno, row in records(archive, VOTE_MEMBER):
            required(row, ["ANO_ELEICAO", "NR_TURNO", "TP_ABRANGENCIA", "DS_CARGO",
                           "SG_UF", "NM_MUNICIPIO", "CD_MUNICIPIO", "NR_ZONA",
                           "NR_SECAO", "NR_VOTAVEL", "NM_VOTAVEL", "QT_VOTOS"], VOTE_MEMBER)
            key = (row["SG_UF"], norm(row["NM_MUNICIPIO"]))
            if key not in TARGETS or not scope(row):
                continue
            ident = section(row) + (row["NR_VOTAVEL"],)
            if ident in rows_per_candidate_section:
                raise ValueError(f"Duplicação de seção/votável em {VOTE_MEMBER}, linha {lineno}: {ident}")
            rows_per_candidate_section.add(ident)
            qty = integer(row["QT_VOTOS"], f"{VOTE_MEMBER}:{lineno}")
            tse_codes[key].add(row["CD_MUNICIPIO"])
            vote_sections[key].add(section(row))
            name = classify(row["NM_VOTAVEL"])
            if name:
                candidate_votes[key][name] += qty
                candidate_names[(key, name)].add(row["NM_VOTAVEL"])
            else:
                unidentified[key][(row["NR_VOTAVEL"], row["NM_VOTAVEL"])] += qty
    with zipfile.ZipFile(directory / "detalhe_votacao_secao_2026.zip") as archive:
        for lineno, row in records(archive, DETAIL_MEMBER):
            required(row, ["ANO_ELEICAO", "NR_TURNO", "TP_ABRANGENCIA", "DS_CARGO",
                           "SG_UF", "NM_MUNICIPIO", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO",
                           "QT_VOTOS_NOMINAIS", "QT_COMPARECIMENTO", "QT_ABSTENCOES"], DETAIL_MEMBER)
            key = (row["SG_UF"], norm(row["NM_MUNICIPIO"]))
            if key not in TARGETS or not scope(row):
                continue
            ident = section(row)
            if ident in seen_detail:
                raise ValueError(f"Duplicação de seção em {DETAIL_MEMBER}, linha {lineno}: {ident}")
            seen_detail.add(ident)
            tse_codes[key].add(row["CD_MUNICIPIO"])
            detail_sections[key].add(ident)
            for field in ("QT_VOTOS_NOMINAIS", "QT_COMPARECIMENTO", "QT_ABSTENCOES"):
                details[key][field] += integer(row[field], f"{DETAIL_MEMBER}:{lineno}")

    result = []
    for key in sorted(TARGETS):
        issue = by_target[key]
        src = by_ibge[issue["codigo_ibge"]]
        problems = []
        if len(tse_codes[key]) != 1:
            problems.append("codigo_tse_ausente_ou_ambiguo")
        if not vote_sections[key] or vote_sections[key] != detail_sections[key]:
            problems.append("cobertura_secoes_divergente")
        for candidate in ("lula", "flavio"):
            if len(candidate_names[(key, candidate)]) != 1:
                problems.append("nome_" + candidate + "_ausente_ou_ambiguo")
        totals = {x: details[key]["QT_VOTOS_NOMINAIS"] for x in ["validos"]}
        for candidate in ("lula", "flavio"):
            totals[candidate] = candidate_votes[key].get(candidate, 0)
        # Não assumir que votos nominais incluam ou excluam votos anulados/legenda:
        # só classificar total de válidos após conferência de categorias eleitorais.
        problems.append("definicao_votos_validos_pendente")
        output = dict(
            uf=key[0], municipio=key[1], codigo_ibge=issue["codigo_ibge"],
            codigo_municipio_tse=";".join(sorted(tse_codes[key])),
            secoes_votacao=len(vote_sections[key]), secoes_apuracao=len(detail_sections[key]),
            nome_lula_tse=";".join(sorted(candidate_names[(key, "lula")])),
            nome_flavio_tse=";".join(sorted(candidate_names[(key, "flavio")])),
            origem_votos_lula=src["votos_lula"], tse_votos_lula=totals["lula"] if candidate_names[(key,"lula")] else "",
            origem_votos_flavio=src["votos_flavio"], tse_votos_flavio=totals["flavio"] if candidate_names[(key,"flavio")] else "",
            origem_votos_validos=src["votos_validos"],
            tse_votos_validos="", dif_validos="",
            tse_comparecimento=details[key]["QT_COMPARECIMENTO"],
            tse_abstencoes=details[key]["QT_ABSTENCOES"],
            status="INCONCLUSIVO" if problems else "PASS",
            observacoes=";".join(problems),
            arquivo_origem=src["arquivo_origem"], linha_origem=src["linha_origem"]
        )
        for name in ("lula", "flavio"):
            value = output["tse_votos_" + name]
            output["dif_" + name] = int(value) - integer(output["origem_votos_" + name], "origem") if value != "" and "cobertura_secoes_divergente" not in problems else ""
        result.append(output)
    return result, {str(k): sorted([{"codigo":code,"nome":name,"votos":qty}
                                   for (code,name),qty in unidentified[k].items()], key=lambda x:(x["codigo"],x["nome"]))
                    for k in sorted(TARGETS)}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--issues", type=Path, default=Path("data/quality/inconsistencias_eleitorais.csv"))
    p.add_argument("--tse", type=Path, default=Path("data/raw/tse/2026"))
    p.add_argument("--out", type=Path, default=Path("data/quality/reconciliacao_8_municipios.csv"))
    args = p.parse_args()
    try:
        rows, candidates = reconcile(args.issues, args.tse)
        write_csv(args.out, rows, OUT_FIELDS)
        candidate_file = args.out.with_name("votaveis_8_municipios.json")
        candidate_file.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"registros": len(rows), "resultado": "INCONCLUSIVO",
                          "relatorio": str(args.out), "catalogo_votaveis": str(candidate_file),
                          "municipios": [{"uf":x["uf"],"municipio":x["municipio"], "status":x["status"],
                                           "observacoes":x["observacoes"]} for x in rows]}, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"resultado":"FAIL","erro":str(exc)},ensure_ascii=False))
        raise SystemExit(1)
if __name__ == "__main__":
    main()
