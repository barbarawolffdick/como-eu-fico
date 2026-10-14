import {NextRequest,NextResponse} from "next/server";
import {readFile} from "node:fs/promises";
import {join} from "node:path";
export const runtime="nodejs";
export const dynamic="force-dynamic";
type Cobertura={pessoas:number|null;populacao:number;cobertura_pct:number|null};
type Source={esquema:number;unidade:string;periodo:string;municipios_ibge:number;municipios_com_dado:number;registros:Record<string,Cobertura>;pagina_fonte:string};
type Cidade={codigo_ibge:string;nome:string;uf:string;vencedor:string|null;empatados:number};
export async function GET(req:NextRequest){
 try {
  const [cstr,rstr]=await Promise.all([
   readFile(join(process.cwd(),"data/public/pessoas_mds.json"),"utf8"),
   readFile(join(process.cwd(),"data/public/rankings_2026.json"),"utf8")]);
  const c=JSON.parse(cstr) as Source,r=JSON.parse(rstr);
  if(c.esquema!==1||c.unidade!=="pessoas_em_familias_beneficiarias"||
     c.municipios_ibge!==5571||r.municipios!==5571||Object.keys(c.registros).length!==5571)
    throw Error("Snapshot MDS/IBGE inválido");
  const q=req.nextUrl.searchParams;
  const municipio=q.get("municipio")||"";
  const uf=q.get("uf")||"";
  const vencedor=q.get("vencedor")||"todos";
  const limite=Number(q.get("limite")||"10");
  if((municipio&&!/^\d{7}$/.test(municipio))||(uf&&!/^[A-Z]{2}$/.test(uf))||
      !["todos","13","22","outros"].includes(vencedor)||!Number.isInteger(limite)||limite<1||limite>100)
   return NextResponse.json({detail:"Filtros inválidos"},{status:422});
  const mapa=(r.registros as Cidade[]).map(m=>({...m,...c.registros[m.codigo_ibge]}));
  if(municipio){
   const item=mapa.find(x=>x.codigo_ibge===municipio);
   if(!item)return NextResponse.json({detail:"Município não encontrado"},{status:404});
   return NextResponse.json({fonte:c.pagina_fonte,periodo:c.periodo,
    descricao:"Percentual de moradores integrantes de famílias beneficiárias, não percentual de titulares que recebem pagamentos.",
    disponivel:item.cobertura_pct!==null,municipio:item});
  }
  const resultados=mapa.filter(m=>m.cobertura_pct!==null&&(!uf||m.uf===uf)&&m.empatados===1&&
    (vencedor==="todos"||(vencedor==="outros"?!["13","22"].includes(m.vencedor||""):m.vencedor===vencedor)))
    .sort((a,b)=>(b.cobertura_pct||0)-(a.cobertura_pct||0)||a.codigo_ibge.localeCompare(b.codigo_ibge))
    .slice(0,limite);
  return NextResponse.json({fonte:c.pagina_fonte,periodo:c.periodo,unidade:c.unidade,
   municipios_ibge:c.municipios_ibge,municipios_com_dado:c.municipios_com_dado,
   indicador:"Percentual da população em famílias beneficiárias do Bolsa Família",uf,vencedor,resultados});
 }catch(e){return NextResponse.json({detail:"Cobertura MDS indisponível: "+(e as Error).message},{status:503});}
}
