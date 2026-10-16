import {NextResponse} from "next/server";
import {CACHE_PUBLICO,lerSnapshot} from "@/lib/snapshots";
export const runtime="nodejs";
export const dynamic="force-dynamic";
type M={codigo_ibge:string;nome:string;uf:string;vencedor:string|null;empatados:number};
type Mes={mes_competencia:string;parcelas:number};
type Det={bolsa_familia:Mes[]};
export async function GET(req:Request){
 try{
 const url=new URL(req.url),uf=url.searchParams.get("uf")||"";
 if(uf&&!/^[A-Z]{2}$/.test(uf))return NextResponse.json({detail:"UF inválida"},{status:422});
 const [r,d]=await Promise.all([lerSnapshot<any>("rankings_2026.json"),lerSnapshot<any>("detalhes_2026.json")]);
 if(r.municipios!==5571||d.municipios!==5571)throw Error("Cobertura divergente");
 const rows:M[]=r.registros.filter((m:M)=>m.empatados===1&&m.vencedor&&(!uf||m.uf===uf));
 const allMonths=[...new Set<string>(Object.values(d.registros as Record<string,Det>).flatMap(x=>x.bolsa_familia.map(y=>y.mes_competencia)))].sort();
 const inicio=allMonths[0],fim=allMonths[allMonths.length-1];
 const changed=rows.flatMap(m=>{
  const meses=(d.registros[m.codigo_ibge] as Det)?.bolsa_familia||[];
  const before=meses.find(x=>x.mes_competencia===inicio)?.parcelas;
  const after=meses.find(x=>x.mes_competencia===fim)?.parcelas;
  if(before===undefined||after===undefined)return [];
  const delta=after-before;
  return [{...m,inicio:before,fim:after,delta,variacao_percentual:before>0?delta*100/before:null,
    situacao:delta>0?"aumentou":delta<0?"diminuiu":"estavel"}];
 });
 const candidates=["13","22","outros"];
 const belongs=(m:M,g:string)=>g==="outros"?!["13","22"].includes(m.vencedor||""):m.vencedor===g;
 const porVencedor=candidates.map(grupo=>{
  const list=changed.filter(x=>belongs(x,grupo));
  return {grupo,total:list.length,
   aumentou:list.filter(x=>x.situacao==="aumentou").length,
   diminuiu:list.filter(x=>x.situacao==="diminuiu").length,
   estavel:list.filter(x=>x.situacao==="estavel").length};
 });
 const porMudanca=["aumentou","diminuiu","estavel"].map(situacao=>{
  const list=changed.filter(x=>x.situacao===situacao);
  return {situacao,total:list.length,...Object.fromEntries(candidates.map(g=>[g,list.filter(x=>belongs(x,g)).length]))};
 });
 const exemplos=changed.filter(x=>x.situacao==="aumentou").sort((a,b)=>b.delta-a.delta).slice(0,20);
 return NextResponse.json({indicador:"Número de parcelas registradas por competência; não é número de famílias ou pessoas beneficiárias",inicio,fim,municipios:changed.length,porVencedor,porMudanca,exemplos},{headers:CACHE_PUBLICO});
 }catch(e){return NextResponse.json({detail:(e as Error).message},{status:503});}
}
