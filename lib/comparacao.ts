export type CidadeDetalhe = {
  municipio: { codigo_ibge: string; nome: string | null; uf: string | null; populacao: number | null; ano_populacao: number | null };
  bolsa_familia: { mes_competencia: string; valor_centavos: number; parcelas: number }[];
  votos_presidenciais: { candidato: string; votos: number }[];
  eleitoral_disponivel: boolean;
};
export type CoberturaCidade = { disponivel: boolean; periodo: string; fonte: string;
  municipio: { pessoas: number | null; populacao: number; cobertura_pct: number | null } };

export function ultimoMesComum(a: CidadeDetalhe, b: CidadeDetalhe) {
  const mesesB = new Set(b.bolsa_familia.map(item => item.mes_competencia));
  return a.bolsa_familia.map(item => item.mes_competencia).filter(mes => mesesB.has(mes)).sort().at(-1) ?? null;
}

export function porHabitante(centavos: number | null | undefined, cidade: CidadeDetalhe) {
  const { populacao, ano_populacao } = cidade.municipio;
  return centavos != null && populacao != null && populacao > 0 && ano_populacao != null ? centavos / populacao : null;
}

export function placar(cidade: CidadeDetalhe) {
  const votos = cidade.eleitoral_disponivel ? cidade.votos_presidenciais : [];
  const total = votos.reduce((sum, item) => sum + item.votos, 0);
  if (total <= 0) return null;
  const ordenados = [...votos].sort((a, b) => b.votos - a.votos || a.candidato.localeCompare(b.candidato));
  const lider = ordenados[0];
  return { total, lider, empate: ordenados.filter(item => item.votos === lider.votos).length > 1,
    percentuais: Object.fromEntries(votos.map(item => [item.candidato, 100 * item.votos / total])) as Record<string, number> };
}
