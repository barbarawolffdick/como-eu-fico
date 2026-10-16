import { NextResponse } from "next/server";
import { CACHE_PUBLICO, registroMunicipal } from "@/lib/snapshots";
export const runtime="nodejs";
export const dynamic="force-dynamic";
export async function GET(_request:Request,context:{params:Promise<{codigo_ibge:string}>}) {
 const {codigo_ibge}=await context.params;
 if(!/^\d{7}$/.test(codigo_ibge))return NextResponse.json({detail:"Código IBGE inválido"},{status:400});
 try {
  const item=await registroMunicipal("detalhes_2026",codigo_ibge);
  return item?NextResponse.json(item,{headers:CACHE_PUBLICO}):NextResponse.json({detail:"Município não encontrado"},{status:404});
 } catch {return NextResponse.json({detail:"Snapshot de municípios indisponível no repositório."},{status:503});}
}
