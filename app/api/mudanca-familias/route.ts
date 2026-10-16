import {NextResponse} from "next/server";
import {CACHE_PUBLICO,lerSnapshot} from "@/lib/snapshots";
export const runtime="nodejs";
export const dynamic="force-dynamic";
type M={codigo_ibge:string;nome:string;uf:string;vencedor:string|null;empatados:number};
export async function GET(req:Request){
 try{
  const uf=new URL(req.url).searchParams.get("uf")||"";
  if(uf&&!/^[A-Z]{2}$/.test(uf))return NextResponse.json({detail:"UF inválida"},{status:422});
  const [r,f]=await Promise.all([lerSnapshot<any>("rankings_2026.json"),lerSnapshot<any>("familias_mds.json")]);
  if(r.municipios!==5571||f.municipios!==5571||f.unidade!=="familias_beneficiarias")throw Error("Cobertura ou unidade incompatível");
  const [inicio,fim]=f.periodos;
  const elegiveis:M[]=r.registros.filter((x:M)=>x.empatados===1&&x.vencedor&&(!uf||x.uf===uf));
  const changed=elegiveis.flatMap(x=>{
   const a=f.registros[inicio][x.codigo_ibge],b=f.registros[fim][x.codigo_ibge];
   if(!Number.isInteger(a)||!Number.isInteger(b))return [];
   return [{...x,antes:a,depois:b,delta:b-a,variacao_percentual:a?100*(b-a)/a:null,
    situacao:b>a?"aumentou":b<a?"diminuiu":"estavel"}];
  });
  const grupos=["13","22","outros"];
  const pertence=(x:M,g:string)=>g==="outros"?!["13","22"].includes(x.vencedor||""):x.vencedor===g;
  const porVencedor=grupos.map(grupo=>{
   const list=changed.filter(x=>pertence(x,grupo));
   return {grupo,total:list.length,aumentou:list.filter(x=>x.situacao==="aumentou").length,
    diminuiu:list.filter(x=>x.situacao==="diminuiu").length,estavel:list.filter(x=>x.situacao==="estavel").length};
  });
  const porMudanca=["aumentou","diminuiu","estavel"].map(situacao=>{
   const list=changed.filter(x=>x.situacao===situacao);
   return {situacao,total:list.length,...Object.fromEntries(grupos.map(g=>[g,list.filter(x=>pertence(x,g)).length]))};
  });
  const exemplos=changed.filter(x=>x.situacao==="aumentou").sort((a,b)=>b.delta-a.delta).slice(0,15);
  return NextResponse.json({fonte:"MDS VIS DATA",indicador:"Famílias beneficiárias do Bolsa Família",inicio,fim,
   municipios:changed.length,porVencedor,porMudanca,exemplos,
   nota:"Contagem de famílias beneficiárias, não pessoas. Comparação territorial descritiva; não permite atribuição causal."},{headers:CACHE_PUBLICO});
 }catch(e){return NextResponse.json({detail:"Fonte MDS ainda não disponível ou falha de validação: "+(e as Error).message},{status:503});}
}
