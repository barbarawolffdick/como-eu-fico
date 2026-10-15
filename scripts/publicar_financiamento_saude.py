"""Integra FNS, despesas SIOPS e rede CNES, preservando escopos e períodos.

Execução: python -m scripts.publicar_financiamento_saude. Não ingere TSE/CGU.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import html
import io
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
import unicodedata
import zipfile

from scripts.publicar_saude_nacional import obter_com_retentativas
from scripts.publicar_saude_piloto import ROOT, FNS_URL, centavos, codigo_seis, inteiro, ponte_ibge

CACHE = ROOT / "data/raw/saude/expansao"
FNS = {2024: "https://portalfns.saude.gov.br/idg_download/repasse-faf-com-populacao-2024/",
       2025: "https://portalfns.saude.gov.br/wp-content/uploads/2026/01/REPASSE-FAF-COM-POPULACAO-2025.xlsx",
       2026: FNS_URL}
SIOPS = "https://portalfns.saude.gov.br/idg_download/siops-despesas-por-fonte-subfuncao-natureza-municipais-2025-6o-bimestre/"
CNES = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/CNES/cnes_estabelecimentos_csv.zip"
LEITOS = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/Leitos_SUS/Leitos_csv_2026.zip"
TABNET = "https://tabnet.datasus.gov.br/cgi/tabcgi.exe?cnes/cnv/equipobr.def"
TABNET_FORM = "https://tabnet.datasus.gov.br/cgi/deftohtm.exe?cnes/cnv/equipobr.def"
FONTE_FEDERAL = "Transferência Fundo a Fundo de Recursos do SUS Provenientes do Governo Federal"
FONTES_SIOPS = {
    "Receitas de Impostos e Transferencias de Impostos": "Impostos e transferências de impostos",
    FONTE_FEDERAL: "Transferências federais fundo a fundo",
    "Transferência Fundo a Fundo de Recursos do SUS Provenientes do Governo Estadual": "Transferências estaduais fundo a fundo",
    "Outros Recursos Vinculados à Saúde": "Outros recursos vinculados à saúde",
    "Recursos Ordinários - Fonte Livre": "Recursos ordinários — fonte livre",
    "Transferência de Convênios ou de Contratos de Repasse Vinculados à Saúde": "Convênios e contratos de repasse",
    "Royalties do Petróleo Vinculados à Saúde (Recursos do Pré-Sal)": "Royalties do petróleo",
    "Despesas Totais Transferências da União - inciso I do art. 5º da Lei Complementar 173 de 2020": "Transferências federais — LC 173/2020",
    "Operações de Crédito Vinculadas à Saúde": "Operações de crédito",
}


def soma_validada(valores):
    valores = list(valores)
    return None if not valores or None in valores else sum(valores)


def percentual(numerador, denominador):
    if numerador is None or denominador is None or denominador <= 0:
        return None
    return float((Decimal(numerador) * 100 / Decimal(denominador)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def dinheiro(value):
    if value is None or value in ("", "-"):
        return None
    if isinstance(value, str) and "," in value:
        value = value.replace(".", "").replace(",", ".")
    return centavos(value)


def ler_fns(path, ano):
    if ano == 2024:
        with path.open(encoding="utf-8-sig", newline="") as arquivo:
            yield from enumerate(csv.DictReader(arquivo, delimiter=";"), 2)
    else:
        import openpyxl
        with path.open("rb") as arquivo:
            wb = openpyxl.load_workbook(arquivo, read_only=True, data_only=True)
            try:
                it = wb.active.iter_rows(values_only=True)
                headers = next(it)
                yield from ((i, dict(zip(headers, row))) for i, row in enumerate(it, 2))
            finally:
                wb.close()


def resumir_fns(linhas, cadastro, ano, mes_fim):
    ponte = ponte_ibge(cadastro)
    grupos = defaultdict(list)
    vistos = set()
    total = 0
    for numero, r in linhas:
        total += 1
        codigo = ponte.get(codigo_seis(r["CO_MUNICIPIO_IBGE"]))
        if codigo is None or r["UF"] != cadastro[codigo]["uf"]:
            raise ValueError("Território FNS fora do cadastro")
        esfera = r["TP_REPASSE"]
        if esfera not in ("MUNICIPAL", "ESTADUAL") or r["ST_FAF"] != "S":
            raise ValueError("Escopo FNS inesperado; exige nova classificação")
        entidade = r["ENTIDADE"].strip()
        if entidade == "AGENCIA PARA O DESENVOLVIMENTO DA ATENCAO PRIMARIA A SAUDE":
            esfera = "OUTROS"
        elif esfera == "MUNICIPAL":
            nome = "".join(c for c in unicodedata.normalize("NFKD", entidade.upper()) if not unicodedata.combining(c))
            if not any(p in nome for p in ("FUNDO", "FMS", "MUNICIP", "PREFEIT")):
                raise ValueError(f"Destinatário municipal exige validação: {entidade}")
        chave = tuple(str(r[k]) for k in ("CO_MUNICIPIO_IBGE", "BLOCO", "GRUPO", "ESTRATEGIA", "CNPJ", "BANCO", "AGENCIA", "CONTA", "TP_REPASSE"))
        if chave in vistos:
            raise ValueError("Granularidade FNS duplicada")
        vistos.add(chave)
        dt = r["DT_ULTIMA_LIBERACAO"]
        dt = dt.date().isoformat() if isinstance(dt, datetime) else str(dt)[:10]
        if not f"{ano}-01-01" <= dt <= f"{ano}-{mes_fim:02d}-31":
            raise ValueError("Liberação fora do período FNS")
        grupos[(codigo, esfera)].append({"linha_origem": numero, "grupo": r["GRUPO"], "bloco": r["BLOCO"],
            "estrategia": r["ESTRATEGIA"], "destinatario": entidade, "esfera_original": r["TP_REPASSE"], "valor_centavos": dinheiro(r["VL_LIQUIDO"]),
            "emenda_identificada": r["ESTRATEGIA"].startswith("EMENDA - ")})

    def resumo(rows):
        if not rows:
            return None
        por_grupo = defaultdict(list)
        por_bloco = defaultdict(list)
        for r in rows:
            por_grupo[r["grupo"]].append(r)
            b = r["bloco"].upper()
            if b.startswith("ESTRUTURAÇÃO"):
                finalidade = "Estruturação da rede"
            elif b.startswith("MANUTENÇÃO"):
                finalidade = "Manutenção dos serviços"
            elif b == "":
                finalidade = "Bloco não informado na fonte"
            else:
                raise ValueError("Bloco FNS não classificado")
            por_bloco[finalidade].append(r)
        total = soma_validada(r["valor_centavos"] for r in rows)
        emendas = [r for r in rows if r["emenda_identificada"]]
        return {"valor_centavos": total, "linhas": len(rows),
            "destinatarios": sorted({r["destinatario"] for r in rows}),
            "esferas_originais": sorted({r["esfera_original"] for r in rows}),
            "grupos": [{"nome": g, "valor_centavos": soma_validada(r["valor_centavos"] for r in lista),
                        "linhas_origem": [r["linha_origem"] for r in lista]} for g, lista in sorted(por_grupo.items())],
            "finalidades": [{"nome": g, "valor_centavos": soma_validada(r["valor_centavos"] for r in lista)} for g, lista in sorted(por_bloco.items())],
            "emendas": {"valor_centavos": soma_validada(r["valor_centavos"] for r in emendas),
                "percentual_do_total": percentual(soma_validada(r["valor_centavos"] for r in emendas), total),
                "linhas_origem": [r["linha_origem"] for r in emendas]}}
    return {codigo: {"ano": ano, "inicio": f"{ano}01", "fim": f"{ano}{mes_fim:02d}", "completo": mes_fim == 12,
        "municipal": resumo(grupos[(codigo, "MUNICIPAL")]), "estadual_sediado_na_cidade": resumo(grupos[(codigo, "ESTADUAL")]),
        "outros_destinatarios_sediados_na_cidade": resumo(grupos[(codigo, "OUTROS")])}
        for codigo in cadastro}, {"linhas_fonte": total, "linhas_conciliadas": len(vistos)}


def extrair_siops(linhas, cadastro):
    ponte = ponte_ibge(cadastro)
    grupos = defaultdict(list)
    vistos = set()
    total = 0
    for numero, r in linhas:
        total += 1
        # Apenas o nível econômico superior, sem somar seus filhos contábeis.
        if r["Fase"] not in ("Despesas Liquidadas", "Despesas Pagas") or r["Codigo"] not in ("3.0.00.00.00.00", "4.0.00.00.00.00"):
            continue
        if r["Ano"] != "2025" or not r["Data_Homologacao"]:
            raise ValueError("SIOPS fora do exercício homologado")
        codigo = ponte.get(codigo_seis(r["Cód.Município"]))
        if codigo is None or cadastro[codigo]["uf"] != r["UF"]:
            raise ValueError("Território SIOPS não conciliado")
        if r["Fonte"] not in FONTES_SIOPS:
            raise ValueError("Fonte SIOPS exige classificação explícita")
        chave = (codigo, r["Fonte"], r["Subfuncao"], r["Codigo"], r["Fase"])
        if chave in vistos:
            raise ValueError("SIOPS duplicado por nível contábil")
        vistos.add(chave)
        grupos[codigo].append({"fonte": r["Fonte"], "fase": r["Fase"], "valor_centavos": dinheiro(r["Valor"]),
            "linha_origem": numero, "homologacao": r["Data_Homologacao"], "transmissao": r["Data_Transmissao"]})
    registros = {}
    for codigo in cadastro:
        rows = grupos[codigo]
        if not rows:
            registros[codigo] = None
            continue
        fases = {}
        for fase in ("Despesas Liquidadas", "Despesas Pagas"):
            valores = defaultdict(list)
            for r in rows:
                if r["fase"] == fase:
                    valores[r["fonte"]].append(r)
            fontes = [{"fonte": fonte, "nome": FONTES_SIOPS[fonte],
                "valor_centavos": soma_validada(x["valor_centavos"] for x in lista),
                "linhas_origem": [x["linha_origem"] for x in lista]} for fonte, lista in sorted(valores.items())]
            soma = soma_validada(f["valor_centavos"] for f in fontes)
            federal = next((f["valor_centavos"] for f in fontes if f["fonte"] == FONTE_FEDERAL), None)
            fases[fase] = {"total_centavos": soma, "fontes": fontes,
                          "percentual_fonte_federal_faf": percentual(federal, soma)}
        registros[codigo] = {"ano": 2025, "bimestre": 6, "fases": fases,
            "homologacao": max(r["homologacao"] for r in rows), "transmissao": max(r["transmissao"] for r in rows)}
    return registros, {"linhas_fonte": total, "linhas_superiores_selecionadas": len(vistos)}


def extrair_cnes(linhas, cadastro):
    ponte = ponte_ibge(cadastro)
    grupos = defaultdict(list)
    vistos = set()
    df = Counter()
    total = 0
    for numero, r in linhas:
        total += 1
        cnes = str(inteiro(r["CO_CNES"])).zfill(7)
        if cnes in vistos:
            raise ValueError("CNES duplicado no cadastro")
        vistos.add(cnes)
        seis = codigo_seis(r["CO_IBGE"])
        if seis[:2] != r["CO_UF"]:
            raise ValueError("UF CNES incompatível com código")
        codigo = ponte.get(seis)
        if codigo is None and r["CO_UF"] == "53":
            # O cadastro territorial do produto representa todo o DF em Brasília.
            codigo = "5300108"
            df[seis] += 1
        if codigo is None:
            raise ValueError("Código CNES não conciliado")
        if r["CO_MOTIVO_DESAB"].strip() or r["CO_AMBULATORIAL_SUS"] != "SIM":
            continue
        grupos[codigo].append({"cnes": cnes, "nome": r["NO_FANTASIA"], "tipo": inteiro(r["TP_UNIDADE"]),
            "gestao": r["TP_GESTAO"], "codigo_local_fonte": seis, "linha_origem": numero})
    registros = {}
    for codigo in cadastro:
        rows = sorted(grupos[codigo], key=lambda x: (x["tipo"] != 2, x["nome"], x["cnes"]))
        registros[codigo] = None if not rows else {"estabelecimentos_sus_ambulatorial": len(rows),
            "ubs": sum(r["tipo"] == 2 for r in rows),
            "postos": sum(r["tipo"] == 1 for r in rows),
            "unidades_exibidas": rows[:10], "lista_limitada": len(rows) > 10}
    return registros, {"linhas_fonte": total, "registros_df_agregados_por_uf": dict(sorted(df.items()))}


def extrair_leitos(linhas, cadastro):
    ponte = ponte_ibge(cadastro)
    grupos = defaultdict(list)
    vistos = set()
    total = 0
    competencias = Counter()
    for numero, r in linhas:
        total += 1
        competencias[r["COMP"]] += 1
        if r["COMP"] != "202608":
            continue
        codigo = ponte.get(codigo_seis(r["CO_IBGE"]))
        if codigo is None or cadastro[codigo]["uf"] != r["UF"]:
            raise ValueError("Território de leitos não conciliado")
        cnes = str(inteiro(r["CNES"])).zfill(7)
        if cnes in vistos:
            raise ValueError("Leitos repetidos por CNES na competência")
        vistos.add(cnes)
        if r["MOTIVO_DESABILITACAO"].strip():
            continue
        normalizar = lambda v: inteiro(None if v == "" else v)
        grupos[codigo].append({"cnes": cnes, "nome": r["NOME_ESTABELECIMENTO"], "gestao": r["TP_GESTAO"],
            "leitos_sus": normalizar(r["LEITOS_SUS"]), "leitos_existentes": normalizar(r["LEITOS_EXISTENTES"]),
            "uti_sus": normalizar(r["UTI_TOTAL_SUS"]), "linha_origem": numero})
    if max(competencias) != "202608":
        raise ValueError("Competência de leitos mudou; revisar recorte")
    return {c: None if not grupos[c] else {"competencia": "202608", "hospitais_na_fonte": len(grupos[c]),
            "leitos_sus": soma_validada(r["leitos_sus"] for r in grupos[c]),
            "uti_sus": soma_validada(r["uti_sus"] for r in grupos[c]),
            "unidades": sorted(grupos[c], key=lambda r: r["nome"])} for c in cadastro}, {"linhas_fonte": total, "competencias": dict(competencias)}


def parametros_equipamento(medida):
    filtros = ('SRegião', 'SUnidade_da_Federação', 'SMunicípio', 'SMunicípio_gestor', 'SCapital', 'SRegião_de_Saúde_(CIR)', 'SMacrorregião_de_Saúde', 'SMicrorregião_IBGE', 'SRegião_Metropolitana_-_RIDE', 'STerritório_da_Cidadania', 'SMesorregião_PNDR', 'SAmazônia_Legal', 'SSemiárido', 'SFaixa_de_Fronteira', 'SZona_de_Fronteira', 'SMunicípio_de_extrema_pobreza', 'SEnsino/Pesquisa', 'SNatureza_Jurídica', 'SEsfera_Jurídica', 'SEsfera_Administrativa', 'SNatureza', 'STipo_de_Estabelecimento', 'STipo_de_Gestão', 'STipo_de_Prestador', 'SEquipamento', 'SGrupo_de_Equipamentos', 'SEquipamento_selecionado')
    return {**{nome: "TODAS_AS_CATEGORIAS__" for nome in filtros},
        "Linha": "Município", "Coluna": "Equipamento_selecionado", "Incremento": medida,
        "Arquivos": "eqbr2608.dbf", "formato": "prn", "mostre": "Mostra", "zeradas": "exibirlz"}


def obter_equipamento(cache, medida, atualizar=False):
    params = parametros_equipamento(medida)
    corpo = urllib.parse.urlencode(params, encoding="latin1").encode()
    chave = hashlib.sha256(TABNET.encode() + corpo).hexdigest()
    path, meta = cache / f"{chave}.raw", cache / f"{chave}.json"
    if path.exists() and meta.exists() and not atualizar:
        b, m = path.read_bytes(), json.loads(meta.read_text())
        if m["parametros"] != params or m["sha256"] != hashlib.sha256(b).hexdigest():
            raise ValueError("Cache Tabnet inválido")
        return b, m
    req = urllib.request.Request(TABNET, data=corpo, headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "ComoEuFico/1.0"})
    with urllib.request.urlopen(req, timeout=120) as res:
        b = res.read()
    m = {"url": TABNET, "metodo": "POST", "parametros": params, "sha256": hashlib.sha256(b).hexdigest(),
         "data_extracao": datetime.now(timezone.utc).isoformat()}
    cache.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b)
    meta.write_text(json.dumps(m, ensure_ascii=False))
    return b, m


def extrair_equipamento(dados, cadastro):
    texto = dados.decode("latin1")
    if "Ago/2026" not in texto:
        raise ValueError("Referência Tabnet não confere")
    match = re.search(r"<PRE>(.*?)</PRE>", texto, re.I | re.S)
    if not match:
        raise ValueError("Tabela Tabnet ausente")
    tabela = list(csv.reader(io.StringIO(html.unescape(match.group(1))), delimiter=";"))
    headers = tabela[1] if not tabela[0] else tabela[0]
    if headers[0] != "Município" or headers[-1] != "Total" or len(headers) != 8:
        raise ValueError("Colunas de equipamentos inesperadas")
    ponte = ponte_ibge(cadastro)
    registros = {}
    ignorados = []
    totais = None
    for linha in tabela:
        if not linha or linha == headers or linha == ["&"]:
            continue
        if linha[0] == "Total":
            totais = [inteiro(v.replace(".", "")) for v in linha[1:-1]]
            continue
        match = re.match(r"^(\d{6}) ", linha[0])
        if not match or match[1] == "000000":
            ignorados.append(linha)
            continue
        codigo = ponte.get(match[1])
        if codigo is None or codigo in registros:
            raise ValueError("Território Tabnet inválido ou duplicado")
        # O traço publicado não é convertido em zero para preencher a interface.
        registros[codigo] = [{"tipo": headers[i], "valor": None if v == "-" else inteiro(v.replace(".", ""))}
                              for i, v in enumerate(linha[1:-1], 1)]
    if totais is None:
        raise ValueError("Tabela Tabnet sem total de controle")
    for i, total in enumerate(totais):
        if sum(r[i]["valor"] for r in registros.values() if r[i]["valor"] is not None) != total:
            raise ValueError("Total Tabnet inclui território não conciliado")
    return registros, {"municipios_na_tabela": len(registros), "linhas_ignoradas": ignorados, "totais_controle": totais}


def linhas_zip(path, encoding):
    with zipfile.ZipFile(path) as z:
        if len(z.namelist()) != 1:
            raise ValueError("ZIP deve conter um único CSV")
        with z.open(z.namelist()[0]) as raw:
            yield from enumerate(csv.DictReader(io.TextIOWrapper(raw, encoding=encoding), delimiter=";"), 2)


def validar(documento, cadastro):
    if set(documento["registros"]) != set(cadastro):
        raise ValueError("Cadastro municipal incompleto")
    for codigo, r in documento["registros"].items():
        for periodo in r["fns"]:
            for esfera in ("municipal", "estadual_sediado_na_cidade", "outros_destinatarios_sediados_na_cidade"):
                v = periodo[esfera]
                if v is not None and (soma_validada(g["valor_centavos"] for g in v["grupos"]) != v["valor_centavos"] or
                                      soma_validada(g["valor_centavos"] for g in v["finalidades"]) != v["valor_centavos"]):
                    raise ValueError("Totais FNS não reconciliados")
        total = r["fns"][-1]["municipal"]
        if total is None and r["centavos_por_habitante"] is not None:
            raise ValueError("Indicador por habitante sem numerador")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=CACHE)
    parser.add_argument("--saida", type=Path, default=ROOT / "data/public/financiamento_saude.json")
    parser.add_argument("--atualizar", action="store_true")
    args = parser.parse_args()
    cadastro = {r["codigo_ibge"]: r for r in json.loads((ROOT / "data/public/rankings_2026.json").read_text())["registros"]}
    fontes, validacao = {}, {}

    def fonte(nome, url):
        _, origem = obter_com_retentativas(url, args.cache, args.atualizar)
        fontes[nome] = origem
        return args.cache / f"{hashlib.sha256(url.encode()).hexdigest()}.raw"

    anos = {}
    for ano, url in FNS.items():
        print(f"FNS {ano}: validando todos os grupos…", flush=True)
        path = fonte(f"fns_{ano}", url)
        anos[ano], validacao[f"fns_{ano}"] = resumir_fns(ler_fns(path, ano), cadastro, ano, 7 if ano == 2026 else 12)
    print("SIOPS: despesas homologadas, sem somar níveis contábeis…", flush=True)
    siops, validacao["siops"] = extrair_siops(linhas_zip(fonte("siops", SIOPS), "utf-8-sig"), cadastro)
    print("CNES: estabelecimentos e leitos…", flush=True)
    cnes, validacao["cnes"] = extrair_cnes(linhas_zip(fonte("cnes", CNES), "latin1"), cadastro)
    leitos, validacao["leitos"] = extrair_leitos(linhas_zip(fonte("leitos", LEITOS), "latin1"), cadastro)
    equipamento = {}
    for nome, medida in (("equipamentos_em_uso", "Equipamentos_em_Uso"), ("estabelecimentos_com_equipamento_sus", "Estab_c/_Equip_SUS")):
        b, fontes[nome] = obter_equipamento(args.cache, medida, args.atualizar)
        equipamento[nome], validacao[nome] = extrair_equipamento(b, cadastro)
    registros = {}
    for c, m in sorted(cadastro.items()):
        atual = anos[2026][c]["municipal"]
        anterior, ultimo = anos[2024][c]["municipal"], anos[2025][c]["municipal"]
        variacao = None
        if anterior and ultimo and anterior["valor_centavos"] is not None and ultimo["valor_centavos"] is not None:
            variacao = percentual(ultimo["valor_centavos"] - anterior["valor_centavos"], anterior["valor_centavos"])
        pop = inteiro(m["populacao"])
        por_hab = None if not atual or atual["valor_centavos"] is None or not pop else int((Decimal(atual["valor_centavos"]) / pop).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        registros[c] = {"municipio": {k: m[k] for k in ("codigo_ibge", "nome", "uf", "populacao", "ano_populacao")},
            "fns": [anos[a][c] for a in sorted(anos)], "variacao_anual_2024_2025_percentual": variacao,
            "centavos_por_habitante": por_hab, "siops": siops[c], "cnes": cnes[c], "leitos": leitos[c],
            "equipamentos": {"competencia": "202608", **{nome: rows.get(c) for nome, rows in equipamento.items()}}}
    cobertura = {nome: sum(pred(r) for r in registros.values()) for nome, pred in {
        "fns_2026": lambda r: r["fns"][-1]["municipal"] is not None,
        "siops": lambda r: r["siops"] is not None,
        "cnes": lambda r: r["cnes"] is not None,
        "leitos": lambda r: r["leitos"] is not None}.items()}
    doc = {"esquema": 1, "natureza": "observado", "municipios": len(cadastro),
        "data_geracao": datetime.now(timezone.utc).isoformat(), "fontes": fontes,
        "validacao": validacao, "cobertura": cobertura, "registros": registros}
    validar(doc, cadastro)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    temp = args.saida.with_suffix(".tmp")
    temp.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n")
    temp.replace(args.saida)
    print(json.dumps({"resultado": "PASS", "municipios": len(registros), "cobertura": cobertura}, ensure_ascii=False))


if __name__ == "__main__":
    main()
