export const regioesBrasil = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"] as const;
export const ufRegiao: Record<string, string> = { AC: "Norte", AP: "Norte", AM: "Norte", PA: "Norte", RO: "Norte", RR: "Norte", TO: "Norte", AL: "Nordeste", BA: "Nordeste", CE: "Nordeste", MA: "Nordeste", PB: "Nordeste", PE: "Nordeste", PI: "Nordeste", RN: "Nordeste", SE: "Nordeste", DF: "Centro-Oeste", GO: "Centro-Oeste", MT: "Centro-Oeste", MS: "Centro-Oeste", ES: "Sudeste", MG: "Sudeste", RJ: "Sudeste", SP: "Sudeste", PR: "Sul", RS: "Sul", SC: "Sul" };
export const metricas = {
  alcance: { tema: "bolsa", nome: "Moradores em famílias beneficiárias", titulo: "Onde o Bolsa Família alcança mais moradores?", descricao: "Percentual da população inteira da cidade que vive em famílias que recebem o Bolsa Família. Conta o titular e os demais integrantes, como crianças.", unidade: "percentual", fonte: "MDS / IBGE", url: "https://aplicacoes.cidadania.gov.br/vis/data3/", limite: "A fonte conta pessoas em famílias beneficiárias. Não permite identificar como essas pessoas votaram." },
  valor_total: { tema: "bolsa", nome: "Valor total do Bolsa Família", titulo: "Quanto foi registrado do Bolsa Família em cada cidade?", descricao: "Soma dos valores das parcelas registradas na CGU no período completo. Não equivale a famílias únicas e não comprova saque.", unidade: "moeda", fonte: "CGU / Portal da Transparência", url: "https://portaldatransparencia.gov.br/download-de-dados/novo-bolsa-familia", limite: "Valores nominais acumulados no período. Cidades maiores podem concentrar valores maiores; use por habitante para considerar a população." },
  valor_habitante: { tema: "bolsa", nome: "Valor por habitante", titulo: "Como os valores do Bolsa Família se distribuem por habitante?", descricao: "Valor acumulado registrado dividido pela população IBGE 2026. É uma medida territorial, não o valor que cada morador recebeu.", unidade: "moeda", fonte: "CGU / IBGE", url: "https://portaldatransparencia.gov.br/download-de-dados/novo-bolsa-familia", limite: "Não é o benefício médio de uma família nem uma média mensal. Valores sem ajuste pela inflação." },
  saude_habitante: { tema: "saude", nome: "Saúde: valor por habitante", titulo: "Quanto dinheiro federal foi enviado à saúde por habitante?", descricao: "Dinheiro enviado ao fundo de saúde da cidade, dividido pela população IBGE 2026. Não é um pagamento individual nem comprovação de atendimento.", unidade: "moeda", fonte: "FNS / IBGE", url: "https://portalfns.saude.gov.br/downloads/", limite: "Somente transferências federais fundo a fundo ao destinatário municipal. Recursos estaduais, distritais e de outras instituições sediadas na cidade ficam separados." },
  saude_total: { tema: "saude", nome: "Saúde: valor total", titulo: "Quanto dinheiro federal chegou ao fundo de saúde de cada cidade?", descricao: "Dinheiro enviado pelo governo federal ao fundo de saúde administrado pela cidade. Receber o dinheiro não significa que ele já foi gasto.", unidade: "moeda", fonte: "FNS", url: "https://portalfns.saude.gov.br/downloads/", limite: "Total das áreas publicadas, incluindo atenção primária e emendas identificadas. Não é todo gasto federal no território. Valores nominais." },
  saude_variacao: { tema: "saude", nome: "Mudança de 2024 para 2025", titulo: "Onde mudou o dinheiro federal enviado à saúde?", descricao: "Mudança percentual entre os anos completos de 2024 e 2025. Aumento e redução são mostrados com sinal, sem ajuste pela inflação.", unidade: "variacao", fonte: "FNS", url: "https://portalfns.saude.gov.br/downloads/", limite: "Não compara o parcial de 2026 com um ano completo. Um aumento nominal não comprova mais poder de compra ou melhor atendimento." },
  votos_lider: { tema: "voto", nome: "Percentual do candidato mais votado", titulo: "Como se distribuiu a votação do candidato mais votado?", descricao: "Percentual sobre a soma dos votos dos candidatos listados no primeiro turno presidencial de 2026. Empates são identificados.", unidade: "percentual", fonte: "TSE", url: "https://dadosabertos.tse.jus.br/dataset/resultados-2026", limite: "O resultado municipal não revela a motivação de cada eleitor. Um percentual maior não é uma avaliação da qualidade de uma gestão." },
} as const;
export type MetricaExplorar = keyof typeof metricas;
export type FiltrosExplorar = { metrica: MetricaExplorar; regiao: string; uf: string; vencedor: string; ordem: "asc" | "desc"; pagina: number; limite: number };
export const filtrosIniciais: FiltrosExplorar = { metrica: "alcance", regiao: "", uf: "", vencedor: "todos", ordem: "desc", pagina: 1, limite: 10 };
export const candidatosFiltro = ["13", "14", "16", "21", "22", "27", "29", "30", "35", "55", "70", "80"];

export function lerFiltros(params: URLSearchParams): FiltrosExplorar {
  const metrica = params.get("metrica") ?? "alcance";
  const regiao = params.get("regiao") ?? "";
  const uf = params.get("uf") ?? "";
  const vencedor = params.get("vencedor") ?? "todos";
  const ordem = params.get("ordem") ?? "desc";
  const pagina = Number(params.get("pagina") ?? 1);
  const limite = Number(params.get("limite") ?? 10);
  if (!Object.hasOwn(metricas, metrica) || (regiao && !regioesBrasil.includes(regiao as typeof regioesBrasil[number])) ||
    (uf && !Object.hasOwn(ufRegiao, uf)) || (uf && regiao && ufRegiao[uf] !== regiao) ||
    !["todos", "outros", "empate", "sem_dado", ...candidatosFiltro].includes(vencedor) || !["asc", "desc"].includes(ordem) ||
    !Number.isInteger(pagina) || pagina < 1 || pagina > 1000 || ![10, 25, 50].includes(limite)) throw Error("Confira os filtros do link. Há uma opção inválida ou um estado fora da região escolhida.");
  return { metrica: metrica as MetricaExplorar, regiao, uf, vencedor, ordem: ordem as "asc" | "desc", pagina, limite };
}
export function parametrosExplorar(filters: FiltrosExplorar) {
  return new URLSearchParams(Object.entries(filters).map(([key, value]) => [key, String(value)]));
}
export type RegistroExplorar = { codigo_ibge: string; nome: string; uf: string; populacao: number | null; ano_populacao: number | null; vencedor: string | null; empatados: number | null; percentual_vencedor: number | null; valor: number };
export type ResultadoExplorar = { filtros: FiltrosExplorar; periodo: string; fonte_url: string; recorte: number; com_dado: number; sem_dado: number; paginas: number; pagina: number; resultados: RegistroExplorar[] };

export function filtrarOrdenarExploracao<T extends RegistroExplorar>(rows: T[], filtros: FiltrosExplorar): T[] {
  return rows.filter(row => (!filtros.uf || row.uf === filtros.uf) && (!filtros.regiao || ufRegiao[row.uf] === filtros.regiao) &&
    (filtros.vencedor === "todos" || (filtros.vencedor === "empate" ? (row.empatados ?? 0) > 1 : filtros.vencedor === "sem_dado" ? !row.vencedor && (row.empatados ?? 0) <= 1 :
      filtros.vencedor === "outros" ? row.empatados === 1 && !!row.vencedor && !["13", "22"].includes(row.vencedor) : row.empatados === 1 && row.vencedor === filtros.vencedor)))
    .sort((a, b) => (filtros.ordem === "desc" ? b.valor - a.valor : a.valor - b.valor) || a.codigo_ibge.localeCompare(b.codigo_ibge));
}
