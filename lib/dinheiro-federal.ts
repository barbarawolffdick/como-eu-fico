// Dinheiro federal que chega à cidade: tipos dos derivados de scripts/derivar_dinheiro_federal.mjs.
export const FLUXOS = ["inss", "bolsa_familia", "fpm", "sus"] as const;
export type Fluxo = (typeof FLUXOS)[number];
export const NOMES_FLUXO: Record<Fluxo, string> = {
  inss: "Aposentadorias e benefícios do INSS",
  bolsa_familia: "Bolsa Família",
  fpm: "FPM, repasse à prefeitura",
  sus: "SUS, repasse à saúde da cidade",
};
export const PARA_PESSOAS: Fluxo[] = ["inss", "bolsa_familia"];
export const PARA_PREFEITURA: Fluxo[] = ["fpm", "sus"];

export type Comparacao = { nome: string; detalhe: string; municipios: number; percentual_do_pib: Record<Fluxo, number | null>; total: number | null };
export type InssGrupos = { aposentadorias: number; aposentadorias_idade: number; aposentadorias_invalidez: number;
  aposentadorias_tempo_contribuicao: number; pensoes_por_morte: number; auxilios: number; outros_previdenciarios: number;
  previdenciario: number; assistencial_e_legislacao_especifica: number; total: number };
export type PibReferencia = { ano_fonte: number; estimado: boolean; fator?: number; metodo?: string };

export type DinheiroFederalCidade = {
  municipio: { codigo_ibge: string; nome: string; uf: string };
  regiao_imediata: { id: string; nome: string };
  regiao: string;
  populacao: number | null;
  pib_centavos: number | null;
  fluxos: Record<Fluxo, number | null>;
  ausencias: Partial<Record<Fluxo | "pib", string>>;
  inss_detalhe: InssGrupos | null;
  inss_quantidade_dezembro: InssGrupos | null;
  inss_beneficios_por_100_habitantes: number | null;
  inss_orgao_pagador_atipico: boolean;
  comparacoes: Comparacao[];
  serie: SerieCidade | null;
};
export type PontoSerie = { nominal: number | null; real: number | null; motivo: string | null };
export type SerieCidade = { anos: string[]; base_inflacao: string; inss: Record<string, PontoSerie>; fpm: Record<string, PontoSerie> };
export type AutorEmenda = { autor: string; tipo: string; ano_emenda: number | null; valor_centavos: number; saude_centavos: number;
  partido: string | null; partido_atual: string | null; casa: string | null; favorecidos: [string, number][] };
export type EmendasCidade = { total_centavos: number; saude_centavos: number; autores: AutorEmenda[] };
export type RespostaDinheiroFederal = { ano: number; pib: PibReferencia; cidade: DinheiroFederalCidade;
  /** Nulo se as emendas não estão publicadas; com o snapshot publicado, cidade sem emenda paga traz totais 0 e lista vazia. */
  emendas: (EmendasCidade & { ano: number }) | null };

export type PontoRegiao = { id: string; nome: string; uf: string; regiao: string; federal_percentual_do_pib: number; lula_percentual: number };
/** [código, nome, UF, Nordeste (0/1), % da economia, deslocamento na faixa larga, na faixa estreita]. */
export type PontoEnxame = [string, string, string, 0 | 1, number, number, number];
export type Enxame = { max: number; larguras: { largo: number; estreito: number }; raios: { largo: number; estreito: number }; pontos: PontoEnxame[] };
export type RespostaRegioes = { ano: number; pib: PibReferencia; regioes: PontoRegiao[];
  correlacao: { brasil: number | null; nordeste: number | null; demais: number | null }; enxame: Enxame };

/** Soma dos fluxos disponíveis; nula se algum faltar, para não exibir um total parcial como completo. */
export function totalFederal(fluxos: Record<Fluxo, number | null>): number | null {
  return FLUXOS.every(f => fluxos[f] != null) ? FLUXOS.reduce((s, f) => s + (fluxos[f] ?? 0), 0) : null;
}
