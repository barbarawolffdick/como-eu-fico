export type BeneficiariosCidade = {
  codigo_ibge: string;
  periodos: Record<string, { pessoas: number | null; familias: number | null }>;
  pessoas_disponiveis: boolean;
  aviso: string | null;
  fontes: { pessoas: { url: string; sha256: string; data_extracao: string } | null;
    familias: { arquivo: string; sha256: string } };
};

export function mediaPorBeneficiario(centavos: number | null | undefined, quantidade: number | null | undefined) {
  return centavos != null && Number.isFinite(centavos) && quantidade != null && Number.isInteger(quantidade) && quantidade > 0
    ? centavos / quantidade : null;
}

export function leituraCobertura(percentual: number) {
  if (percentual === 0) return "A fonte informa zero moradores em famílias beneficiárias neste mês.";
  if (percentual < 1) return "Menos de 1 em cada 100 moradores vive em uma família que recebe o Bolsa Família.";
  if (percentual > 99 && percentual < 100) return "Quase todos os moradores vivem em famílias que recebem o Bolsa Família.";
  return `Cerca de ${Math.round(percentual).toLocaleString("pt-BR")} em cada 100 moradores vivem em famílias que recebem o Bolsa Família.`;
}

const faixas = ["(case when coalesce(t.n_pess_070_140_cad_pbf,0) + coalesce(t.n_", "n_pess_140_272_cad_pbf", "(t.n_pess_cad_pbf - (t.n_pess_070_cad_pbf + t.n_pess_070_140_ca"];
const normalizar = (s: string) => s.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toUpperCase().replace(/[^A-Z0-9]/g, "");
export function pessoasTabulares(html: string, cidade: { codigo_ibge: string; nome: string; uf: string; aliases?: string[] }) {
  const blocos = [...html.matchAll(/var strJsondados = '([\s\S]*?)';/g)];
  if (blocos.length !== 1) throw Error("Bloco tabular ausente ou ambíguo");
  const linhas: Record<string, unknown>[] = JSON.parse(blocos[0][1].replace(/\\'/g, "'"));
  if (!Array.isArray(linhas) || !linhas.length) throw Error("Série tabular vazia");
  const periodos: Record<string, number> = {};
  for (const row of linhas) {
    if (String(row.codigo) !== cidade.codigo_ibge.slice(0, 6) || row.sigla !== cidade.uf ||
        typeof row.nome !== "string" || ![cidade.nome, ...(cidade.aliases ?? [])].some(nome => normalizar(row.nome as string) === normalizar(nome))) throw Error("Identidade municipal divergente");
    const data = String(row.mes_ano);
    if (!/^\d{4}-(0[1-9]|1[0-2])-01$/.test(data) || data > new Date().toISOString().slice(0, 10)) throw Error("Competência inválida");
    const mes = data.slice(0, 7).replace("-", "");
    if (Object.hasOwn(periodos, mes)) throw Error("Competência duplicada");
    const valores = [...faixas, "n_pess_cad_pbf"].map(k => row[k]);
    // Lacuna mensal não é zero; períodos sem contagem válida não são publicados.
    if (valores.some(v => v == null)) continue;
    if (!valores.every(v => typeof v === "number" && Number.isSafeInteger(v) && v >= 0)) throw Error("Contagem inválida");
    const [a, b, c, total] = valores as number[];
    if (a + b + c !== total) throw Error("Faixas não reconciliam com o total");
    periodos[mes] = total;
  }
  if (!Object.keys(periodos).length) throw Error("Série sem contagens válidas");
  return periodos;
}
