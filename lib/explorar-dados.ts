import { filtrarOrdenarExploracao, type FiltrosExplorar, type RegistroExplorar, type ResultadoExplorar } from "./explorar";
import type { FinanciamentoSaude } from "./saude";
import { lerExplorarSaude, lerManifesto, lerSnapshot } from "./snapshots";

type Cidade = Omit<RegistroExplorar, "valor" | "percentual_vencedor"> & { valor_centavos: number | null; competencias: number | null; votos_vencedor: number | null; votos_total: number | null };
type Territorio = { esquema: number; inicio: string; fim: string; municipios: number; registros: Cidade[] };
type Pessoas = { esquema: number; unidade: string; periodo: string; pagina_fonte: string; registros: Record<string, { cobertura_pct: number | null }> };
type SaudeExplorar = { municipio: Pick<FinanciamentoSaude["municipio"], "ano_populacao">;
  fns: (Pick<FinanciamentoSaude["fns"][number], "ano" | "inicio" | "fim" | "completo"> & { municipal: { valor_centavos: number | null } | null })[] } &
  Pick<FinanciamentoSaude, "variacao_anual_2024_2025_percentual" | "centavos_por_habitante">;
type Saude = { esquema: number; municipios: number; registros: Record<string, SaudeExplorar> };
async function lerSaude(): Promise<Saude> {
  const [{ snapshots }, { registros }] = await Promise.all([lerManifesto(), lerExplorarSaude<SaudeExplorar>()]);
  const { esquema, municipios } = snapshots["financiamento_saude.json"].metadados as { esquema: number; municipios: number };
  return { esquema, municipios, registros };
}
const mes = (value: string) => `${value.slice(4)}/${value.slice(0, 4)}`;

export async function consultarExploracao(filtros: FiltrosExplorar): Promise<ResultadoExplorar> {
  const healthMetric = filtros.metrica.startsWith("saude_");
  const [territorio, pessoas, saude] = await Promise.all([
    lerSnapshot<Territorio>("rankings_2026.json"),
    filtros.metrica === "alcance" ? lerSnapshot<Pessoas>("pessoas_mds.json") : null,
    healthMetric ? lerSaude() : null,
  ]);
  if (territorio.esquema !== 1 || territorio.registros.length !== territorio.municipios || territorio.municipios !== 5571 ||
    (pessoas && (pessoas.esquema !== 1 || pessoas.unidade !== "pessoas_em_familias_beneficiarias")) ||
    (saude && (saude.esquema !== 1 || saude.municipios !== territorio.municipios))) throw Error("Fonte incompatível");
  let periodo = "1º turno presidencial de 2026";
  if (pessoas) periodo = mes(pessoas.periodo) + " · população IBGE 2026";
  else if (healthMetric) periodo = filtros.metrica === "saude_variacao" ? "2024 → 2025 · anos completos · sem ajuste pela inflação" : "01/2026 a 07/2026 · acumulado parcial";
  else if (filtros.metrica !== "votos_lider") periodo = `${mes(territorio.inicio)} a ${mes(territorio.fim)} · acumulado`;

  const base = territorio.registros.map(city => ({ ...city, percentual_vencedor: city.votos_total && city.votos_vencedor != null ? 100 * city.votos_vencedor / city.votos_total : null, valor: 0 }));
  const recorte = filtrarOrdenarExploracao(base, filtros);
  const mesesEsperados = (Number(territorio.fim.slice(0, 4)) - Number(territorio.inicio.slice(0, 4))) * 12 + Number(territorio.fim.slice(4)) - Number(territorio.inicio.slice(4)) + 1;
  const rows = recorte.flatMap(city => {
    let value: number | null = null;
    const financial = saude?.registros[city.codigo_ibge];
    const current = financial?.fns.find(row => row.ano === 2026 && row.inicio === "202601" && row.fim === "202607" && !row.completo);
    switch (filtros.metrica) {
      case "alcance": value = pessoas?.registros[city.codigo_ibge]?.cobertura_pct ?? null; break;
      case "valor_total": value = city.competencias === mesesEsperados ? city.valor_centavos : null; break;
      case "valor_habitante": value = city.competencias === mesesEsperados && city.valor_centavos != null && city.populacao != null && city.populacao > 0 && city.ano_populacao === 2026 ? city.valor_centavos / city.populacao : null; break;
      case "saude_total": value = current?.municipal?.valor_centavos ?? null; break;
      case "saude_habitante": value = current?.municipal && financial?.municipio.ano_populacao === 2026 ? financial.centavos_por_habitante : null; break;
      case "saude_variacao": {
        const years = financial?.fns.filter(row => row.completo && [2024, 2025].includes(row.ano) && row.municipal?.valor_centavos != null);
        value = years?.length === 2 ? financial?.variacao_anual_2024_2025_percentual ?? null : null;
        break;
      }
      case "votos_lider": value = city.percentual_vencedor; break;
    }
    return value != null && Number.isFinite(value) ? [{ ...city, valor: value }] : [];
  });
  const ordered = filtrarOrdenarExploracao(rows, filtros);
  const paginas = Math.max(1, Math.ceil(ordered.length / filtros.limite));
  const pagina = Math.min(filtros.pagina, paginas);
  return { filtros, periodo, fonte_url: pessoas?.pagina_fonte ?? "", recorte: recorte.length, com_dado: ordered.length, sem_dado: recorte.length - ordered.length, paginas, pagina,
    resultados: ordered.slice((pagina - 1) * filtros.limite, pagina * filtros.limite) };
}
