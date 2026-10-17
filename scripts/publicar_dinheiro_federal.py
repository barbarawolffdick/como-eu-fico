"""Publica, por município, dinheiro federal que chega à cidade ao lado do tamanho da economia local.

Fontes de um mesmo ano: PIB municipal (IBGE), benefícios emitidos pelo INSS (Ministério da
Previdência) e FPM creditado (Tesouro Nacional). Cada fluxo fica separado; nada é somado num
"total federal". Reutiliza caches verificados e só substitui a saída após validar as três fontes.

Uso: python -m scripts.publicar_dinheiro_federal [--ano 2023] [--atualizar]
Método e limites: methodology/dinheiro-federal.md
"""
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import gzip
import io
import json
from pathlib import Path
import re
import unicodedata

from scripts.publicar_saude_nacional import obter_com_retentativas
from scripts.publicar_saude_piloto import ROOT, centavos, inteiro

IBGE_MUNICIPIOS = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
PIB_URL = "https://servicodados.ibge.gov.br/api/v3/agregados/5938/periodos/{ano}/variaveis/37?localidades=N6%5Ball%5D"
INSS_URL = "https://www.gov.br/previdencia/pt-br/assuntos/previdencia-social/arquivos/ben_municipios_especie_{ano}.xlsx"
FPM_CATALOGO = "https://www.tesourotransparente.gov.br/ckan/api/3/action/package_show?id=af4e7c47-2132-4d9a-bd7c-34e28a210b03"

GRUPOS_INSS = ("aposentadorias", "aposentadorias_idade", "aposentadorias_invalidez", "aposentadorias_tempo_contribuicao",
               "pensoes_por_morte", "auxilios", "outros_previdenciarios", "previdenciario", "assistencial_e_legislacao_especifica", "total")
CABECALHO_FPM = ["Município", "UF", "ANO", "Mês", "1º Decêndio", "2º Decêndio", "3º Decêndio", "Item transferência", "Transferência"]

# Nomes do Tesouro que diferem do cadastro IBGE, revisados um a um (mesma UF; grafia histórica ou
# renomeação oficial). Nunca por semelhança automática: nome sem correspondência interrompe a publicação.
ALIASES_FPM = {
    ("Major Izidoro", "AL"): "2704401", ("Olho D Água Grande", "AL"): "2705903", ("Olho D Água das Flores", "AL"): "2705705",
    ("Olho D Água do Casado", "AL"): "2705804", ("Tanque D Arca", "AL"): "2709004", ("Dias D Ávila", "BA"): "2910057",
    ("Muquém de São Francisco", "BA"): "2922250", ("Santa Teresinha", "BA"): "2928505", ("Itapagé", "CE"): "2306306",
    ("Barão de Monte Alto", "MG"): "3105509", ("Brasópolis", "MG"): "3108909", ("Ponte Chique", "MG"): "3152131",
    ("São Thomé das Letras", "MG"): "3165206", ("Poxoréo", "MT"): "5107008", ("Santo Antônio do Leverger", "MT"): "5107800",
    ("Eldorado dos Carajás", "PA"): "1502954", ("Santa Isabel do Pará", "PA"): "1506500", ("Belém de São Francisco", "PE"): "2601607",
    ("Iguaraci", "PE"): "2606903", ("Lagoa do Itaenga", "PE"): "2608503", ("Capitão Gervásio de Oliveira", "PI"): "2202455",
    ("Pau DArco", "PI"): "2207793", ("Trajano de Morais", "RJ"): "3305901", ("Arês", "RN"): "2401206",
    ("Açu", "RN"): "2400208",  # renomeado Assú
    ("Presidente Juscelino", "RN"): "2410306",  # renomeado Serra Caiada
    ("São Luiz", "RR"): "1400605", ("Presidente Castelo Branco", "SC"): "4213906", ("São Miguel DOeste", "SC"): "4217204",
    ("Amparo de São Francisco", "SE"): "2800100", ("Gracho Cardoso", "SE"): "2802601", ("Florínia", "SP"): "3516101",
    ("São Luís do Paraitinga", "SP"): "3550001", ("Couto de Magalhães", "TO"): "1706001",
}
# Tolerância da conciliação municipal × linha BRASIL no valor anual do INSS (resíduo não alocado pela fonte).
TOLERANCIA_BRASIL_CENTAVOS = 10_000_00


def json_da_fonte(dados):
    """A API do IBGE responde com gzip mesmo sem pedir; o cache guarda os bytes originais."""
    return json.loads(gzip.decompress(dados) if dados[:2] == b"\x1f\x8b" else dados)


def normalizar(texto):
    return unicodedata.normalize("NFD", str(texto)).encode("ascii", "ignore").decode().lower().strip()


def chave_nome(nome, uf):
    return (normalizar(nome).replace("-", " ").replace("'", ""), uf)


def territorio(municipios_ibge):
    """Cadastro IBGE com UF e região imediata, indexado pelo código de 7 dígitos."""
    saida = {}
    for m in municipios_ibge:
        imediata = m["regiao-imediata"]
        uf = imediata["regiao-intermediaria"]["UF"]
        saida[f"{int(m['id']):07d}"] = {"nome": m["nome"], "uf": uf["sigla"], "regiao": uf["regiao"]["nome"],
                                        "regiao_imediata": {"id": str(imediata["id"]), "nome": imediata["nome"]}}
    return saida


def extrair_pib(documento, ano):
    """PIB a preços correntes (mil reais) → centavos. Valores não numéricos da fonte ficam nulos, nunca zero."""
    variavel = documento[0]
    if variavel["id"] != "37" or variavel["unidade"] != "Mil Reais":
        raise ValueError("Variável ou unidade de PIB inesperada")
    pib = {}
    for serie in variavel["resultados"][0]["series"]:
        codigo = serie["localidade"]["id"]
        if not re.fullmatch(r"\d{7}", codigo) or codigo in pib:
            raise ValueError(f"Código de município inválido ou repetido no PIB: {codigo}")
        bruto = serie["serie"].get(str(ano))
        pib[codigo] = None if bruto is None or not re.fullmatch(r"-?\d+(\.\d+)?", bruto) else centavos(bruto) * 1000
    return pib


def centavos_planilha(valor):
    """Excel guarda somas grandes como double: R$ 37 bilhões chegam com ruído acima de 0,0001 centavo.
    Arredonda ao centavo só quando o excesso é menor que 1/100 de centavo; acima disso, recusa."""
    if isinstance(valor, float):
        bruto = valor * 100
        if abs(bruto - round(bruto)) >= 0.01:
            raise ValueError(f"Valor monetário com fração de centavo: {valor!r}")
        return int(round(bruto))
    return centavos(valor)


def _codigo(valor):
    texto = str(valor).strip() if valor is not None else ""
    texto = texto[:-2] if texto.endswith(".0") else texto
    return texto if re.fullmatch(r"\d{7}", texto) else None


def extrair_aba_inss(linhas, quantidade, cadastro):
    """Uma aba do INSS por espécie. Aceita os três leiautes publicados (2019–2022, 2023, 2024–2025).

    O cabeçalho é localizado pelo rótulo "IBGE"; a coluna do código é decidida pelos dados, porque o
    rótulo já apareceu invertido. Linha sem código só é aceita por nome e UF idênticos ao cadastro.
    """
    linhas = list(linhas)
    h = next((i for i, r in enumerate(linhas[:15]) if any(c and "ibge" in normalizar(c) for c in r[:2])), None)
    if h is None:
        raise ValueError("Cabeçalho do INSS não encontrado")
    rotulos = " | ".join(normalizar(c) for r in linhas[h:h + 3] for c in r[3:13] if c)
    for esperado in ("aposentadorias", "pensoes por morte", "auxilios", "assistenciais", "total"):
        if esperado not in rotulos:
            raise ValueError(f"Leiaute INSS inesperado: falta {esperado!r}")
    dados = linhas[h + 3:]
    ci = next((j for r in dados[:40] for j in (0, 1) if _codigo(r[j])), None)
    if ci is None:
        raise ValueError("Coluna de código IBGE não encontrada")
    ni = 1 - ci
    nomes = {chave_nome(m["nome"], m["uf"]): c for c, m in cadastro.items()}
    converter = inteiro if quantidade else centavos_planilha
    registros, brasil, inferidos = {}, None, []
    for r in dados:
        valores = r[3:13]
        if any(v is None or (isinstance(v, str) and not re.fullmatch(r"\s*-?\d+(\.\d+)?\s*", v)) for v in valores):
            continue  # notas, títulos e linhas em branco
        if "brasil" in (normalizar(r[ci] or ""), normalizar(r[ni] or "")):
            # Soma de milhares de células no Excel: acumula ruído de ponto flutuante. Só serve à conciliação, com tolerância.
            brasil = dict(zip(GRUPOS_INSS, (int(round(float(v))) if quantidade else int(round(float(v) * 100)) for v in valores)))
            continue
        convertidos = dict(zip(GRUPOS_INSS, (converter(v) for v in valores)))
        codigo = _codigo(r[ci])
        if codigo is None:
            uf = r[2] if r[2] and len(str(r[2]).strip()) == 2 else None
            codigo = nomes.get(chave_nome(r[ni], uf)) if r[ni] and uf else None
            if codigo is None:
                raise ValueError(f"Linha INSS sem código e sem correspondência exata: {r[ni]!r}")
            inferidos.append({"codigo_ibge": codigo, "nome_fonte": r[ni], "uf": uf})
        if codigo in registros:
            raise ValueError(f"Município repetido no INSS: {codigo}")
        registros[codigo] = convertidos
    for codigo, g in registros.items():
        if (g["aposentadorias_idade"] + g["aposentadorias_invalidez"] + g["aposentadorias_tempo_contribuicao"] != g["aposentadorias"]
                or g["aposentadorias"] + g["pensoes_por_morte"] + g["auxilios"] + g["outros_previdenciarios"] != g["previdenciario"]
                or g["previdenciario"] + g["assistencial_e_legislacao_especifica"] != g["total"]):
            raise ValueError(f"Soma interna do INSS inconsistente em {codigo}")
    conciliacao = None
    if brasil is not None:
        residuo = brasil["total"] - sum(g["total"] for g in registros.values())
        limite = 0 if quantidade else TOLERANCIA_BRASIL_CENTAVOS
        if abs(residuo) > limite:
            raise ValueError(f"Municípios do INSS não conciliam com a linha BRASIL (resíduo {residuo})")
        conciliacao = {"total_brasil": brasil["total"], "residuo_nao_alocado": residuo}
    return registros, {"municipios": len(registros), "codigos_por_nome_exato": inferidos, "conciliacao_brasil": conciliacao}


def escolher_abas_inss(nomes, ano):
    norm = {n: normalizar(n) for n in nomes}
    quantidade = [n for n, v in norm.items() if v.startswith(("qtd", "quantidade"))]
    anual = [n for n, v in norm.items() if v.startswith("valor") and "dez" not in v and "medio" not in v and v.endswith(str(ano))]
    if len(quantidade) != 1 or len(anual) != 1:
        raise ValueError(f"Abas INSS inesperadas: {nomes}")
    return quantidade[0], anual[0]


def ler_fpm_csv(conteudo):
    """Arquivo mensal do Tesouro (latin-1, ';'). Devolve o mês declarado e as células por chave."""
    leitor = csv.reader(io.StringIO(conteudo.decode("latin-1")), delimiter=";")
    cabecalho = [c for c in next(leitor) if c]
    if cabecalho != CABECALHO_FPM:
        raise ValueError(f"Cabeçalho FPM inesperado: {cabecalho}")
    meses, celulas = set(), {}
    for r in leitor:
        if not r or not any(r):
            continue
        meses.add((r[2], r[3]))
        chave = (r[0], r[1], r[7], r[8])
        if chave in celulas:
            raise ValueError(f"Linha FPM repetida: {chave}")
        celulas[chave] = tuple(centavos(x or 0) for x in r[4:7])
    if len(meses) != 1:
        raise ValueError(f"Arquivo FPM mistura competências: {sorted(meses)}")
    return meses.pop(), celulas


def contem(maior, menor):
    """Verdadeiro se `menor` é versão anterior de `maior`: mesmas chaves ou menos, e valores idênticos onde já havia valor."""
    return set(menor) <= set(maior) and all(m == 0 or m == M for k, v in menor.items() for m, M in zip(v, maior[k]))


def consolidar_fpm(arquivos, ano):
    """Uma versão por mês. Versões repetidas só são aceitas se encadeadas; fica a mais completa."""
    por_mes = defaultdict(list)
    for origem, (competencia, celulas) in arquivos:
        if competencia[0] != str(ano):
            continue
        por_mes[competencia[1]].append((origem, celulas))
    if sorted(por_mes) != [f"{m:02d}" for m in range(1, 13)]:
        raise ValueError(f"FPM {ano} incompleto: meses {sorted(por_mes)}")
    escolhidos, descartados = {}, []
    for mes, versoes in sorted(por_mes.items()):
        versoes.sort(key=lambda v: (len(v[1]), sum(sum(x) for x in v[1].values())), reverse=True)
        maior = versoes[0]
        for origem, celulas in versoes[1:]:
            if not contem(maior[1], celulas):
                raise ValueError(f"Versões divergentes do FPM em {ano}-{mes}; exige reconciliação")
            if celulas != maior[1]:
                descartados.append({"mes": mes, "url": origem["url"], "sha256": origem["sha256"], "motivo": "versão anterior e incompleta do mesmo mês"})
        escolhidos[mes] = maior
    return escolhidos, descartados


def fpm_por_municipio(escolhidos, cadastro):
    """Soma anual da linha FPM/FPM: crédito ao município, já líquido da retenção para o FUNDEB.
    Linhas de FUNDEB (inclusive impostos estaduais) e royalties não entram."""
    indice = {chave_nome(m["nome"], m["uf"]): c for c, m in cadastro.items()}
    if len(indice) != len(cadastro):
        raise ValueError("Cadastro IBGE com nomes ambíguos na mesma UF")
    total, meses = defaultdict(int), defaultdict(set)
    for mes, (_, celulas) in escolhidos.items():
        for (nome, uf, item, transferencia), valores in celulas.items():
            if item != "FPM" or transferencia != "FPM":
                continue
            codigo = ALIASES_FPM.get((nome, uf)) or indice.get(chave_nome(nome, uf))
            if codigo is None:
                raise ValueError(f"Município do FPM sem correspondência: {nome}-{uf}")
            if cadastro[codigo]["uf"] != uf:
                raise ValueError(f"UF do FPM incompatível com o cadastro: {nome}-{uf}")
            total[codigo] += sum(valores)
            meses[codigo].add(mes)
    incompletos = sorted(c for c, m in meses.items() if len(m) != 12)
    if incompletos:
        raise ValueError(f"FPM sem os 12 meses em {len(incompletos)} municípios")
    return dict(total)


def montar_documento(ano, cadastro, pib, inss_valor, inss_qtd, fpm, fontes, validacao):
    motivos = {
        "pib": "O IBGE não publica PIB deste município para o ano (município instalado depois ou valor não numérico).",
        "inss": "A planilha do INSS não traz este município no ano.",
        "fpm": "O Tesouro não registra FPM para este ente no ano (Fernando de Noronha é distrito estadual; ou município instalado depois).",
    }
    registros = {}
    for codigo, m in sorted(cadastro.items()):
        inss = None
        if codigo in inss_valor:
            inss = {"valor_ano_centavos": inss_valor[codigo], "quantidade_dezembro": inss_qtd.get(codigo)}
        r = {"municipio": {"codigo_ibge": codigo, "nome": m["nome"], "uf": m["uf"]},
             "regiao_imediata": m["regiao_imediata"], "regiao": m["regiao"],
             "pib_centavos": pib.get(codigo), "inss": inss,
             "fpm": None if codigo not in fpm else {"valor_ano_centavos": fpm[codigo]}}
        r["ausencias"] = {k: motivos[k] for k, vazio in (("pib", r["pib_centavos"] is None), ("inss", inss is None), ("fpm", r["fpm"] is None)) if vazio}
        registros[codigo] = r
    return {
        "esquema": 1, "ano": ano, "natureza": "observado", "data_geracao": datetime.now(timezone.utc).isoformat(),
        "municipios_referencia": len(cadastro), "unidade_territorial": "municipio_ibge_7_digitos",
        "definicoes": {
            "pib_centavos": "PIB a preços correntes do ano (IBGE, tabela 5938, variável 37), em centavos.",
            "inss.valor_ano_centavos": "Valor líquido (bruto menos descontos) dos benefícios emitidos pelo INSS no ano, por grupo de espécies, "
                                       "no município do órgão pagador — não necessariamente o de residência do beneficiário.",
            "inss.quantidade_dezembro": "Quantidade de benefícios emitidos em dezembro (créditos, não pessoas), mesmo critério territorial.",
            "fpm.valor_ano_centavos": "FPM creditado ao município no ano (soma dos decêndios), líquido da retenção para o FUNDEB.",
        },
        "limites": "Fluxos de natureza diferente: benefícios a pessoas (INSS) e transferência constitucional ao governo municipal (FPM). "
                   "Não somar como investimento federal. Valores nominais. O INSS segue o órgão pagador: taxas por habitante e rankings "
                   "municipais não descrevem os moradores; usar a região imediata para comparações.",
        "fontes": fontes, "validacao": validacao, "cobertura": cobertura(registros), "registros": registros,
    }


def cobertura(registros):
    return {"pib": sum(r["pib_centavos"] is not None for r in registros.values()),
            "inss": sum(r["inss"] is not None for r in registros.values()),
            "fpm": sum(r["fpm"] is not None for r in registros.values())}


def validar_publicacao(documento, cadastro):
    registros = documento["registros"]
    if set(registros) != set(cadastro) or documento["municipios_referencia"] != len(cadastro):
        raise ValueError("Publicação não cobre todo o cadastro municipal")
    if documento["cobertura"] != cobertura(registros):
        raise ValueError("Cobertura declarada não confere com registros")
    for codigo, r in registros.items():
        if r["municipio"]["codigo_ibge"] != codigo:
            raise ValueError("Identificação municipal inconsistente")
        for campo in ("pib", "inss", "fpm"):
            vazio = (r["pib_centavos"] if campo == "pib" else r[campo]) is None
            if vazio != (campo in r["ausencias"]):
                raise ValueError(f"Ausência de {campo} sem motivo declarado em {codigo}")
        if r["inss"] is not None and r["inss"]["valor_ano_centavos"]["total"] < 0:
            raise ValueError("Valor anual do INSS negativo")
    # Proporção mínima esperada: quase todos os municípios do ano têm as três fontes.
    if min(documento["cobertura"].values()) < len(cadastro) - 5:
        raise ValueError(f"Cobertura abaixo do esperado: {documento['cobertura']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ano", type=int, default=2023)
    parser.add_argument("--cache", type=Path, default=ROOT / "data/raw/dinheiro_federal")
    parser.add_argument("--saida", type=Path, default=ROOT / "data/public/dinheiro_federal.json")
    parser.add_argument("--atualizar", action="store_true")
    args = parser.parse_args()
    import openpyxl

    b, origem_ibge = obter_com_retentativas(IBGE_MUNICIPIOS, args.cache, args.atualizar)
    cadastro = territorio(json_da_fonte(b))
    publicado = {r["codigo_ibge"] for r in json.loads((ROOT / "data/public/rankings_2026.json").read_text())["registros"]}
    if set(cadastro) != publicado:
        raise ValueError("Cadastro IBGE diverge dos municípios publicados pelo projeto")

    b, origem_pib = obter_com_retentativas(PIB_URL.format(ano=args.ano), args.cache, args.atualizar)
    pib = extrair_pib(json_da_fonte(b), args.ano)
    if set(pib) - set(cadastro):
        raise ValueError("PIB com município fora do cadastro")
    print(f"PIB {args.ano}: {sum(v is not None for v in pib.values())} municípios.", flush=True)

    b, origem_inss = obter_com_retentativas(INSS_URL.format(ano=args.ano), args.cache, args.atualizar)
    wb = openpyxl.load_workbook(io.BytesIO(b), read_only=True, data_only=True)
    try:
        aba_qtd, aba_ano = escolher_abas_inss(wb.sheetnames, args.ano)
        inss_qtd, val_qtd = extrair_aba_inss(wb[aba_qtd].iter_rows(values_only=True), True, cadastro)
        inss_valor, val_valor = extrair_aba_inss(wb[aba_ano].iter_rows(values_only=True), False, cadastro)
    finally:
        wb.close()
    if set(inss_qtd) != set(inss_valor) or set(inss_valor) - set(cadastro):
        raise ValueError("Abas do INSS cobrem municípios diferentes ou fora do cadastro")
    print(f"INSS {args.ano}: {len(inss_valor)} municípios.", flush=True)

    b, origem_catalogo = obter_com_retentativas(FPM_CATALOGO, args.cache, args.atualizar)
    recursos = [r["url"] for r in json_da_fonte(b)["result"]["resources"]
                if re.search(rf"transferenciamensalmunicipios{args.ano}\d\d", r["url"])]
    arquivos = []
    for url in sorted(set(recursos)):
        conteudo, origem = obter_com_retentativas(url, args.cache, args.atualizar)
        arquivos.append((origem, ler_fpm_csv(conteudo)))
    escolhidos, descartados = consolidar_fpm(arquivos, args.ano)
    fpm = fpm_por_municipio(escolhidos, cadastro)
    print(f"FPM {args.ano}: {len(fpm)} municípios, {len(escolhidos)} meses.", flush=True)

    fontes = {"cadastro_ibge": origem_ibge, "pib": origem_pib, "inss": origem_inss | {"abas": [aba_qtd, aba_ano]},
              "fpm": {"catalogo": origem_catalogo, "licenca": "ODbL",
                      "meses": {mes: v[0] for mes, v in sorted(escolhidos.items())}, "versoes_descartadas": descartados}}
    validacao = {"inss": {"quantidade_dezembro": val_qtd, "valor_ano": val_valor},
                 "fpm": {"municipios": len(fpm), "aliases_revisados": len(ALIASES_FPM)}}
    documento = montar_documento(args.ano, cadastro, pib, inss_valor, inss_qtd, fpm, fontes, validacao)
    validar_publicacao(documento, cadastro)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    temp = args.saida.with_suffix(".tmp")
    temp.write_text(json.dumps(documento, ensure_ascii=False, separators=(",", ":")) + "\n")
    temp.replace(args.saida)
    print(json.dumps({"arquivo": str(args.saida), "ano": args.ano, "cobertura": documento["cobertura"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
