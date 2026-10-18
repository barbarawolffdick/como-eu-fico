import type { NextConfig } from "next";

// lib/snapshots.ts lê arquivos por caminho calculado, que o rastreamento do Next não
// detecta. Os snapshots canônicos menores e o manifesto acompanham todas as funções;
// os fragmentos por UF, apenas as rotas que os consultam. Os snapshots completos de
// saúde e financiamento (66 MB) não são lidos em produção.
const comuns = ["rankings_2026", "detalhes_2026", "familias_mds", "pessoas_mds", "pessoas_mds_mensal"].map(nome => `./data/public/${nome}.json`);
const derivados = (...nomes: string[]) => nomes.map(nome => "./data/derivados/" + nome);
const nextConfig: NextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: process.cwd(),
  outputFileTracingIncludes: {
    "/**": [...comuns, ...derivados("manifesto.json")],
    "/api/municipios": derivados("busca_municipios.json"),
    "/api/municipios/[codigo_ibge]": derivados("detalhes_2026/*.json"),
    "/api/saude/[codigo_ibge]": derivados("saude_municipal/*.json", "financiamento_saude/*.json"),
    "/api/explorar": derivados("explorar_saude.json"),
    "/api/dinheiro-federal/[codigo_ibge]": derivados("dinheiro_federal/*.json", "emendas/*.json"),
    "/api/dinheiro-federal/regioes": derivados("dinheiro_federal_regioes.json"),
  },
};
export default nextConfig;
