import { NextRequest, NextResponse } from "next/server";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type Registro = {codigo_ibge:string;nome:string;uf:string;populacao:number|null;ano_populacao:number|null;valor_centavos:number|null;parcelas:number|null;competencias:number|null;vencedor:string|null;votos_vencedor:number|null;votos_total:number|null;empatados:number|null};
type Snapshot = {esquema:number;inicio:string;fim:string;municipios:number;populacao_completa:boolean;registros:Registro[]};

export async function GET(req: NextRequest) {
  let data: Snapshot;
  try {
    data = JSON.parse(await readFile(join(process.cwd(), "data/public/rankings_2026.json"), "utf8")) as Snapshot;
    if (data.esquema !== 1 || data.municipios !== 5571 || data.registros.length !== 5571) throw new Error("snapshot inválido");
  } catch {
    return NextResponse.json({detail:"Snapshot de rankings ainda não publicado. Execute python scripts/exportar_rankings_web.py e versione data/public/rankings_2026.json."}, {status:503});
  }
  const q = req.nextUrl.searchParams;
  const metrica = q.get("metrica") || "valor_total";
  const vencedor = q.get("vencedor") || "todos";
  const uf = q.get("uf") || "";
  const inicio = q.get("inicio") || "202601";
  const fim = q.get("fim") || "202608";
  const limite = Number(q.get("limite") || "10");
  if (!["valor_total","valor_habitante"].includes(metrica) || !["todos","13","22","outros"].includes(vencedor) ||
      (uf !== "" && !/^[A-Z]{2}$/.test(uf)) || inicio !== data.inicio || fim !== data.fim ||
      !Number.isInteger(limite) || limite < 1 || limite > 100) {
    return NextResponse.json({detail:"Parâmetros inválidos ou período não publicado."},{status:422});
  }
  if (metrica==="valor_habitante" && !data.populacao_completa) return NextResponse.json({metrica,inicio,fim,disponivel:false,motivo:"População IBGE ainda não está no SQLite publicado no GitHub.",resultados:[]});
  const rows = data.registros.filter(m=>m.valor_centavos!==null && m.empatados===1 &&
    !!m.vencedor && (!uf || m.uf===uf) &&
    (vencedor==="todos" || (vencedor==="outros" ? !["13","22"].includes(m.vencedor) : m.vencedor===vencedor)) &&
    (metrica==="valor_total" || (m.populacao!==null && m.populacao>0 && m.ano_populacao!==null)))
   .map(m=>({...m,percentual_vencedor:m.votos_total&&m.votos_vencedor!==null?100*m.votos_vencedor/m.votos_total:null,
                centavos_por_habitante:m.populacao&&m.valor_centavos!==null?m.valor_centavos/m.populacao:null}))
   .sort((a,b)=>{
      const av=metrica==="valor_total"?a.valor_centavos:a.centavos_por_habitante;
      const bv=metrica==="valor_total"?b.valor_centavos:b.centavos_por_habitante;
      return (bv??0)-(av??0) || a.codigo_ibge.localeCompare(b.codigo_ibge);
   }).slice(0,limite);
  return NextResponse.json({metrica,vencedor,uf,inicio,fim,disponivel:true,resultados:rows,
     nota:"Valores registrados por competência. Valor por habitante não mede cobertura de famílias. Votos são agregados municipais."});
}
