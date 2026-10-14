import {NextRequest,NextResponse} from "next/server";
import {readFile} from "node:fs/promises";
import {join} from "node:path";
export const runtime="nodejs";
export const dynamic="force-dynamic";
type Row={codigo_ibge:string;nome:string;uf:string;populacao:number|null;valor_centavos:number|null;vencedor:string|null;votos_vencedor:number|null;votos_total:number|null;empatados:number|null};
type Detail={bolsa_familia:{mes_competencia:string;valor_centavos:number}[]};
const groups=["13","22","outros"];
const group=(r:Row)=>r.vencedor==="13"?"13":r.vencedor==="22"?"22":"outros";
export async function GET(req:NextRequest){
 try{
 const [rjson,djson]=await Promise.all([readFile(join(process.cwd(),"data/public/rankings_2026.json"),"utf8"),readFile(join(process.cwd(),"data/public/detalhes_2026.json"),"utf8")]);
 const r=JSON.parse(rjson),d=JSON.parse(djson);
 if(r.municipios!==5571||d.municipios!==5571)throw Error("Cobertura inconsistente");
 const uf=req.nextUrl.searchParams.get("uf")||"";
 if(uf&&!/^[A-Z]{2}$/.test(uf))return NextResponse.json({detail:"UF inválida"},{status:422});
 const all:Row[]=r.registros.filter((x:Row)=>x.empatados===1&&x.populacao&&x.populacao>0&&x.valor_centavos!==null&&x.vencedor&&(!uf||x.uf===uf));
 const amount=(x:Row)=>x.valor_centavos!*1.0/x.populacao!;
 const values=all.map(amount).sort((a,b)=>a-b);
 const quantile=(p:number)=>values.length?values[Math.floor((values.length-1)*p)]:0;
 const q1=quantile(.25),median=quantile(.5),q3=quantile(.75);
 const histogram=groups.map(key=>({grupo:key,faixas:[0,0,0,0],total:0}));
 const cutoffs=[quantile(.25),quantile(.5),quantile(.75)];
 for(const x of all){const h=histogram.find(h=>h.grupo===group(x))!;h.total++;let i=0;while(i<3&&amount(x)>cutoffs[i])i++;h.faixas[i]++;}
 const outliers=all.filter(x=>group(x)==="13"||group(x)==="22").sort((a,b)=>group(a)===group(b)?amount(b)-amount(a):group(a)==="22"?-1:1);
 const uncommon={flavioAlto:outliers.filter(x=>group(x)==="22"&&amount(x)>=q3).slice(0,10),lulaBaixo:outliers.filter(x=>group(x)==="13"&&amount(x)<=q1).sort((a,b)=>amount(a)-amount(b)).slice(0,10)};
 const meses=["202601","202602","202603","202604","202605","202606","202607","202608"];
 const evolution=meses.map(mes=>{
   const z:Record<string,number|string>={mes};
   for(const key of ["13","22"]){
    const subset=all.filter(x=>group(x)===key);
    const pop=subset.reduce((s,x)=>s+x.populacao!,0);
    const cents=subset.reduce((s,x)=>s+(d.registros[x.codigo_ibge] as Detail)?.bolsa_familia.find(y=>y.mes_competencia===mes)?.valor_centavos||0,0);
    z[key]=pop?cents/pop/100:0;
   }return z;
 });
 const others=all.filter(x=>group(x)==="outros").sort((a,b)=>b.votos_vencedor!/b.votos_total!-a.votos_vencedor!/a.votos_total!).map(x=>({...x,valor_por_habitante:amount(x)/100}));
 return NextResponse.json({unidade:"R$ por habitante no acumulado janeiro-agosto 2026",uf,universo:all.length,quartis:{q1:q1/100,mediana:median/100,q3:q3/100},distribuicao:histogram.map(h=>({...h,percentuais:h.faixas.map(n=>h.total?100*n/h.total:0)})),excecoes:{flavioAlto:uncommon.flavioAlto.map(x=>({...x,valor_por_habitante:amount(x)/100})),lulaBaixo:uncommon.lulaBaixo.map(x=>({...x,valor_por_habitante:amount(x)/100}))},evolucao:evolution,outros:others});
 }catch(e){return NextResponse.json({detail:"Não foi possível calcular as análises: "+(e as Error).message},{status:503});}
}
