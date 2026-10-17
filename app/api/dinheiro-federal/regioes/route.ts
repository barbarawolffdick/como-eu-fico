import { NextResponse } from "next/server";
import type { RespostaRegioes } from "@/lib/dinheiro-federal";
import { CACHE_PUBLICO, lerRegioesFederais } from "@/lib/snapshots";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  try {
    return NextResponse.json(await lerRegioesFederais<RespostaRegioes>(), { headers: CACHE_PUBLICO });
  } catch {
    return NextResponse.json({ detail: "Não foi possível carregar a relação entre regiões." }, { status: 503 });
  }
}
