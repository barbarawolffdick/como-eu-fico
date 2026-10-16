import { NextRequest,NextResponse } from "next/server";
import { CACHE_PUBLICO, lerIndiceBusca, normalizarBusca } from "@/lib/snapshots";
export const runtime="nodejs";
export const dynamic="force-dynamic";
// Busca sem distinção de acentos; nomes iguais ao termo vêm antes, depois os que começam por ele.
export async function GET(request:NextRequest) {
 try {
  const indice=await lerIndiceBusca();
  const q=normalizarBusca((request.nextUrl.searchParams.get("q")||"").trim());
  const limit=Math.min(100,Math.max(1,Number(request.nextUrl.searchParams.get("limit")||"30")));
  const ordem=(x:{chave:string})=>x.chave===q?0:x.chave.startsWith(q)?1:2;
  const encontrados=indice.filter(x=>x.codigo_ibge.includes(q)||x.chave.includes(q));
  const resultado=encontrados.map((x,i)=>({x,i})).sort((a,b)=>ordem(a.x)-ordem(b.x)||a.i-b.i).slice(0,limit)
   .map(({x:{codigo_ibge,nome,uf,populacao,ano_populacao}})=>({codigo_ibge,nome,uf,populacao,ano_populacao}));
  return NextResponse.json(resultado,{headers:CACHE_PUBLICO});
 } catch {return NextResponse.json({detail:"Snapshot de municípios indisponível no repositório."},{status:503});}
}
