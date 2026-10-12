#!/usr/bin/env python3
"""Pré-validação TSE 2026: somente leitura, sem correções ou agregação eleitoral."""
import argparse
import csv
import hashlib
import io
import json
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

FILES = {
    "votos": "votacao_secao_2026_BR.zip",
    "detalhe": "detalhe_votacao_secao_2026.zip",
    "munzona": "detalhe_votacao_munzona_2026.zip",
}
KEYS = {"ANO_ELEICAO", "NR_TURNO", "TP_ABRANGENCIA", "SG_UF",
        "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "CD_CARGO", "DS_CARGO",
        "NR_LOCAL_VOTACAO"}
VOTE_FIELDS = KEYS | {"NR_VOTAVEL", "QT_VOTOS"}
DETAIL_FIELDS = KEYS | {"QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES",
                        "QT_VOTOS_NOMINAIS", "QT_VOTOS_BRANCOS", "QT_VOTOS_NULOS"}

def check(name, status, **evidence):
    return {"teste": name, "status": status, "evidencia": evidence}

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def rows(zip_file, member):
    with zip_file.open(member) as binary:
        stream = io.TextIOWrapper(binary, encoding="latin-1", newline="")
        reader = csv.DictReader(stream, delimiter=";")
        columns = set(reader.fieldnames or [])
        if len(columns) < 5:
            raise ValueError("Cabeçalho inválido: " + member)
        yield columns, None
        for line, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Linha inválida: {member}:{line}")
            yield None, row

def in_scope(row):
    return (row["ANO_ELEICAO"] == "2026" and row["NR_TURNO"] == "1"
            and row["TP_ABRANGENCIA"] == "F"
            and row["DS_CARGO"].strip().casefold() == "presidente")

def voting_checks(zip_file, member):
    iterator = rows(zip_file, member)
    columns, _ = next(iterator)
    missing = sorted(VOTE_FIELDS - columns)
    if missing:
        return [check("esquema_votacao", "FAIL", faltantes=missing)]
    total = selected = invalid = negative = conflicts = 0
    sections = {}
    votables = set()
    for _, row in iterator:
        total += 1
        if not in_scope(row):
            invalid += 1
            continue
        selected += 1
        section = (row["SG_UF"], row["CD_MUNICIPIO"], row["NR_ZONA"], row["NR_SECAO"])
        local = row["NR_LOCAL_VOTACAO"]
        if section in sections and sections[section] != local:
            conflicts += 1
        sections[section] = local
        try:
            if int(row["QT_VOTOS"]) < 0:
                negative += 1
        except ValueError:
            negative += 1
        votables.add(row["NR_VOTAVEL"])
    return [
        check("esquema_votacao", "PASS", colunas=len(columns), arquivo=member),
        check("escopo_votacao", "FAIL" if invalid or not selected else "PASS",
              linhas=total, selecionadas=selected, fora_escopo=invalid),
        check("valores_votacao", "FAIL" if negative else "PASS", invalidos=negative),
        check("locais_votacao", "FAIL" if conflicts else "PASS",
              secoes_distintas=len(sections), conflitos=conflicts),
        check("unicidade_linhas_votacao", "INCONCLUSIVO",
              motivo="O esquema inclui várias linhas por seção; falta validar a chave por votável e origem."),
        check("classificacao_votaveis", "INCONCLUSIVO",
              motivo="Não classificar votos brancos/nulos nem inferir candidato somente pelo número.",
              codigos_distintos=len(votables)),
    ]

EVIDENCE_FIELDS = ("arquivo_zip", "arquivo_csv", "linha_csv", "SG_UF", "CD_MUNICIPIO",
                   "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "NR_LOCAL_VOTACAO",
                   "QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES", "diferenca")

def write_evidence(path, evidence):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EVIDENCE_FIELDS)
        writer.writeheader()
        writer.writerows(evidence)

def detail_checks(zip_file, evidence=None, zip_name="detalhe_votacao_secao_2026.zip"):
    national = [name for name in zip_file.namelist()
                if name.endswith("detalhe_votacao_secao_2026_BRASIL.csv")]
    if len(national) != 1:
        return [check("selecionar_detalhe", "INCONCLUSIVO",
                      motivo="Arquivo nacional BRASIL não identificado de forma única.",
                      candidatos=national)]
    member = national[0]
    iterator = rows(zip_file, member)
    columns, _ = next(iterator)
    missing = sorted(DETAIL_FIELDS - columns)
    if missing:
        return [check("esquema_detalhe", "FAIL", faltantes=missing, arquivo=member)]
    total = selected = ignored = duplicates = 0
    seen = set()
    violations = Counter()
    examples = []
    numeric = ("QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES",
               "QT_VOTOS_NOMINAIS", "QT_VOTOS_BRANCOS", "QT_VOTOS_NULOS")
    for line_number, (_, row) in enumerate(iterator, start=2):
        total += 1
        if not in_scope(row):
            ignored += 1
            continue
        selected += 1
        section = (row["SG_UF"], row["CD_MUNICIPIO"], row["NR_ZONA"], row["NR_SECAO"])
        if section in seen:
            duplicates += 1
            if len(examples) < 5:
                examples.append(list(section))
        seen.add(section)
        try:
            values = {field: int(row[field]) for field in numeric}
        except ValueError:
            violations["inteiro_invalido"] += 1
            continue
        if any(value < 0 for value in values.values()):
            violations["negativo"] += 1
        difference = values["QT_APTOS"] - values["QT_COMPARECIMENTO"] - values["QT_ABSTENCOES"]
        if difference != 0:
            violations["aptos_diferentes_comparecimento_abstencoes"] += 1
            if evidence is not None:
                evidence.append({
                    "arquivo_zip": zip_name, "arquivo_csv": member,
                    "linha_csv": line_number,
                    **{field: row.get(field, "") for field in
                       ("SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO",
                        "NR_ZONA", "NR_SECAO", "NR_LOCAL_VOTACAO",
                        "QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES")},
                    "diferenca": difference,
                })
        if (values["QT_VOTOS_NOMINAIS"] + values["QT_VOTOS_BRANCOS"]
                + values["QT_VOTOS_NULOS"] > values["QT_COMPARECIMENTO"]):
            violations["votos_superiores_comparecimento"] += 1
    return [
        check("esquema_detalhe", "PASS", arquivo=member, colunas=len(columns)),
        check("escopo_detalhe", "FAIL" if not selected else "PASS",
              linhas=total, selecionadas=selected, outras_linhas=ignored),
        check("unicidade_detalhe", "FAIL" if duplicates else "PASS",
              repeticoes=duplicates, secoes_distintas=len(seen), exemplos=examples),
        check("aritmetica_detalhe", "FAIL" if violations else "PASS",
              ocorrencias=dict(violations)),
    ]

def run(directory, evidence=None):
    tests = []
    manifest_path = directory / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        resources = manifest["resources"]
        if not isinstance(resources, list):
            raise ValueError("resources não é lista")
        tests.append(check("manifesto", "PASS", arquivo=str(manifest_path)))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        resources = []
        tests.append(check("manifesto", "FAIL", erro=str(exc)))
    expected = {}
    for resource in resources:
        if isinstance(resource, dict):
            dl = resource.get("download") or {}
            if isinstance(dl, dict):
                expected[Path(dl.get("file") or "").name] = dl.get("sha256")
    valid = {}
    for kind, filename in FILES.items():
        path = directory / filename
        if not path.is_file():
            tests.append(check("arquivo_" + kind, "FAIL", caminho=str(path)))
            continue
        actual = sha256(path)
        reference = expected.get(filename)
        if not reference:
            tests.append(check("hash_" + kind, "INCONCLUSIVO",
                               motivo="Hash não consta do manifesto.", sha256=actual))
            continue
        status = "PASS" if actual.lower() == str(reference).lower() else "FAIL"
        tests.append(check("hash_" + kind, status,
                           esperado=reference, calculado=actual, bytes=path.stat().st_size))
        if status != "PASS":
            continue
        try:
            with zipfile.ZipFile(path) as archive:
                csvs = [name for name in archive.namelist() if name.lower().endswith(".csv")]
                status = "PASS" if csvs else "FAIL"
                tests.append(check("zip_" + kind, status,
                                   csvs=len(csvs), amostras_nomes=csvs[:4]))
                if csvs:
                    valid[kind] = path
        except (OSError, zipfile.BadZipFile) as exc:
            tests.append(check("zip_" + kind, "FAIL", erro=str(exc)))
    if "votos" in valid:
        try:
            with zipfile.ZipFile(valid["votos"]) as archive:
                candidates = [n for n in archive.namelist()
                              if n.endswith("votacao_secao_2026_BR.csv")]
                if len(candidates) != 1:
                    tests.append(check("arquivo_votacao_presidencial", "FAIL",
                                       encontrados=candidates))
                else:
                    tests.extend(voting_checks(archive, candidates[0]))
        except Exception as exc:
            tests.append(check("ler_votacao", "FAIL", erro=repr(exc)))
    if "detalhe" in valid:
        try:
            with zipfile.ZipFile(valid["detalhe"]) as archive:
                tests.extend(detail_checks(archive, evidence=evidence, zip_name=FILES["detalhe"]))
        except Exception as exc:
            tests.append(check("ler_detalhe", "FAIL", erro=repr(exc)))
    tests.append(check("reconciliacao", "INCONCLUSIVO",
                       motivo="Ainda não implementada; requer classificação validada dos votos e cobertura."))
    return tests

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=Path("data/raw/tse/2026"))
    parser.add_argument("--output", type=Path, default=Path("data/quality/validacao_tse_2026.json"))
    parser.add_argument("--evidence", type=Path,
                        default=Path("data/quality/divergencias_aptos_2026.csv"))
    args = parser.parse_args()
    evidence = []
    tests = run(args.dir, evidence=evidence)
    write_evidence(args.evidence, evidence)
    counts = dict(Counter(test["status"] for test in tests))
    status = "FAIL" if counts.get("FAIL") else ("INCONCLUSIVO" if counts.get("INCONCLUSIVO") else "PASS")
    report = {"gerado_em_utc": datetime.now(timezone.utc).isoformat(),
              "resultado": status, "contagem": counts, "testes": tests}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"resultado": status, "contagem": counts,
                      "relatorio": str(args.output),
                      "arquivo_evidencias": str(args.evidence), "registros_evidencias": len(evidence),
                      "falhas": [t["teste"] for t in tests if t["status"] == "FAIL"],
                      "inconclusivos": [t["teste"] for t in tests if t["status"] == "INCONCLUSIVO"]},
                     ensure_ascii=False, indent=2))
    return 1 if counts.get("FAIL") else 0

if __name__ == "__main__":
    sys.exit(main())
