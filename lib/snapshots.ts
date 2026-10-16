import { readFile } from "node:fs/promises";
import { join } from "node:path";

// Os snapshots de data/public e os derivados de data/derivados são imutáveis durante
// um deploy. Cada arquivo é lido e interpretado uma única vez por processo; as rotas
// recebem o mesmo objeto e não devem alterá-lo. Uma falha de leitura não fica em cache.
const cache: Map<string, Promise<unknown>> =
  ((globalThis as { __comoEuFicoSnapshots?: Map<string, Promise<unknown>> }).__comoEuFicoSnapshots ??= new Map());

function ler<T>(caminho: string): Promise<T> {
  let promessa = cache.get(caminho);
  if (!promessa) {
    promessa = readFile(join(process.cwd(), caminho), "utf8").then(JSON.parse);
    promessa.catch(() => cache.delete(caminho));
    cache.set(caminho, promessa);
  }
  return promessa as Promise<T>;
}

export type SnapshotPublico = "rankings_2026.json" | "detalhes_2026.json" | "familias_mds.json" | "pessoas_mds.json" |
  "saude_municipal.json" | "financiamento_saude.json" | "pessoas_mds_mensal.json";
export type SnapshotFragmentado = "detalhes_2026" | "saude_municipal" | "financiamento_saude";

/** Snapshot canônico completo. Preferir `registroMunicipal` para consultas de uma cidade. */
export const lerSnapshot = <T>(arquivo: SnapshotPublico) => ler<T>("data/public/" + arquivo);

export type Manifesto = { esquema: number; gerado_em: string; snapshots: Record<SnapshotPublico, {
  sha256: string; bytes: number; metadados: Record<string, unknown>; fragmentos?: string[] }> };
/** SHA-256 e campos de cabeçalho (tudo exceto `registros`) de cada snapshot, calculados no build. */
export const lerManifesto = () => ler<Manifesto>("data/derivados/manifesto.json");

/** Registro de uma cidade, lido somente do fragmento da sua UF. `undefined` se não existir. */
export async function registroMunicipal<T>(snapshot: SnapshotFragmentado, codigo_ibge: string): Promise<T | undefined> {
  if (!/^\d{7}$/.test(codigo_ibge)) return undefined;
  const { snapshots } = await lerManifesto();
  const uf = codigo_ibge.slice(0, 2);
  if (!snapshots[`${snapshot}.json`].fragmentos?.includes(uf)) return undefined;
  const { registros } = await ler<{ registros: Record<string, T> }>(`data/derivados/${snapshot}/${uf}.json`);
  return registros[codigo_ibge];
}

/** Projeção de financiamento_saude.json com os campos usados na exploração nacional. */
export const lerExplorarSaude = <T>() => ler<{ registros: Record<string, T> }>("data/derivados/explorar_saude.json");

export type MunicipioBusca = { codigo_ibge: string; nome: string; uf: string; populacao: number | null; ano_populacao: number | null; chave: string };
export const lerIndiceBusca = () => ler<MunicipioBusca[]>("data/derivados/busca_municipios.json");
export const normalizarBusca = (texto: string) => texto.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLocaleLowerCase("pt-BR");

// Respostas derivadas de snapshots só mudam com um novo deploy, que renova o cache da CDN.
export const CACHE_PUBLICO = { "Cache-Control": "public, max-age=0, s-maxage=86400, stale-while-revalidate=604800" };
