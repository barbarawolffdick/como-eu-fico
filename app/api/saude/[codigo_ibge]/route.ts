import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { NextResponse } from "next/server";
import type { SaudeMunicipal } from "@/lib/saude";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

// O arquivo é imutável durante o deploy. Cada visita recebe somente sua cidade.
let snapshotPromise: Promise<{ esquema: number; status: string; municipios_referencia: number;
  registros: Record<string, SaudeMunicipal> }> | undefined;
function carregarSnapshot() {
  snapshotPromise ??= readFile(join(process.cwd(), "data/public/saude_municipal.json"), "utf8")
    .then(raw => {
      const snapshot = JSON.parse(raw);
      if (snapshot.esquema !== 2 || snapshot.status !== "NACIONAL" ||
          Object.keys(snapshot.registros).length !== snapshot.municipios_referencia) throw Error("Snapshot inválido");
      return snapshot;
    }).catch(erro => { snapshotPromise = undefined; throw erro; });
  return snapshotPromise;
}

export async function GET(_request: Request, context: { params: Promise<{ codigo_ibge: string }> }) {
  const { codigo_ibge } = await context.params;
  if (!/^\d{7}$/.test(codigo_ibge)) return NextResponse.json({ detail: "Código IBGE inválido" }, { status: 400 });
  try {
    const snapshot = await carregarSnapshot();
    const dados = snapshot.registros[codigo_ibge];
    if (!dados) {
      return NextResponse.json({ detail: "Município não encontrado" }, { status: 404 });
    }
    return NextResponse.json({ status: "NACIONAL", disponivel: true, dados,
      municipios_referencia: snapshot.municipios_referencia });
  } catch {
    return NextResponse.json({ detail: "Não foi possível carregar os indicadores de saúde." }, { status: 503 });
  }
}
