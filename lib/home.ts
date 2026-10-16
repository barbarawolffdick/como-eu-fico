import { lerSnapshot, type SnapshotPublico } from "./snapshots";

type Municipio = { codigo_ibge: string; nome: string; uf: string };
type Pessoas = { periodo: string; unidade: string; registros: Record<string, { pessoas: number | null; cobertura_pct: number | null }> };
type Familias = { unidade: string; periodos: string[]; registros: Record<string, Record<string, number | null>> };
const regioes: Record<string, string> = { AC: "Norte", AP: "Norte", AM: "Norte", PA: "Norte", RO: "Norte", RR: "Norte", TO: "Norte", AL: "Nordeste", BA: "Nordeste", CE: "Nordeste", MA: "Nordeste", PB: "Nordeste", PE: "Nordeste", PI: "Nordeste", RN: "Nordeste", SE: "Nordeste", DF: "Centro-Oeste", GO: "Centro-Oeste", MT: "Centro-Oeste", MS: "Centro-Oeste", ES: "Sudeste", MG: "Sudeste", RJ: "Sudeste", SP: "Sudeste", PR: "Sul", RS: "Sul", SC: "Sul" };

const snapshot = <T>(file: SnapshotPublico) => lerSnapshot<T>(file);

export async function descobertasHome() {
  const [territorio, pessoas, familias] = await Promise.allSettled([
    snapshot<{ registros: Municipio[] }>("rankings_2026.json"),
    snapshot<Pessoas>("pessoas_mds.json"),
    snapshot<Familias>("familias_mds.json"),
  ]);
  if (territorio.status !== "fulfilled") return { ranking: null, mudanca: null };
  const cidades = territorio.value.registros;
  const ranking = pessoas.status === "fulfilled" && pessoas.value.unidade === "pessoas_em_familias_beneficiarias" ? {
    periodo: pessoas.value.periodo,
    cidades: cidades.flatMap(city => {
      const item = pessoas.value.registros[city.codigo_ibge];
      return item && item.pessoas != null && item.cobertura_pct != null ? [{ ...city, pessoas: item.pessoas, percentual: item.cobertura_pct }] : [];
    }).sort((a, b) => b.percentual - a.percentual || a.codigo_ibge.localeCompare(b.codigo_ibge)).slice(0, 5),
  } : null;
  let mudanca = null;
  if (familias.status === "fulfilled" && familias.value.unidade === "familias_beneficiarias" && familias.value.periodos.length === 2) {
    const dados = familias.value;
    const [inicio, fim] = dados.periodos;
    const grupos = new Map<string, { regiao: string; antes: number; depois: number; municipios: number; total: number }>();
    for (const city of cidades) {
      const regiao = regioes[city.uf];
      if (!regiao) continue;
      const grupo = grupos.get(regiao) ?? { regiao, antes: 0, depois: 0, municipios: 0, total: 0 };
      grupo.total++;
      const antes = dados.registros[inicio]?.[city.codigo_ibge];
      const depois = dados.registros[fim]?.[city.codigo_ibge];
      if (antes != null && depois != null && Number.isInteger(antes) && Number.isInteger(depois)) {
        grupo.antes += antes; grupo.depois += depois; grupo.municipios++;
      }
      grupos.set(regiao, grupo);
    }
    mudanca = { inicio, fim, regioes: [...grupos.values()].map(g => ({ ...g, percentual: g.antes > 0 ? 100 * (g.depois - g.antes) / g.antes : null })) };
  }
  return { ranking, mudanca };
}
