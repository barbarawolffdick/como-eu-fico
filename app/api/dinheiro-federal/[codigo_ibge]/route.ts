import { NextResponse } from "next/server";
import type { DinheiroFederalCidade, PibReferencia } from "@/lib/dinheiro-federal";
import { CACHE_PUBLICO, lerManifesto, registroMunicipal } from "@/lib/snapshots";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(_request: Request, context: { params: Promise<{ codigo_ibge: string }> }) {
  const { codigo_ibge } = await context.params;
  if (!/^\d{7}$/.test(codigo_ibge)) return NextResponse.json({ detail: "Código IBGE inválido" }, { status: 400 });
  try {
    const [{ snapshots, dinheiro_federal_atual }, cidade] = await Promise.all([lerManifesto(), registroMunicipal<DinheiroFederalCidade>("dinheiro_federal", codigo_ibge)]);
    if (!cidade) return NextResponse.json({ detail: "Município não encontrado" }, { status: 404 });
    const meta = snapshots[dinheiro_federal_atual].metadados as { esquema: number; ano: number; pib?: PibReferencia };
    if (meta.esquema !== 1) throw Error("Snapshot inválido");
    return NextResponse.json({ ano: meta.ano, pib: meta.pib ?? { ano_fonte: meta.ano, estimado: false }, cidade }, { headers: CACHE_PUBLICO });
  } catch {
    return NextResponse.json({ detail: "Não foi possível carregar o dinheiro federal da cidade." }, { status: 503 });
  }
}
