import { NextRequest,NextResponse } from "next/server";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
export const runtime="nodejs";
export const dynamic="force-dynamic";
export async function GET(request:NextRequest) {
 try {
  const data=JSON.parse(await readFile(join(process.cwd(),"data/public/detalhes_2026.json"),"utf8"));
  const q=(request.nextUrl.searchParams.get("q")||"").trim().toLocaleLowerCase("pt-BR");
  const limit=Math.min(100,Math.max(1,Number(request.nextUrl.searchParams.get("limit")||"30")));
  const registros=Object.values(data.registros) as {municipio:{codigo_ibge:string;nome:string;uf:string;populacao:number|null;ano_populacao:number|null}}[];
  return NextResponse.json(registros.map(x=>x.municipio).filter(x=>x.codigo_ibge.includes(q)||x.nome.toLocaleLowerCase("pt-BR").includes(q)).sort((a,b)=>a.nome.localeCompare(b.nome,"pt-BR")).slice(0,limit));
 } catch {return NextResponse.json({detail:"Snapshot de municípios indisponível no repositório."},{status:503});}
}
