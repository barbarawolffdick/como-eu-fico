import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { NextResponse } from "next/server";
import type { SaudeMunicipal } from "@/lib/saude";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(_request: Request, context: { params: Promise<{ codigo_ibge: string }> }) {
  const { codigo_ibge } = await context.params;
  if (!/^\d{7}$/.test(codigo_ibge)) return NextResponse.json({ detail: "Código IBGE inválido" }, { status: 400 });
  try {
    const [raw, municipios] = await Promise.all([
      readFile(join(process.cwd(), "data/public/saude_piloto.json"), "utf8"),
      readFile(join(process.cwd(), "data/public/rankings_2026.json"), "utf8"),
    ]);
    const snapshot = JSON.parse(raw) as { esquema: number; status: string; municipios_piloto: string[]; registros: Record<string, SaudeMunicipal> };
    if (snapshot.esquema !== 1 || snapshot.status !== "PILOTO" || Object.keys(snapshot.registros).length !== snapshot.municipios_piloto.length) throw Error("Snapshot inválido");
    if (!JSON.parse(municipios).registros.some((m: { codigo_ibge: string }) => m.codigo_ibge === codigo_ibge)) {
      return NextResponse.json({ detail: "Município não encontrado" }, { status: 404 });
    }
    const dados = snapshot.registros[codigo_ibge] || null;
    return NextResponse.json({ status: "PILOTO", disponivel: dados !== null, dados,
      municipios_piloto: snapshot.municipios_piloto,
      motivo: dados ? undefined : "Esta cidade ainda não faz parte do piloto de saúde. Isso não significa ausência de recursos ou serviços." });
  } catch {
    return NextResponse.json({ detail: "Não foi possível carregar os indicadores de saúde." }, { status: 503 });
  }
}
