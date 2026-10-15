export type OrigemSaude = { url: string; sha256: string; data_extracao: string };
type ResumoFNS = { valor_liquido_centavos: number | null; linhas: number; componentes: {
  bloco: string; estrategia: string; valor_liquido_centavos: number | null; linhas_origem: number[];
}[] };
export type SaudeMunicipal = {
  municipio: { codigo_ibge: string; nome: string; uf: string };
  fns: { periodo_inicio: string; periodo_fim: string; tipo_periodo: string;
    municipal: ResumoFNS | null; estadual_sediado_na_cidade: ResumoFNS | null };
  aps: { parcela: string; competencia_cnes: string; data_relatorio: string;
    equipes: { tipo: string; homologadas: number | null; financiadas: number | null }[] } | null;
  mais_medicos: { ultimo: { data_referencia: string; vagas_ocupadas: number | null; linha_origem: number } | null;
    indicador: "total_ocupadas"; motivo: string | null };
  proveniencia: { fns: OrigemSaude; aps: OrigemSaude; mais_medicos: OrigemSaude };
};
export type RespostaSaude = { disponivel: boolean; status: "NACIONAL"; municipios_referencia: number;
  motivo?: string; dados: SaudeMunicipal | null; financiamento: FinanciamentoSaude;
  fontes_financiamento: Record<string, OrigemSaude> };

type ValorNomeado = { nome: string; valor_centavos: number | null };
type Repasse = { valor_centavos: number | null; linhas: number; destinatarios: string[]; grupos: ValorNomeado[]; finalidades: ValorNomeado[];
  emendas: { valor_centavos: number | null; percentual_do_total: number | null } };
export type FinanciamentoSaude = {
  municipio: { codigo_ibge: string; nome: string; uf: string; populacao: number | null; ano_populacao: number | null };
  fns: { ano: number; inicio: string; fim: string; completo: boolean; municipal: Repasse | null; estadual_sediado_na_cidade: Repasse | null;
    outros_destinatarios_sediados_na_cidade: Repasse | null }[];
  variacao_anual_2024_2025_percentual: number | null; centavos_por_habitante: number | null;
  siops: { ano: number; bimestre: number; homologacao: string; transmissao: string;
    fases: Record<string, { total_centavos: number | null; percentual_fonte_federal_faf: number | null; fontes: ValorNomeado[] }> } | null;
  cnes: { estabelecimentos_sus_ambulatorial: number; ubs: number; postos: number; lista_limitada: boolean;
    unidades_exibidas: { cnes: string; nome: string; tipo: number; gestao: string; codigo_local_fonte: string }[] } | null;
  leitos: { competencia: string; hospitais_na_fonte: number; leitos_sus: number | null; uti_sus: number | null;
    unidades: { cnes: string; nome: string; gestao: string; leitos_sus: number | null; uti_sus: number | null }[] } | null;
  equipamentos: { competencia: string; equipamentos_em_uso: { tipo: string; valor: number | null }[] | null;
    estabelecimentos_com_equipamento_sus: { tipo: string; valor: number | null }[] | null };
};
