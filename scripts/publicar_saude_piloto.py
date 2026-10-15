"""Publica um piloto municipal do SUS a partir de FNS, APS e Mais Médicos.

Os domínios e períodos permanecem separados. Não executa ingestões TSE/CGU.
Instalação do leitor XLSX: pip install -r requirements-dados.txt.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PILOTO = ("3550308", "2611606", "2312908", "5003702", "5101837")
FNS_URL = "https://portalfns.saude.gov.br/wp-content/uploads/2026/08/Repasse-FAF-com-POPULACAO-2026-acumulado-ate-julho.xlsx"
APS = "https://relatorioaps-prd.saude.gov.br"
PMMB = "https://apidadosabertos.saude.gov.br/atencao-primaria/pmmb-serie-historica"


def inteiro(value):
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("Booleano não é uma contagem")
    try:
        d = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Contagem não numérica") from exc
    if not d.is_finite() or d < 0 or d != d.to_integral_value():
        raise ValueError("Contagem inválida")
    return int(d)


def centavos(value):
    if value is None:
        return None
    try:
        d = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Valor monetário inválido") from exc
    if not d.is_finite():
        raise ValueError("Valor monetário não finito")
    cents = (d * 100).quantize(Decimal("1"))
    if abs(d * 100 - cents) > Decimal("0.0001"):
        raise ValueError("Precisão monetária inesperada")
    return int(cents)


def ponte_ibge(cadastro):
    ponte = {codigo[:6]: codigo for codigo in cadastro}
    if len(ponte) != len(cadastro):
        raise ValueError("Correspondência de seis dígitos ambígua")
    return ponte


def codigo_seis(value):
    code = str(inteiro(value))
    if len(code) != 6 or not code.isascii() or not code.isdigit():
        raise ValueError("Código municipal da fonte inválido")
    return code


def extrair_fns(linhas, cadastro, municipios=PILOTO):
    ponte = ponte_ibge(cadastro)
    registros = {codigo: {"MUNICIPAL": [], "ESTADUAL": []} for codigo in municipios}
    vistas = set()
    linhas_aps = 0
    for numero, linha in linhas:
        if linha.get("GRUPO") != "ATENÇÃO PRIMÁRIA":
            continue
        linhas_aps += 1
        seis = codigo_seis(linha["CO_MUNICIPIO_IBGE"])
        codigo = ponte.get(seis)
        if codigo is None:
            raise ValueError(f"Município FNS fora do cadastro: {seis}")
        if codigo not in registros:
            continue
        if linha["UF"] != cadastro[codigo]["uf"]:
            raise ValueError("UF FNS incompatível com IBGE")
        tipo = linha["TP_REPASSE"]
        if tipo not in registros[codigo]:
            raise ValueError("Esfera de repasse inesperada")
        chave = tuple(str(linha.get(k)) for k in (
            "CO_MUNICIPIO_IBGE", "BLOCO", "ESTRATEGIA", "CNPJ", "BANCO", "AGENCIA", "CONTA", "TP_REPASSE",
        ))
        if chave in vistas:
            raise ValueError("Linha FNS duplicada ou granularidade ambígua")
        vistas.add(chave)
        data = linha.get("DT_ULTIMA_LIBERACAO")
        data = data.date().isoformat() if isinstance(data, datetime) else data
        if data and not "2026-01-01" <= data <= "2026-07-31":
            raise ValueError("Liberação FNS fora do período declarado")
        registros[codigo][tipo].append({
            "linha_origem": numero, "bloco": linha["BLOCO"], "estrategia": linha["ESTRATEGIA"],
            "valor_bruto_centavos": centavos(linha["VL_BRUTO"]),
            "valor_liquido_centavos": centavos(linha["VL_LIQUIDO"]), "ultima_liberacao": data,
        })

    def resumir(rows):
        if not rows:
            return None
        grupos = defaultdict(list)
        for row in rows:
            grupos[(row["bloco"], row["estrategia"])].append(row)
        componentes = []
        for (bloco, estrategia), lista in sorted(grupos.items()):
            valores = [x["valor_liquido_centavos"] for x in lista]
            componentes.append({"bloco": bloco, "estrategia": estrategia,
                "valor_liquido_centavos": None if None in valores else sum(valores),
                "linhas_origem": [x["linha_origem"] for x in lista]})
        valores = [x["valor_liquido_centavos"] for x in rows]
        return {"valor_liquido_centavos": None if None in valores else sum(valores),
                "linhas": len(rows), "componentes": componentes}

    return {codigo: {"periodo_inicio": "202601", "periodo_fim": "202607", "tipo_periodo": "acumulado_de_repasses",
            "municipal": resumir(r["MUNICIPAL"]), "estadual_sediado_na_cidade": resumir(r["ESTADUAL"])}
            for codigo, r in registros.items()}, {"linhas_aps_na_fonte": linhas_aps, "linhas_piloto": len(vistas)}


def extrair_aps(doc, codigo, parcela):
    rows = doc["pagamentos"]
    if not rows:
        return None
    # Vários processos ou competências não podem ser somados como equipes únicas.
    if len(rows) != 1:
        raise ValueError("APS possui múltiplos processos/competências; exige reconciliação")
    row = rows[0]
    if codigo_seis(row["coMunicipioIbge"]) != codigo[:6] or row["nuParcela"] != parcela:
        raise ValueError("Filtro municipal ou temporal da APS não respeitado")
    campos = [("eSF — Saúde da Família", "qtEsfHomologado", "qtEsfTotalPgto"),
              ("eAP — Atenção Primária", "qtEapHomologado", "qtEapTotalPgto"),
              ("eMulti — Equipes multiprofissionais", "qtEmultiHomologado", "qtEmultiPagas")]
    return {"parcela": row["nuParcela"], "competencia_cnes": row["nuCompCnes"], "data_relatorio": doc["data"],
            "equipes": [{"tipo": nome, "homologadas": inteiro(row.get(hom)), "financiadas": inteiro(row.get(pago))}
                        for nome, hom, pago in campos]}


def extrair_pmmb(doc, codigo):
    rows = doc["pmmb_serie_historica"]
    if len(rows) >= 1000:
        raise ValueError("PMMB pode estar truncado; exige paginação")
    datas = set()
    serie = []
    for row in rows:
        if codigo_seis(row["ibge"]) != codigo[:6]:
            raise ValueError("Filtro municipal do PMMB não respeitado")
        data = datetime.strptime(row["dt_referencia"], "%d/%m/%Y").date().isoformat()
        if data in datas:
            raise ValueError("PMMB possui mais de um registro na mesma referência")
        datas.add(data)
        serie.append({"data_referencia": data, "profissionais_ativos": inteiro(row["total_prof_ativos"])})
    serie.sort(key=lambda r: r["data_referencia"])
    return {"ultimo": serie[-1] if serie else None, "serie": serie,
            "motivo": None if serie else "A consulta oficial não retornou observações para esta cidade. Ausência não é zero."}


def obter(url, cache, atualizar=False):
    chave = hashlib.sha256(url.encode()).hexdigest()
    arquivo, meta = cache / f"{chave}.raw", cache / f"{chave}.json"
    if arquivo.exists() and meta.exists() and not atualizar:
        dados = arquivo.read_bytes()
        origem = json.loads(meta.read_text())
        if origem["url"] != url or hashlib.sha256(dados).hexdigest() != origem["sha256"]:
            raise ValueError("Cache da fonte corrompido")
        return dados, origem
    req = urllib.request.Request(url, headers={"User-Agent": "ComoEuFico/1.0", "Accept": "application/json,*/*"})
    with urllib.request.urlopen(req, timeout=60) as resposta:
        dados = resposta.read()
        origem = {"url": url, "url_final": resposta.url, "sha256": hashlib.sha256(dados).hexdigest(),
                  "data_extracao": datetime.now(timezone.utc).isoformat()}
    cache.mkdir(parents=True, exist_ok=True)
    arquivo.write_bytes(dados)
    meta.write_text(json.dumps(origem, ensure_ascii=False))
    return dados, origem


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fns-arquivo", type=Path, help="Reutiliza a planilha oficial já baixada, sem nova transferência.")
    parser.add_argument("--cache", type=Path, default=ROOT / "data/raw/saude/piloto")
    parser.add_argument("--saida", type=Path, default=ROOT / "data/public/saude_piloto.json")
    parser.add_argument("--atualizar", action="store_true")
    args = parser.parse_args()
    import openpyxl

    cadastro = {r["codigo_ibge"]: r for r in json.loads((ROOT / "data/public/rankings_2026.json").read_text())["registros"]}
    if args.fns_arquivo:
        dados = args.fns_arquivo.read_bytes()
        origem_fns = {"url": FNS_URL, "sha256": hashlib.sha256(dados).hexdigest(),
                      "data_extracao": datetime.now(timezone.utc).isoformat(), "reutilizado": True}
        args.cache.mkdir(parents=True, exist_ok=True)
        chave = hashlib.sha256(FNS_URL.encode()).hexdigest()
        (args.cache / f"{chave}.raw").write_bytes(dados)
        (args.cache / f"{chave}.json").write_text(json.dumps(origem_fns, ensure_ascii=False))
        planilha = args.fns_arquivo
    else:
        dados, origem_fns = obter(FNS_URL, args.cache, args.atualizar)
        planilha = args.cache / f"{hashlib.sha256(FNS_URL.encode()).hexdigest()}.raw"
    with planilha.open("rb") as arquivo:
        wb = openpyxl.load_workbook(arquivo, read_only=True, data_only=True)
        try:
            it = wb.active.iter_rows(values_only=True)
            headers = next(it)
            fns, validacao = extrair_fns(((i, dict(zip(headers, row))) for i, row in enumerate(it, 2)), cadastro)
        finally:
            wb.close()

    b, origem_parcelas = obter(APS + "/data/parcelas?ano=2026", args.cache, args.atualizar)
    parcelas = json.loads(b)
    hoje = datetime.now(timezone.utc).strftime("%Y%m")
    parcela = max(p for p in parcelas if p <= hoje and len(p) == 6 and p.isdigit())
    registros = {}
    for codigo in PILOTO:
        qs = urllib.parse.urlencode({"coMunicipio": codigo[:6], "nuParcelaInicio": parcela, "nuParcelaFim": parcela,
                                    "tipoRelatorio": "COMPLETO", "unidadeGeografica": "MUNICIPIO"})
        a, origem_aps = obter(APS + "/financiamento/pagamento?" + qs, args.cache, args.atualizar)
        p, origem_pmmb = obter(PMMB + "?" + urllib.parse.urlencode({"ibge": codigo[:6], "limit": 1000, "offset": 0}), args.cache, args.atualizar)
        registros[codigo] = {"municipio": {k: cadastro[codigo][k] for k in ("codigo_ibge", "nome", "uf")},
            "fns": fns[codigo], "aps": extrair_aps(json.loads(a), codigo, parcela), "mais_medicos": extrair_pmmb(json.loads(p), codigo),
            "proveniencia": {"fns": origem_fns, "aps": origem_aps, "mais_medicos": origem_pmmb}}
    documento = {"esquema": 1, "status": "PILOTO", "data_geracao": datetime.now(timezone.utc).isoformat(),
        "municipios_piloto": list(PILOTO), "municipios_referencia": len(cadastro), "unidade_territorial": "municipio_ibge_7_digitos",
        "metodo_ponte": "Código de seis dígitos conferido com prefixo único do cadastro IBGE de sete dígitos; sem pareamento por nome.",
        "natureza": "observado", "fonte_parcelas": origem_parcelas, "validacao": validacao, "registros": registros}
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    temporario = args.saida.with_suffix(".tmp")
    temporario.write_text(json.dumps(documento, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporario.replace(args.saida)
    print(json.dumps({"arquivo": str(args.saida), "municipios": len(registros), "parcela_aps": parcela, "validacao": validacao}, ensure_ascii=False))


if __name__ == "__main__":
    main()
