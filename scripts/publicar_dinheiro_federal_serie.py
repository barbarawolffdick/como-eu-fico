"""Publica a série anual de INSS e FPM por município e o IPCA médio de cada ano.

Reutiliza os leitores validados de scripts/publicar_dinheiro_federal.py: um ano só entra para uma
fonte se passar em todos os controles dela; senão fica nulo, com o motivo. Valores nominais; a
correção pela inflação é feita na leitura (scripts/derivar_dinheiro_federal.mjs) com o IPCA daqui.

Uso: python -m scripts.publicar_dinheiro_federal_serie [--anos 2019 2025] [--atualizar]
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import re

from scripts.publicar_dinheiro_federal import (
    FpmIncompleto, carregar_cadastro, carregar_fpm, carregar_inss, json_da_fonte,
)
from scripts.publicar_saude_nacional import obter_com_retentativas
from scripts.publicar_saude_piloto import ROOT

IPCA_URL = ("https://servicodados.ibge.gov.br/api/v3/agregados/1737/periodos/{periodos}/variaveis/2266"
            "?localidades=N1%5Ball%5D")


def ipca_medio_anual(documento, anos):
    """Média dos 12 números-índice mensais do IPCA (base dez/1993 = 100) em cada ano. Ano sem 12 meses interrompe."""
    variavel = documento[0]
    if str(variavel["id"]) != "2266":
        raise ValueError("Variável do IPCA inesperada")
    serie = variavel["resultados"][0]["series"][0]["serie"]
    medias = {}
    for ano in anos:
        valores = [Decimal(v) for k, v in serie.items() if k.startswith(str(ano)) and re.fullmatch(r"\d+(\.\d+)?", v or "")]
        if len(valores) != 12:
            raise ValueError(f"IPCA de {ano} com {len(valores)} meses")
        medias[str(ano)] = float(sum(valores) / 12)
    return medias


def montar_serie(anos, cadastro, inss_por_ano, fpm_por_ano, situacao, ipca, fontes):
    registros = {codigo: {"inss": {str(a): (inss_por_ano[a] or {}).get(codigo, {}).get("total") if inss_por_ano[a] is not None else None for a in anos},
                          "fpm": {str(a): ((fpm_por_ano[a] or {}).get(codigo) or (None,))[0] if fpm_por_ano[a] is not None else None for a in anos}}
                 for codigo in sorted(cadastro)}
    return {"esquema": 1, "natureza": "observado, valores nominais", "data_geracao": datetime.now(timezone.utc).isoformat(),
            "anos": [str(a) for a in anos], "municipios_referencia": len(cadastro), "ipca_medio_anual": ipca,
            "definicoes": {"inss": "Valor líquido anual dos benefícios emitidos pelo INSS (total), por município do órgão pagador.",
                           "fpm": "FPM creditado no ano: cotas mensais líquidas da retenção do FUNDEB mais as cotas extraordinárias de 1%.",
                           "ipca_medio_anual": "Média dos números-índice mensais do IPCA no ano (IBGE, tabela 1737, variável 2266)."},
            "situacao": situacao, "fontes": fontes, "registros": registros}


def validar_serie(documento, cadastro):
    if set(documento["registros"]) != set(cadastro):
        raise ValueError("Série não cobre o cadastro municipal")
    for ano in documento["anos"]:
        for fonte in ("inss", "fpm"):
            completo = documento["situacao"][ano][fonte] == "completo"
            com_valor = sum(r[fonte][ano] is not None for r in documento["registros"].values())
            if completo and com_valor < len(cadastro) - 5:
                raise ValueError(f"{fonte} {ano} marcado completo com {com_valor} municípios")
            if not completo and com_valor:
                raise ValueError(f"{fonte} {ano} recusado mas com valores publicados")
        if ano not in documento["ipca_medio_anual"]:
            raise ValueError(f"IPCA ausente para {ano}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anos", type=int, nargs=2, default=(2019, 2025), metavar=("INICIO", "FIM"))
    parser.add_argument("--cache", type=Path, default=ROOT / "data/raw/dinheiro_federal")
    parser.add_argument("--saida", type=Path, default=ROOT / "data/public/dinheiro_federal_serie.json")
    parser.add_argument("--atualizar", action="store_true")
    args = parser.parse_args()
    anos = list(range(args.anos[0], args.anos[1] + 1))

    cadastro, origem_ibge = carregar_cadastro(args.cache, args.atualizar)
    periodos = "%7C".join(f"{a}{m:02d}" for a in anos for m in range(1, 13))
    b, origem_ipca = obter_com_retentativas(IPCA_URL.format(periodos=periodos), args.cache, args.atualizar)
    ipca = ipca_medio_anual(json_da_fonte(b), anos)

    inss_por_ano, fpm_por_ano, situacao, fontes = {}, {}, {}, {"cadastro_ibge": origem_ibge, "ipca": origem_ipca, "inss": {}, "fpm": {}}
    for ano in anos:
        situacao[str(ano)] = {}
        try:
            valor, _, _, origem = carregar_inss(ano, cadastro, args.cache, args.atualizar)
            inss_por_ano[ano], situacao[str(ano)]["inss"], fontes["inss"][str(ano)] = valor, "completo", origem
        except Exception as exc:  # noqa: BLE001 — ano recusado fica nulo, com motivo
            inss_por_ano[ano], situacao[str(ano)]["inss"] = None, f"recusado: {exc}"
        try:
            fpm, _, origem = carregar_fpm(ano, cadastro, args.cache, args.atualizar)
            fpm_por_ano[ano], situacao[str(ano)]["fpm"], fontes["fpm"][str(ano)] = fpm, "completo", {"meses": origem["meses"]}
        except FpmIncompleto as exc:
            fpm_por_ano[ano], situacao[str(ano)]["fpm"] = None, f"incompleto: {exc.problemas}"
        except Exception as exc:  # noqa: BLE001
            fpm_por_ano[ano], situacao[str(ano)]["fpm"] = None, f"recusado: {exc}"
        print(ano, {k: v.split(":")[0] for k, v in situacao[str(ano)].items()}, flush=True)

    documento = montar_serie(anos, cadastro, inss_por_ano, fpm_por_ano, situacao, ipca, fontes)
    validar_serie(documento, cadastro)
    temp = args.saida.with_suffix(".tmp")
    temp.write_text(json.dumps(documento, ensure_ascii=False, separators=(",", ":")) + "\n")
    temp.replace(args.saida)
    print(json.dumps({"arquivo": str(args.saida), "situacao": {a: {k: v.split(":")[0] for k, v in s.items()} for a, s in situacao.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
