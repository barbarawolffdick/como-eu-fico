import { NextResponse } from "next/server";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
export const runtime="nodejs";
export const dynamic="force-dynamic";
export async function GET(_request:Request,context:{params:Promise<{codigo_ibge:string}>}) {
 const {codigo_ibge}=await context.params;
 if(!/^\d{7}$/.test(codigo_ibge))return NextResponse.json({detail:"Código IBGE inválido"},{status:400});
 try {
  const data=JSON.parse(await readFile(join(process.cwd(),"data/public/detalhes_2026.json"),"utf8"));
  const item=data.registros[codigo_ibge];
  return item?NextResponse.json(item):NextResponse.json({detail:"Município não encontrado"},{status:404});
 } catch {return NextResponse.json({detail:"Snapshot de municípios indisponível no repositório."},{status:503});}
}
