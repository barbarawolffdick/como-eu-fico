"""Publica, por município, as emendas parlamentares recebidas no ano, com autor, tipo e partido.

Fonte: CGU, emendas parlamentares por favorecido (pagamentos mês a mês). O município é o do
favorecido (prefeitura, fundo municipal, entidade), ligado ao código IBGE por nome e UF exatos; nunca
por semelhança. O partido é o da época da emenda, segundo a Câmara dos Deputados e o Senado.

Uso: python -m scripts.publicar_emendas [--ano 2025] [--atualizar]
"""
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import zipfile

import re

from scripts.publicar_dinheiro_federal import ALIASES_FPM, carregar_cadastro, chave_nome, json_da_fonte
from scripts.publicar_saude_nacional import obter_com_retentativas
from scripts.publicar_saude_piloto import ROOT, centavos

EMENDAS_ZIP = "https://dadosabertos-download.cgu.gov.br/PortalDaTransparencia/saida/emendas-parlamentares/EmendasParlamentares.zip"
CAMARA_DEPUTADOS = "https://dadosabertos.camara.leg.br/api/v2/deputados?idLegislatura={legislatura}&itens=1000&ordem=ASC&ordenarPor=nome"
CAMARA_HISTORICO = "https://dadosabertos.camara.leg.br/api/v2/deputados/{id}/historico"
SENADO_LEGISLATURA = "https://legis.senado.leg.br/dadosabertos/senador/lista/legislatura/{legislatura}.json"
SENADO_FILIACOES = "https://legis.senado.leg.br/dadosabertos/senador/{codigo}/filiacoes.json"
ARQUIVO = "EmendasParlamentares_PorFavorecido.csv"
COLUNAS = ["Código da Emenda", "Código do Autor da Emenda", "Nome do Autor da Emenda", "Número da emenda", "Tipo de Emenda",
           "Ano/Mês", "Código do Favorecido", "Favorecido", "Natureza Jurídica", "Tipo Favorecido", "UF Favorecido",
           "Município Favorecido", "Valor Recebido"]
NOMES_PARTIDO = {"UNIÃO": "União", "NOVO": "Novo", "REDE": "Rede", "PODE": "Podemos", "SOLIDARIEDADE": "Solidariedade",
                 "REPUBLICANOS": "Republicanos", "CIDADANIA": "Cidadania", "AVANTE": "Avante", "AGIR": "Agir", "PATRIOTA": "Patriota"}
MAX_FAVORECIDOS = 5
# Nomes antigos ou grafias da CGU revisados à mão, além dos do FPM.
ALIASES = {chave_nome(n, uf): c for (n, uf), c in ALIASES_FPM.items()} | {
    chave_nome(n, uf): c for (n, uf), c in {("Embu", "SP"): "3515004", ("Dona Eusébia", "MG"): "3122900",
                                            ("Seridó", "PB"): "2515401",  # renomeado São Vicente do Seridó
                                            ("Augusto Severo", "RN"): "2401305",  # renomeado Campo Grande
                                            ("Fortaleza do Tabocão", "TO"): "1708254"}.items()}


def legislaturas(ano):
    """Emendas pagas no ano podem vir de anos anteriores (restos a pagar): consulta a legislatura do ano e as duas anteriores."""
    atual = 57 + (ano - 2023) // 4
    return [atual - 2, atual - 1, atual]


def ano_da_emenda(codigo):
    return int(codigo[:4]) if re.fullmatch(r"\d{4}", codigo[:4] or "") else None


def limpar_autor(nome):
    """Suplentes que herdaram emendas vêm como "NOME (EX-PARLAMENTAR FULANO, NOS TERMOS ...)"."""
    return re.sub(r"\s*\(EX-PARLAMENTAR.*$", "", nome.strip())


def limpar_favorecido(nome):
    """A CGU às vezes prefixa o nome com vírgula ou código numérico."""
    return re.sub(r"^[^A-Za-zÀ-ÿ]+", "", nome).strip()


def valor(texto):
    """CGU usa vírgula decimal e ponto de milhar."""
    return centavos(texto.replace(".", "").replace(",", ".")) if texto else 0


def eh_fundo_saude(favorecido):
    nome = chave_nome(favorecido, "")[0]
    return "fundo" in nome and "saude" in nome


def ler_favorecidos(conteudo_csv, ano):
    leitor = csv.DictReader(io.TextIOWrapper(conteudo_csv, encoding="latin-1"), delimiter=";")
    if leitor.fieldnames != COLUNAS:
        raise ValueError(f"Colunas inesperadas no arquivo de emendas: {leitor.fieldnames}")
    for linha in leitor:
        if linha["Ano/Mês"].startswith(str(ano)):
            yield linha


def agregar(linhas, cadastro):
    indice = {chave_nome(m["nome"], m["uf"]): c for c, m in cadastro.items()}
    por_cidade = defaultdict(lambda: defaultdict(lambda: {"tipo": None, "codigo_autor": None, "valor_centavos": 0, "saude_centavos": 0,
                                                            "favorecidos": defaultdict(int), "anos": defaultdict(int)}))
    sem_municipio, sem_correspondencia, linhas_validas = 0, defaultdict(int), 0
    for linha in linhas:
        uf, municipio = linha["UF Favorecido"].strip(), linha["Município Favorecido"].strip()
        if not municipio or not uf:
            sem_municipio += 1
            continue
        codigo = ALIASES.get(chave_nome(municipio, uf)) or indice.get(chave_nome(municipio, uf))
        if codigo is None:
            sem_correspondencia[f"{municipio}-{uf}"] += valor(linha["Valor Recebido"])
            continue
        linhas_validas += 1
        a = por_cidade[codigo][limpar_autor(linha["Nome do Autor da Emenda"])]
        v = valor(linha["Valor Recebido"])
        a["tipo"] = linha["Tipo de Emenda"].split(" - ")[0].strip()
        a["codigo_autor"] = linha["Código do Autor da Emenda"].strip()
        a["valor_centavos"] += v
        if eh_fundo_saude(linha["Favorecido"]):
            a["saude_centavos"] += v
        a["favorecidos"][limpar_favorecido(linha["Favorecido"])] += v
        a["anos"][ano_da_emenda(linha["Código da Emenda"])] += v
    return por_cidade, {"linhas_ligadas_a_municipio": linhas_validas, "linhas_sem_municipio": sem_municipio,
                        "municipios_sem_correspondencia": dict(sorted(sem_correspondencia.items(), key=lambda x: -x[1])[:50]),
                        "valor_sem_correspondencia_centavos": sum(sem_correspondencia.values())}


def partido_na_data(filiacoes, ano):
    """Último partido com início até o fim do ano. `filiacoes` = [(data ISO, sigla)]."""
    validos = sorted((d, p) for d, p in filiacoes if p and d[:4] <= str(ano))
    return validos[-1][1] if validos else None


def partidos_dos_autores(nomes, ano, cache, atualizar):
    """Nome do autor → linha do tempo de filiações [(data, sigla)], juntando Câmara e Senado.

    Só correspondência exata de nome; mais de uma pessoa com o mesmo nome na mesma casa fica ambígua.
    """
    obter = lambda url: json_da_fonte(obter_com_retentativas(url, cache, atualizar)[0])
    deputados, senadores = defaultdict(set), defaultdict(set)
    for leg in legislaturas(ano):
        for d in obter(CAMARA_DEPUTADOS.format(legislatura=leg))["dados"]:
            deputados[chave_nome(d["nome"], "")[0]].add(d["id"])
        for p in obter(SENADO_LEGISLATURA.format(legislatura=leg))["ListaParlamentarLegislatura"]["Parlamentares"]["Parlamentar"]:
            i = p["IdentificacaoParlamentar"]
            senadores[chave_nome(i["NomeParlamentar"], "")[0]].add(i["CodigoParlamentar"])
    saida, ambiguos = {}, []
    for nome in sorted(nomes):
        chave = chave_nome(nome, "")[0]
        deps, sens = deputados.get(chave, set()), senadores.get(chave, set())
        if len(deps) > 1 or len(sens) > 1:
            ambiguos.append(nome)
            continue
        if not deps and not sens:
            continue
        filiacoes, casas = [], []
        for id_ in deps:
            filiacoes += [(h["dataHora"], h["siglaPartido"]) for h in obter(CAMARA_HISTORICO.format(id=id_))["dados"]]
            casas.append("Câmara")
        for codigo in sens:
            lista = obter(SENADO_FILIACOES.format(codigo=codigo))["FiliacaoParlamentar"]["Parlamentar"].get("Filiacoes", {}).get("Filiacao", [])
            filiacoes += [(f["DataFiliacao"], f["Partido"]["SiglaPartido"]) for f in (lista if isinstance(lista, list) else [lista])]
            casas.append("Senado")
        saida[nome] = {"filiacoes": filiacoes, "casa": casas[-1]}
    return saida, ambiguos


def nome_partido(sigla):
    return NOMES_PARTIDO.get(sigla, sigla) if sigla else None


def montar_documento(ano, cadastro, por_cidade, partidos, validacao, fontes):
    registros = {}
    for codigo, autores in sorted(por_cidade.items()):
        lista = []
        for autor, a in sorted(autores.items(), key=lambda x: (-x[1]["valor_centavos"], x[0])):
            p = None if a["tipo"] != "Emenda Individual" else partidos.get(autor)
            ano_principal = max((x for x in a["anos"] if x), key=lambda x: a["anos"][x], default=None)
            epoca = p and ano_principal and nome_partido(partido_na_data(p["filiacoes"], ano_principal))
            atual = p and nome_partido(partido_na_data(p["filiacoes"], 9999))
            lista.append({"autor": autor, "tipo": a["tipo"], "ano_emenda": ano_principal, "valor_centavos": a["valor_centavos"], "saude_centavos": a["saude_centavos"],
                          "partido": epoca or None, "partido_atual": atual if epoca and atual != epoca else None,
                          "casa": p["casa"] if p else None,
                          "favorecidos": [[f, v] for f, v in sorted(a["favorecidos"].items(), key=lambda x: -x[1])[:MAX_FAVORECIDOS]]})
        registros[codigo] = {"total_centavos": sum(x["valor_centavos"] for x in lista), "saude_centavos": sum(x["saude_centavos"] for x in lista), "autores": lista}
    return {"esquema": 1, "ano": ano, "natureza": "observado, pagamentos por favorecido", "data_geracao": datetime.now(timezone.utc).isoformat(),
            "municipios_referencia": len(cadastro), "municipios_com_emendas": len(registros),
            "definicoes": {"total_centavos": "Valor recebido no ano por favorecidos sediados no município (prefeitura, fundos, entidades), segundo a CGU.",
                           "saude_centavos": "Parte recebida por fundos municipais de saúde.",
                           "ano_emenda": "Ano de origem da emenda que mais pagou ao município (pagamentos podem ser restos a pagar de anos anteriores).",
                           "partido": "Partido do autor no ano de origem da emenda (Câmara dos Deputados, Senado). Nulo para emendas de bancada, comissão ou relator, ou sem correspondência única."},
            "limites": "Município do favorecido, não necessariamente onde o recurso foi aplicado. Ausência de linha significa nenhuma emenda paga a favorecidos do município no ano.",
            "fontes": fontes, "validacao": validacao, "registros": registros}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ano", type=int, default=2025)
    parser.add_argument("--cache", type=Path, default=ROOT / "data/raw/emendas")
    parser.add_argument("--saida", type=Path)
    parser.add_argument("--atualizar", action="store_true")
    args = parser.parse_args()
    saida = args.saida or ROOT / "data/public" / f"emendas_{args.ano}.json"
    cadastro, origem_ibge = carregar_cadastro(ROOT / "data/raw/dinheiro_federal", False)
    b, origem = obter_com_retentativas(EMENDAS_ZIP, args.cache, args.atualizar)
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        if ARQUIVO not in z.namelist():
            raise ValueError(f"Arquivo {ARQUIVO} ausente no ZIP de emendas")
        with z.open(ARQUIVO) as f:
            por_cidade, validacao = agregar(ler_favorecidos(f, args.ano), cadastro)
    nomes = {a for autores in por_cidade.values() for a, x in autores.items() if x["tipo"] == "Emenda Individual"}
    partidos, ambiguos = partidos_dos_autores(nomes, args.ano, args.cache, args.atualizar)
    validacao |= {"aliases_revisados": len(ALIASES), "autores_individuais": len(nomes), "autores_com_partido": len(partidos), "autores_ambiguos": ambiguos,
                  "autores_sem_correspondencia": sorted(nomes - set(partidos) - set(ambiguos))}
    documento = montar_documento(args.ano, cadastro, por_cidade, partidos, validacao, {"emendas": origem, "cadastro_ibge": origem_ibge})
    temp = saida.with_suffix(".tmp")
    temp.write_text(json.dumps(documento, ensure_ascii=False, separators=(",", ":")) + "\n")
    temp.replace(saida)
    print(json.dumps({"arquivo": str(saida), "municipios_com_emendas": documento["municipios_com_emendas"],
                      **{k: validacao[k] for k in ("linhas_ligadas_a_municipio", "linhas_sem_municipio", "valor_sem_correspondencia_centavos", "autores_individuais", "autores_com_partido")},
                      "ambiguos": len(ambiguos), "sem_correspondencia": len(validacao["autores_sem_correspondencia"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
