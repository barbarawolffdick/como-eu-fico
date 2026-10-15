import { NextResponse } from "next/server";
import { fontesPublicadas } from "@/lib/fontes";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  try {
    return NextResponse.json(await fontesPublicadas());
  } catch {
    return NextResponse.json({ detail: "Não foi possível consultar as fontes publicadas." }, { status: 503 });
  }
}
