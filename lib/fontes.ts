import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

const arquivos = ["rankings_2026.json", "detalhes_2026.json", "familias_mds.json", "pessoas_mds.json", "saude_piloto.json"] as const;

export async function fontesPublicadas() {
  const snapshots = await Promise.all(arquivos.map(async arquivo => {
    const bytes = await readFile(join(process.cwd(), "data/public", arquivo));
    return { arquivo, sha256: createHash("sha256").update(bytes).digest("hex"), dados: JSON.parse(bytes.toString("utf8")) };
  }));
  const [rankings, detalhes, familias, pessoas, saude] = snapshots;
  const commit = /^[a-f0-9]{40}$/.test(process.env.VERCEL_GIT_COMMIT_SHA || "") ? process.env.VERCEL_GIT_COMMIT_SHA! : null;
  return {
    commit,
    arquivos: snapshots.map(({ arquivo, sha256 }) => ({ arquivo, sha256,
      url: `https://github.com/barbarawolffdick/como-eu-fico/blob/${commit || "main"}/data/public/${arquivo}` })),
    municipios: rankings.dados.municipios as number,
    populacao_completa: rankings.dados.populacao_completa as boolean,
    periodo_ranking: { inicio: rankings.dados.inicio as string, fim: rankings.dados.fim as string },
    periodo_serie_cgu: [...new Set<string>(Object.values(detalhes.dados.registros as Record<string, { bolsa_familia: { mes_competencia: string }[] }>).flatMap(x => x.bolsa_familia.map(m => m.mes_competencia)))].sort(),
    familias: { periodos: familias.dados.periodos as string[], coleta_utc: familias.dados.coleta_utc as string, proveniencia: familias.dados.proveniencia },
    pessoas: { periodo: pessoas.dados.periodo as string, data_extracao: pessoas.dados.data_extracao as string,
      municipios_com_dado: pessoas.dados.municipios_com_dado as number,
      municipios_sem_dado: (pessoas.dados.municipios_sem_dado as string[]).map(codigo => ({ codigo_ibge: codigo,
        nome: detalhes.dados.registros[codigo].municipio.nome as string, uf: detalhes.dados.registros[codigo].municipio.uf as string })),
      proveniencia: pessoas.dados.proveniencia },
    saude: { status: saude.dados.status as string, municipios_piloto: saude.dados.municipios_piloto as string[],
      data_geracao: saude.dados.data_geracao as string, natureza: saude.dados.natureza as string,
      proveniencia: Object.fromEntries(Object.entries(saude.dados.registros as Record<string, { proveniencia: unknown }>).map(([codigo, r]) => [codigo, r.proveniencia])) },
    fontes: [
      { nome: "TSE — resultados presidenciais de 2026, primeiro turno", url: "https://dadosabertos.tse.jus.br/dataset/resultados-2026" },
      { nome: "CGU — parcelas e valores do Novo Bolsa Família", url: "https://portaldatransparencia.gov.br/download-de-dados/novo-bolsa-familia" },
      { nome: "IBGE — população municipal de 2026 (SIDRA 6579/9324)", url: "https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/2026?formato=json" },
      { nome: "MDS — VIS DATA 3, famílias e pessoas", url: "https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php" },
      { nome: "FNS — repasses federais para o SUS", url: "https://portalfns.saude.gov.br/downloads/" },
      { nome: "Ministério da Saúde — financiamento de equipes APS", url: "https://relatorioaps.saude.gov.br/" },
      { nome: "Ministério da Saúde — Mais Médicos", url: "https://dadosabertos.saude.gov.br/dataset/provimento-federal-programa-mais-medicos" },
    ],
    limites: "Dados agregados por município. Não identificam o voto de beneficiários nem demonstram causalidade. Ausências são indisponíveis, nunca zero. Parcelas CGU, famílias MDS e pessoas em famílias beneficiárias são unidades distintas.",
  };
}
