import { NextResponse } from "next/server";
import { lerFiltros } from "@/lib/explorar";
import { consultarExploracao } from "@/lib/explorar-dados";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  let filtros;
  try { filtros = lerFiltros(new URL(request.url).searchParams); }
  catch { return NextResponse.json({ detail: "Filtros inválidos. Confira região, estado, indicador e ordenação." }, { status: 422 }); }
  try { return NextResponse.json(await consultarExploracao(filtros)); }
  catch { return NextResponse.json({ detail: "Não foi possível consultar os dados deste tema. Tente novamente." }, { status: 503 }); }
}
