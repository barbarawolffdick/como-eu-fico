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
  motivo?: string; dados: SaudeMunicipal | null };
