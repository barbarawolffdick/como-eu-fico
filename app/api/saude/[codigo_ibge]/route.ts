import { NextResponse } from "next/server";
import type { SaudeMunicipal, FinanciamentoSaude, OrigemSaude } from "@/lib/saude";
import { CACHE_PUBLICO, lerManifesto, registroMunicipal } from "@/lib/snapshots";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

// Lê somente os fragmentos da UF da cidade; a contagem de registros de cada snapshot
// é conferida no build, ao gerar os fragmentos (scripts/fragmentar_snapshots.mjs).
async function cabecalhos() {
  const { snapshots } = await lerManifesto();
  const saude = snapshots["saude_municipal.json"].metadados as { esquema: number; status: string; municipios_referencia: number };
  const financiamento = snapshots["financiamento_saude.json"].metadados as { esquema: number; fontes: Record<string, OrigemSaude> };
  if (saude.esquema !== 2 || saude.status !== "NACIONAL") throw Error("Snapshot inválido");
  if (financiamento.esquema !== 1) throw Error("Financiamento inválido");
  return { saude, financiamento };
}

export async function GET(_request: Request, context: { params: Promise<{ codigo_ibge: string }> }) {
  const { codigo_ibge } = await context.params;
  if (!/^\d{7}$/.test(codigo_ibge)) return NextResponse.json({ detail: "Código IBGE inválido" }, { status: 400 });
  try {
    const [{ saude, financiamento }, dados, financiamentoCidade] = await Promise.all([cabecalhos(),
      registroMunicipal<SaudeMunicipal>("saude_municipal", codigo_ibge),
      registroMunicipal<FinanciamentoSaude>("financiamento_saude", codigo_ibge)]);
    if (!dados) {
      return NextResponse.json({ detail: "Município não encontrado" }, { status: 404 });
    }
    if (!financiamentoCidade) throw Error("Financiamento municipal ausente");
    return NextResponse.json({ status: "NACIONAL", disponivel: true, dados,
      financiamento: financiamentoCidade, fontes_financiamento: financiamento.fontes,
      municipios_referencia: saude.municipios_referencia }, { headers: CACHE_PUBLICO });
  } catch {
    return NextResponse.json({ detail: "Não foi possível carregar os indicadores de saúde." }, { status: 503 });
  }
}
