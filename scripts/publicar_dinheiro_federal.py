"""Publica, por município, dinheiro federal que chega à cidade ao lado do tamanho da economia local.

Fontes de um mesmo ano: PIB municipal (IBGE), benefícios emitidos pelo INSS (Ministério da
Previdência) e FPM creditado (Tesouro Nacional). Cada fluxo fica separado; nada é somado num
"total federal". Reutiliza caches verificados e só substitui a saída após validar as três fontes.

Uso: python -m scripts.publicar_dinheiro_federal [--ano 2023] [--pib observado|estimado|ausente] [--atualizar]
     python -m scripts.publicar_dinheiro_federal --diagnosticar 2019 2020 ... (só relata; não publica)
Método e limites: methodology/dinheiro-federal.md
"""
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
from decimal import Decimal
import gzip
import io
import json
from pathlib import Path
import re
from statistics import median
import unicodedata

from scripts.publicar_saude_nacional import obter_com_retentativas
from scripts.publicar_saude_piloto import ROOT, centavos, inteiro

IBGE_MUNICIPIOS = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
PIB_URL = "https://servicodados.ibge.gov.br/api/v3/agregados/5938/periodos/{ano}/variaveis/37?localidades=N6%5Ball%5D"
# Contas trimestrais, valores correntes: PIB a preços de mercado do Brasil (milhões de reais).
PIB_TRIMESTRAL_URL = ("https://servicodados.ibge.gov.br/api/v3/agregados/1846/periodos/{periodos}/variaveis/585"
                      "?localidades=N1%5Ball%5D&classificacao=11255%5B90707%5D")
INSS_URL = "https://www.gov.br/previdencia/pt-br/assuntos/previdencia-social/arquivos/ben_municipios_especie_{ano}.xlsx"
FPM_CATALOGO = "https://www.tesourotransparente.gov.br/ckan/api/3/action/package_show?id=af4e7c47-2132-4d9a-bd7c-34e28a210b03"

GRUPOS_INSS = ("aposentadorias", "aposentadorias_idade", "aposentadorias_invalidez", "aposentadorias_tempo_contribuicao",
               "pensoes_por_morte", "auxilios", "outros_previdenciarios", "previdenciario", "assistencial_e_legislacao_especifica", "total")
CABECALHO_FPM = ["Município", "UF", "ANO", "Mês", "1º Decêndio", "2º Decêndio", "3º Decêndio", "Item transferência", "Transferência"]
# Valores do FPM: ponto decimal (padrão) ou, no arquivo de 2021-08 exportado do Excel, também vírgula decimal com ponto de
# milhar e "-" contábil para zero. Ponto seguido de três dígitos sem vírgula é ambíguo (milhar ou decimal) e é recusado.
VALOR_PONTO = re.compile(r"-?\d+(\.\d{1,2})?")
VALOR_VIRGULA = re.compile(r"-?\d{1,3}(\.\d{3})*,\d{1,2}")
# Um mês cujo total nacional de FPM foge desta razão em relação à mediana dos demais meses do ano é recusado. A variação
# legítima entre meses fica abaixo de 2×; erro de escala (valor sem ponto decimal) multiplica por 100.
LIMITE_ESCALA_FPM = 4

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
# Ruído relativo aceito em células do Excel do INSS. Em 2019 as células municipais são somas em ponto flutuante feitas pela
# fonte: o maior desvio observado é 2,2e-13 do valor (0,17 centavo em São Paulo, R$ 47,8 bilhões); o limite dá margem de 4×.
# Fração real de centavo (ex.: valor em reais com três casas) continua recusada em qualquer célula abaixo de R$ 5 bilhões.
RUIDO_RELATIVO_PLANILHA = 1e-12
# Diferença aceita entre a soma do PIB municipal do ano-base e o PIB nacional das contas trimestrais (revisões entre bases).
TOLERANCIA_PIB_NACIONAL = Decimal("0.02")


class FpmIncompleto(ValueError):
    """Ano do FPM com meses ausentes, parciais ou de escala suspeita; `problemas` mapeia mês → motivo."""

    def __init__(self, ano, problemas):
        self.ano, self.problemas = ano, problemas
        super().__init__(f"FPM {ano} incompleto: " + "; ".join(f"{ano}-{m}: {p}" for m, p in problemas.items()))


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
    if not documento:
        raise ValueError(f"IBGE sem PIB municipal de {ano}: use --pib estimado ou --pib ausente "
                         "(se o IBGE já publicou, rode com --atualizar, pois a resposta vazia fica no cache)")
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


def pib_nacional_anual(documento, ano):
    """Soma dos quatro trimestres do PIB a preços de mercado (IBGE 1846, milhões de reais). Ano incompleto interrompe."""
    variavel = documento[0]
    if variavel["id"] != "585" or variavel["unidade"] != "Milhões de Reais":
        raise ValueError("Variável ou unidade do PIB trimestral inesperada")
    resultado = variavel["resultados"][0]
    if [c["categoria"] for c in resultado["classificacoes"]] != [{"90707": "PIB a preços de mercado"}]:
        raise ValueError("Recorte do PIB trimestral inesperado")
    serie = resultado["series"][0]["serie"]
    trimestres = [serie.get(f"{ano}{t:02d}") for t in range(1, 5)]
    if not all(v and re.fullmatch(r"\d+(\.\d+)?", v) for v in trimestres):
        raise ValueError(f"Contas trimestrais sem os quatro trimestres de {ano}")
    return sum(Decimal(v) for v in trimestres)


def estimar_pib(pib_base, nacional_base, nacional_ano):
    """Estimativa rotulada: PIB municipal do ano-base × variação do PIB nacional nominal. Supõe que todo município
    cresceu como o país; arredonda a mil reais (unidade da fonte) para não sugerir precisão. Nulo continua nulo."""
    soma = sum(v for v in pib_base.values() if v is not None)
    if abs(Decimal(soma) / (nacional_base * 100_000_000) - 1) > TOLERANCIA_PIB_NACIONAL:
        raise ValueError("PIB municipal do ano-base não confere com as contas trimestrais")
    fator = (nacional_ano / nacional_base).quantize(Decimal("0.000001"))
    estimado = {c: None if v is None else int((v * fator / 100_000).quantize(Decimal(1))) * 100_000 for c, v in pib_base.items()}
    return estimado, fator


def centavos_planilha(valor):
    """Excel guarda somas grandes como double: R$ 37 bilhões chegam com ruído acima de 0,0001 centavo.
    Arredonda ao centavo só quando o excesso é menor que 1/100 de centavo ou que o ruído relativo de somas em ponto
    flutuante (RUIDO_RELATIVO_PLANILHA); acima disso, recusa."""
    if isinstance(valor, float):
        bruto = valor * 100
        if abs(bruto - round(bruto)) >= max(0.01, abs(bruto) * RUIDO_RELATIVO_PLANILHA):
            raise ValueError(f"Valor monetário com fração de centavo: {valor!r}")
        return int(round(bruto))
    return centavos(valor)


def _codigo(valor):
    texto = str(valor).strip() if valor is not None else ""
    texto = texto[:-2] if texto.endswith(".0") else texto
    return texto if re.fullmatch(r"\d{7}", texto) else None


def linha_de_total(*rotulos):
    """Linha nacional: rotulada "BRASIL" (2023–2025), "Total" na coluna do código e nome vazio (2019–2022) ou sem rótulo.
    Município com "Brasil" no nome não casa, porque o rótulo inteiro precisa ser o do total."""
    return {normalizar(r) for r in rotulos if r is not None} - {"", "#n/a"} <= {"brasil", "total"}


def extrair_aba_inss(linhas, quantidade, cadastro):
    """Uma aba do INSS por espécie. Aceita os três leiautes publicados (2019–2022, 2023, 2024–2025).

    O cabeçalho é localizado pelo rótulo "IBGE"; a coluna do código é decidida pelos dados, porque o
    rótulo já apareceu invertido. Linha sem código só é aceita por nome e UF idênticos ao cadastro.
    A linha de total nacional, rotulada ou não, só serve à conciliação e precisa ser única.
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
        if linha_de_total(r[ci], r[ni]):
            if brasil is not None:
                raise ValueError("Mais de uma linha de total nacional no INSS")
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


def valor_fpm(texto, formatos):
    """Célula monetária do FPM → centavos, registrando em `formatos` a grafia encontrada. Vazio é zero (leiaute original)."""
    t = texto.strip()
    if not t:
        return 0
    if t == "-":
        formatos.add("traco_zero")
        return 0
    if VALOR_PONTO.fullmatch(t):
        formatos.add("ponto_decimal")
        return centavos(t)
    if VALOR_VIRGULA.fullmatch(t):
        formatos.add("virgula_decimal")
        return centavos(t.replace(".", "").replace(",", "."))
    raise ValueError(f"Valor monetário inválido no FPM: {texto!r}")


def ler_fpm_csv(conteudo, formatos=None):
    """Arquivo mensal do Tesouro (latin-1, ';'). Devolve o mês declarado e as células por chave.
    O cabeçalho é comparado sem caixa ("Ano" em 2021-08) e o mês é normalizado a dois dígitos ("8" → "08")."""
    formatos = set() if formatos is None else formatos
    leitor = csv.reader(io.StringIO(conteudo.decode("latin-1")), delimiter=";")
    cabecalho = [c.strip() for c in next(leitor) if c]
    if [c.casefold() for c in cabecalho] != [c.casefold() for c in CABECALHO_FPM]:
        raise ValueError(f"Cabeçalho FPM inesperado: {cabecalho}")
    meses, celulas = set(), {}
    for r in leitor:
        if not r or not any(r):
            continue
        ano, mes = r[2].strip(), r[3].strip()
        if not re.fullmatch(r"\d{4}", ano) or not re.fullmatch(r"\d{1,2}", mes) or not 1 <= int(mes) <= 12:
            raise ValueError(f"Competência FPM inválida: {r[2]!r}/{r[3]!r}")
        meses.add((ano, f"{int(mes):02d}"))
        chave = tuple(r[i].strip() for i in (0, 1, 7, 8))
        if chave in celulas:
            raise ValueError(f"Linha FPM repetida: {chave}")
        celulas[chave] = tuple(valor_fpm(x, formatos) for x in r[4:7])
    if len(meses) != 1:
        raise ValueError(f"Arquivo FPM mistura competências: {sorted(meses)}")
    return meses.pop(), celulas


def contem(maior, menor):
    """Verdadeiro se `menor` é versão anterior de `maior`: mesmas chaves ou menos, e valores idênticos onde já havia valor."""
    return set(menor) <= set(maior) and all(m == 0 or m == M for k, v in menor.items() for m, M in zip(v, maior[k]))


def totais_nacionais_fpm(celulas):
    """Soma nacional da linha FPM/FPM em cada decêndio."""
    totais = [0, 0, 0]
    for (_, _, item, transferencia), valores in celulas.items():
        if item == "FPM" and transferencia == "FPM":
            totais = [t + v for t, v in zip(totais, valores)]
    return tuple(totais)


def problemas_fpm(escolhidos):
    """Meses que não podem entrar na soma anual, com o motivo. Nada é corrigido: o mês é recusado.

    - ausente: nenhum arquivo do catálogo traz o mês no conteúdo (ou o arquivo não pôde ser lido);
    - parcial: 3º decêndio nacional zerado — o Tesouro publicou o mês antes do último crédito e não substituiu;
    - escala: total nacional fora de LIMITE_ESCALA_FPM× a mediana dos demais meses (ex.: valores sem ponto decimal).
    """
    problemas = {f"{m:02d}": "mês ausente do catálogo" for m in range(1, 13) if f"{m:02d}" not in escolhidos}
    totais = {mes: totais_nacionais_fpm(celulas) for mes, (_, celulas) in escolhidos.items()}
    for mes, t in totais.items():
        if sum(t) == 0:
            problemas[mes] = "arquivo sem crédito de FPM no mês"
        elif t[2] == 0:
            problemas[mes] = "3º decêndio nacional zerado (publicação parcial, sem versão completa no catálogo)"
    validos = {mes: sum(t) for mes, t in totais.items() if mes not in problemas}
    for mes, total in validos.items():
        outros = [v for m, v in validos.items() if m != mes]
        if len(outros) >= 3:
            razao = total / median(outros)
            if not 1 / LIMITE_ESCALA_FPM <= razao <= LIMITE_ESCALA_FPM:
                problemas[mes] = f"total nacional {razao:.2f}× a mediana dos demais meses (escala suspeita; não corrigida)"
    return dict(sorted(problemas.items()))


def consolidar_fpm(arquivos, ano):
    """Uma versão por mês. Versões repetidas só são aceitas se encadeadas; fica a mais completa.
    Depois da escolha, o ano inteiro precisa passar em problemas_fpm; senão, FpmIncompleto lista todos os meses."""
    por_mes = defaultdict(list)
    for origem, (competencia, celulas) in arquivos:
        if competencia[0] != str(ano):
            continue
        por_mes[competencia[1]].append((origem, celulas))
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
    problemas = problemas_fpm(escolhidos)
    if problemas:
        raise FpmIncompleto(ano, problemas)
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


def montar_documento(ano, cadastro, pib, inss_valor, inss_qtd, fpm, fontes, validacao, pib_referencia=None, pib_estimado=None):
    """`pib_referencia` diz se o PIB do ano é observado, estimado ou ausente. Estimativa vai em campo próprio
    (`pib_estimado_centavos`); `pib_centavos` só recebe valor observado."""
    pib_referencia = pib_referencia or {"natureza": "observado", "ano": ano}
    natureza_pib = pib_referencia["natureza"]
    motivos = {
        "pib": "O IBGE não publica PIB deste município para o ano (município instalado depois ou valor não numérico).",
        "inss": "A planilha do INSS não traz este município no ano.",
        "fpm": "O Tesouro não registra FPM para este ente no ano (Fernando de Noronha é distrito estadual; ou município instalado depois).",
    }
    if natureza_pib != "observado":
        motivos["pib"] = f"O IBGE ainda não publicou o PIB municipal de {ano}."
    registros = {}
    for codigo, m in sorted(cadastro.items()):
        inss = None
        if codigo in inss_valor:
            inss = {"valor_ano_centavos": inss_valor[codigo], "quantidade_dezembro": inss_qtd.get(codigo)}
        r = {"municipio": {"codigo_ibge": codigo, "nome": m["nome"], "uf": m["uf"]},
             "regiao_imediata": m["regiao_imediata"], "regiao": m["regiao"],
             "pib_centavos": pib.get(codigo), "inss": inss,
             "fpm": None if codigo not in fpm else {"valor_ano_centavos": fpm[codigo]}}
        if natureza_pib == "estimado":
            r["pib_estimado_centavos"] = pib_estimado.get(codigo)
        r["ausencias"] = {k: motivos[k] for k, vazio in (("pib", r["pib_centavos"] is None), ("inss", inss is None), ("fpm", r["fpm"] is None)) if vazio}
        if natureza_pib == "estimado":
            r["ausencias"]["pib"] += (" Ver pib_estimado_centavos (estimativa, não observado)." if r["pib_estimado_centavos"] is not None
                                      else f" Sem PIB observado em {pib_referencia['ano_base']}, não há estimativa.")
        registros[codigo] = r
    definicoes = {
        "pib_centavos": "PIB a preços correntes do ano (IBGE, tabela 5938, variável 37), em centavos. Só valor observado.",
        "inss.valor_ano_centavos": "Valor líquido (bruto menos descontos) dos benefícios emitidos pelo INSS no ano, por grupo de espécies, "
                                   "no município do órgão pagador — não necessariamente o de residência do beneficiário.",
        "inss.quantidade_dezembro": "Quantidade de benefícios emitidos em dezembro (créditos, não pessoas), mesmo critério territorial.",
        "fpm.valor_ano_centavos": "FPM creditado ao município no ano (soma dos decêndios), líquido da retenção para o FUNDEB.",
    }
    if natureza_pib == "estimado":
        definicoes["pib_estimado_centavos"] = ("ESTIMATIVA, não dado do IBGE: PIB municipal observado no ano-base × variação do PIB nacional "
                                               "nominal entre o ano-base e o ano (ver pib_referencia). Arredondado a mil reais.")
    return {
        "esquema": 1, "ano": ano, "natureza": "observado" if natureza_pib == "observado" else f"fluxos observados; PIB {natureza_pib}",
        "data_geracao": datetime.now(timezone.utc).isoformat(),
        "municipios_referencia": len(cadastro), "unidade_territorial": "municipio_ibge_7_digitos",
        "pib_referencia": pib_referencia, "definicoes": definicoes,
        "limites": "Fluxos de natureza diferente: benefícios a pessoas (INSS) e transferência constitucional ao governo municipal (FPM). "
                   "Não somar como investimento federal. Valores nominais. O INSS segue o órgão pagador: taxas por habitante e rankings "
                   "municipais não descrevem os moradores; usar a região imediata para comparações.",
        "fontes": fontes, "validacao": validacao, "cobertura": cobertura(registros), "registros": registros,
    }


def cobertura(registros):
    saida = {"pib": sum(r["pib_centavos"] is not None for r in registros.values()),
             "inss": sum(r["inss"] is not None for r in registros.values()),
             "fpm": sum(r["fpm"] is not None for r in registros.values())}
    if any("pib_estimado_centavos" in r for r in registros.values()):
        saida["pib_estimado"] = sum(r.get("pib_estimado_centavos") is not None for r in registros.values())
    return saida


def validar_publicacao(documento, cadastro):
    registros = documento["registros"]
    natureza_pib = documento.get("pib_referencia", {"natureza": "observado"})["natureza"]
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
        if ("pib_estimado_centavos" in r) != (natureza_pib == "estimado"):
            raise ValueError(f"Estimativa de PIB fora do modo estimado em {codigo}")
        if natureza_pib != "observado" and r["pib_centavos"] is not None:
            raise ValueError(f"PIB observado em publicação sem PIB do ano em {codigo}")
        if r["inss"] is not None and r["inss"]["valor_ano_centavos"]["total"] < 0:
            raise ValueError("Valor anual do INSS negativo")
    # Proporção mínima esperada: quase todos os municípios do ano têm as fontes publicadas.
    esperadas = {"observado": ("pib", "inss", "fpm"), "estimado": ("pib_estimado", "inss", "fpm"), "ausente": ("inss", "fpm")}[natureza_pib]
    if min(documento["cobertura"][c] for c in esperadas) < len(cadastro) - 5:
        raise ValueError(f"Cobertura abaixo do esperado: {documento['cobertura']}")


def carregar_cadastro(cache, atualizar):
    b, origem = obter_com_retentativas(IBGE_MUNICIPIOS, cache, atualizar)
    cadastro = territorio(json_da_fonte(b))
    publicado = {r["codigo_ibge"] for r in json.loads((ROOT / "data/public/rankings_2026.json").read_text())["registros"]}
    if set(cadastro) != publicado:
        raise ValueError("Cadastro IBGE diverge dos municípios publicados pelo projeto")
    return cadastro, origem


def carregar_pib(ano, modo, ano_base, cadastro, cache, atualizar):
    """Devolve (pib observado do ano, estimativa ou None, pib_referencia, fontes)."""
    if modo == "observado":
        b, origem = obter_com_retentativas(PIB_URL.format(ano=ano), cache, atualizar)
        pib = extrair_pib(json_da_fonte(b), ano)
        if set(pib) - set(cadastro):
            raise ValueError("PIB com município fora do cadastro")
        if not any(v is not None for v in pib.values()):
            raise ValueError(f"IBGE sem PIB municipal de {ano}; use --pib estimado ou --pib ausente")
        return pib, None, {"natureza": "observado", "ano": ano}, origem
    if modo == "ausente":
        return {}, None, {"natureza": "ausente", "ano": ano}, None
    if ano_base >= ano:
        raise ValueError("O ano-base da estimativa precisa ser anterior ao ano publicado")
    b, origem_base = obter_com_retentativas(PIB_URL.format(ano=ano_base), cache, atualizar)
    pib_base = extrair_pib(json_da_fonte(b), ano_base)
    if set(pib_base) - set(cadastro):
        raise ValueError("PIB com município fora do cadastro")
    periodos = "|".join(f"{a}{t:02d}" for a in (ano_base, ano) for t in range(1, 5))
    b, origem_trim = obter_com_retentativas(PIB_TRIMESTRAL_URL.format(periodos=periodos), cache, atualizar)
    trimestral = json_da_fonte(b)
    nacional = {a: pib_nacional_anual(trimestral, a) for a in (ano_base, ano)}
    estimado, fator = estimar_pib(pib_base, nacional[ano_base], nacional[ano])
    referencia = {
        "natureza": "estimado", "ano": ano, "ano_base": ano_base, "fator": str(fator),
        "pib_nacional_milhoes": {str(a): str(v) for a, v in nacional.items()},
        "metodo": f"PIB municipal observado de {ano_base} (IBGE 5938) × razão entre o PIB nacional nominal de {ano} e o de {ano_base} "
                  f"(soma dos quatro trimestres, IBGE 1846, PIB a preços de mercado). Supõe que todo município cresceu como o país: "
                  f"não capta safra, preço de commodities, royalties ou choques locais. Substituir pelo PIB municipal quando o IBGE publicar.",
    }
    return {}, estimado, referencia, {"pib_municipal_ano_base": origem_base, "contas_trimestrais": origem_trim}


def carregar_inss(ano, cadastro, cache, atualizar):
    import openpyxl

    b, origem = obter_com_retentativas(INSS_URL.format(ano=ano), cache, atualizar)
    wb = openpyxl.load_workbook(io.BytesIO(b), read_only=True, data_only=True)
    try:
        aba_qtd, aba_ano = escolher_abas_inss(wb.sheetnames, ano)
        inss_qtd, val_qtd = extrair_aba_inss(wb[aba_qtd].iter_rows(values_only=True), True, cadastro)
        inss_valor, val_valor = extrair_aba_inss(wb[aba_ano].iter_rows(values_only=True), False, cadastro)
    finally:
        wb.close()
    if set(inss_qtd) != set(inss_valor) or set(inss_valor) - set(cadastro):
        raise ValueError("Abas do INSS cobrem municípios diferentes ou fora do cadastro")
    return inss_valor, inss_qtd, {"quantidade_dezembro": val_qtd, "valor_ano": val_valor}, origem | {"abas": [aba_qtd, aba_ano]}


def urls_fpm(catalogo, ano):
    """O nome do arquivo no catálogo pode estar até dois meses adiantado (2024-01 saiu em ...202402); o mês vem do conteúdo."""
    padrao = rf"transferenciamensalmunicipios({ano}\d\d|{ano + 1}0[12])"
    return sorted({r["url"] for r in catalogo["result"]["resources"] if re.search(padrao, r["url"])})


def carregar_fpm(ano, cadastro, cache, atualizar):
    b, origem_catalogo = obter_com_retentativas(FPM_CATALOGO, cache, atualizar)
    arquivos = []
    for url in urls_fpm(json_da_fonte(b), ano):
        conteudo, origem = obter_com_retentativas(url, cache, atualizar)
        formatos = set()
        try:
            lido = ler_fpm_csv(conteudo, formatos)
        except ValueError as exc:
            raise ValueError(f"Arquivo FPM ilegível ({url}): {exc}") from exc
        if formatos - {"ponto_decimal"}:
            origem = origem | {"formatos_numericos": sorted(formatos)}
        arquivos.append((origem, lido))
    escolhidos, descartados = consolidar_fpm(arquivos, ano)
    fpm = fpm_por_municipio(escolhidos, cadastro)
    fontes = {"catalogo": origem_catalogo, "licenca": "ODbL", "meses": {mes: v[0] for mes, v in sorted(escolhidos.items())},
              "versoes_descartadas": descartados}
    return fpm, escolhidos, fontes


def diagnosticar(anos, cadastro, cache, atualizar):
    """Completude de INSS e FPM por ano, sem publicar. Cada fonte recusada traz o motivo."""
    relatorio = {}
    for ano in anos:
        linha = {}
        try:
            inss_valor, _, val, _ = carregar_inss(ano, cadastro, cache, atualizar)
            linha["inss"] = {"situacao": "completo", "municipios": len(inss_valor)}
        except Exception as exc:  # noqa: BLE001 — relatório, não publicação
            linha["inss"] = {"situacao": "recusado", "motivo": str(exc)}
        try:
            fpm, escolhidos, _ = carregar_fpm(ano, cadastro, cache, atualizar)
            linha["fpm"] = {"situacao": "completo", "municipios": len(fpm), "total_centavos": sum(fpm.values())}
        except FpmIncompleto as exc:
            linha["fpm"] = {"situacao": "incompleto", "meses_recusados": exc.problemas}
        except Exception as exc:  # noqa: BLE001
            linha["fpm"] = {"situacao": "recusado", "motivo": str(exc)}
        relatorio[str(ano)] = linha
        print(json.dumps({ano: linha}, ensure_ascii=False), flush=True)
    return relatorio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ano", type=int, default=2023)
    parser.add_argument("--pib", choices=("observado", "estimado", "ausente"), default="observado",
                        help="observado: PIB municipal do ano (IBGE); estimado: ano-base × crescimento nacional, rotulado; ausente: nulo")
    parser.add_argument("--pib-ano-base", type=int, default=2023, help="ano do PIB municipal observado usado na estimativa")
    parser.add_argument("--diagnosticar", type=int, nargs="+", metavar="ANO", help="relata a completude de INSS e FPM; não publica")
    parser.add_argument("--cache", type=Path, default=ROOT / "data/raw/dinheiro_federal")
    parser.add_argument("--saida", type=Path, help="padrão: data/public/dinheiro_federal.json (2023) ou dinheiro_federal_{ano}.json")
    parser.add_argument("--atualizar", action="store_true")
    args = parser.parse_args()

    cadastro, origem_ibge = carregar_cadastro(args.cache, args.atualizar)
    if args.diagnosticar:
        diagnosticar(args.diagnosticar, cadastro, args.cache, args.atualizar)
        return
    # 2023 mantém o nome do primeiro snapshot; demais anos ganham arquivo próprio para não sobrescrevê-lo.
    saida = args.saida or ROOT / "data/public" / ("dinheiro_federal.json" if args.ano == 2023 else f"dinheiro_federal_{args.ano}.json")

    pib, pib_estimado, pib_referencia, origem_pib = carregar_pib(args.ano, args.pib, args.pib_ano_base, cadastro, args.cache, args.atualizar)
    print(f"PIB {args.ano} ({pib_referencia['natureza']}): "
          f"{sum(v is not None for v in (pib_estimado if pib_estimado is not None else pib).values())} municípios.", flush=True)

    inss_valor, inss_qtd, val_inss, origem_inss = carregar_inss(args.ano, cadastro, args.cache, args.atualizar)
    print(f"INSS {args.ano}: {len(inss_valor)} municípios.", flush=True)

    fpm, escolhidos, fontes_fpm = carregar_fpm(args.ano, cadastro, args.cache, args.atualizar)
    print(f"FPM {args.ano}: {len(fpm)} municípios, {len(escolhidos)} meses.", flush=True)

    fontes = {"cadastro_ibge": origem_ibge, "pib": origem_pib, "inss": origem_inss, "fpm": fontes_fpm}
    validacao = {"inss": val_inss, "fpm": {"municipios": len(fpm), "aliases_revisados": len(ALIASES_FPM)}}
    documento = montar_documento(args.ano, cadastro, pib, inss_valor, inss_qtd, fpm, fontes, validacao, pib_referencia, pib_estimado)
    validar_publicacao(documento, cadastro)
    saida.parent.mkdir(parents=True, exist_ok=True)
    temp = saida.with_suffix(".tmp")
    temp.write_text(json.dumps(documento, ensure_ascii=False, separators=(",", ":")) + "\n")
    temp.replace(saida)
    print(json.dumps({"arquivo": str(saida), "ano": args.ano, "pib": pib_referencia["natureza"], "cobertura": documento["cobertura"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
