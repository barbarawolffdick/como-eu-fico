import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const base = process.env.FASTAPI_BASE_URL?.replace(/\/$/, "");
  if (!base) return NextResponse.json({ detail: "API de dados não configurada. Defina FASTAPI_BASE_URL para conectar ao FastAPI com o SQLite real." }, { status: 503 });
  const { path } = await context.params;
  // Only publicly exposed read-only endpoints are proxied.
  if (request.method !== "GET" || !["municipios", "fontes", "health", "rankings"].includes(path[0]) || (path[0] !== "municipios" && path.length !== 1) || path.length > 2 || (path.length === 2 && !/^\d{7}$/.test(path[1]))) {
    return NextResponse.json({ detail: "Rota não permitida" }, { status: 404 });
  }
  const url = new URL(base + "/api/" + path.join("/"));
  url.search = request.nextUrl.search;
  try {
    const response = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(8000) });
    const body = await response.text();
    return new NextResponse(body, { status: response.status, headers: { "content-type": response.headers.get("content-type") || "application/json", "cache-control": "no-store" } });
  } catch {
    return NextResponse.json({ detail: "Não foi possível conectar à API de dados. Verifique FASTAPI_BASE_URL e se o FastAPI está acessível a partir do servidor Next.js." }, { status: 503 });
  }
}
export { proxy as GET };
