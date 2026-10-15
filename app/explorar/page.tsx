"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

type Item = {codigo_ibge:string;nome:string;uf:string;valor_centavos:number;centavos_por_habitante:number|null;vencedor:string;percentual_vencedor:number;ano_populacao:number|null};
type CoverageItem={codigo_ibge:string;nome:string;uf:string;vencedor:string|null;pessoas:number|null;populacao:number;cobertura_pct:number|null};
type CoverageResult={periodo:string;municipios_com_dado:number;resultados:CoverageItem[]};
type Resultado = {disponivel:boolean;motivo?:string;resultados:Item[]};
const names:Record<string,string>={"13":"Lula","22":"Flávio Bolsonaro","14":"Renan Santos","16":"Hertz Dias","21":"Edmilson Costa","27":"Clariana Barão","29":"Rui Costa Pimenta","30":"Zema","35":"Veterinário Wilson Grassi","55":"Ronaldo Caiado","70":"Escritor Augusto Cury","80":"Samara"};
const moeda=(v:number)=>new Intl.NumberFormat("pt-BR",{style:"currency",currency:"BRL"}).format(v/100);
export default function Explorar(){
 const [metrica,setMetrica]=useState("valor_total");
 const [vencedor,setVencedor]=useState("todos");
 const [uf,setUf]=useState("");
 const [dados,setDados]=useState<Resultado|null>(null);
 const [erro,setErro]=useState("");
 const [comparativos,setComparativos]=useState<Record<string,Resultado>>({});
 const [erroComparativo,setErroComparativo]=useState("");
 const [loading,setLoading]=useState(true);
 const [coberturas,setCoberturas]=useState<Record<string,CoverageResult>>({});
 const [erroCobertura,setErroCobertura]=useState("");
 useEffect(()=>{
  let ativo=true;setLoading(true);setErro("");
  const q=new URLSearchParams({metrica,vencedor,uf,inicio:"202601",fim:"202608",limite:"10"});
  fetch("/api/rankings?"+q).then(async r=>{const v=await r.json();if(!r.ok)throw Error(v.detail||"Erro na consulta");return v as Resultado})
   .then(v=>{if(ativo)setDados(v)}).catch(e=>{if(ativo){setErro(e.message);setDados(null)}}).finally(()=>{if(ativo)setLoading(false)});
  return ()=>{ativo=false};
 },[metrica,vencedor,uf]);
 useEffect(()=>{
  let ativo=true;
  setComparativos({});
  setErroComparativo("");
  Promise.all(["22","13"].map(async numero=>{
   const q=new URLSearchParams({metrica:"valor_habitante",vencedor:numero,uf,inicio:"202601",fim:"202608",limite:"10"});
   const response=await fetch("/api/rankings?"+q,{cache:"no-store"});
   const result=await response.json();
   if(!response.ok)throw Error(result.detail||"Falha ao carregar comparação");
   return [numero,result] as const;
  })).then(entries=>{if(ativo)setComparativos(Object.fromEntries(entries));})
    .catch(e=>{if(ativo)setErroComparativo(e.message);});
  return ()=>{ativo=false};
 },[uf]);
 useEffect(()=>{
  let ativo=true;setCoberturas({});setErroCobertura("");
  Promise.all(["22","13"].map(async numero=>{
    const p=new URLSearchParams({vencedor:numero,uf,limite:"10"});
    const r=await fetch("/api/cobertura?"+p,{cache:"no-store"});
    const d=await r.json();
    if(!r.ok)throw Error(d.detail||"Dados de cobertura indisponíveis");
    return [numero,d as CoverageResult] as const;
  })).then(rows=>{if(ativo)setCoberturas(Object.fromEntries(rows));})
    .catch(e=>{if(ativo)setErroCobertura(e.message)});
  return ()=>{ativo=false};
 },[uf]);
 return <><header className="masthead"><div className="shell"><div className="topbar"><Link href="/" className="brand">Como Eu Fico</Link><span className="tag">Explorar o Brasil</span></div><div className="hero"><div className="eyebrow">Comparação municipal</div><h1>Explore os municípios brasileiros</h1><p>Compare registros do Bolsa Família e resultados eleitorais por município.</p></div></div></header>
 <main className="shell main"><section className="searchpanel"><h2>Rankings municipais</h2><p><Link href="/analises">Explorar quatro análises territoriais →</Link></p><div className="ranking-controls">
 <label>Métrica<select value={metrica} onChange={e=>setMetrica(e.target.value)}><option value="valor_total">Valor total do Bolsa Família</option><option value="valor_habitante">Valor por habitante</option></select></label>
 <label>Resultado eleitoral<select value={vencedor} onChange={e=>setVencedor(e.target.value)}><option value="todos">Todos</option><option value="13">Lula</option><option value="22">Flávio Bolsonaro</option><option value="outros">Outros vencedores</option></select></label>
 <label>UF<select value={uf} onChange={e=>setUf(e.target.value)}><option value="">Todas as UFs</option>{"AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split(" ").map(x=><option key={x}>{x}</option>)}</select></label></div><div className="metric-explain"><p><strong>Valor total:</strong> soma em reais das parcelas registradas para o município entre janeiro e agosto de 2026.</p><p><strong>Valor por habitante:</strong> essa soma dividida pela população estimada do IBGE em 2026. É um indicador de distribuição territorial dos valores, não quanto cada pessoa recebeu nem percentual de famílias beneficiárias.</p><p><strong>Parcelas:</strong> registros individuais de parcelas do benefício na base do Portal da Transparência, agrupados por competência. Não equivalem a famílias únicas e não comprovam que o valor tenha sido sacado.</p></div><p className="hint">Bolsa Família: competências janeiro–agosto de 2026. Eleição presidencial: primeiro turno de 2026.</p></section>
 <section className="ranking-section"><h2>Alcance do Bolsa Família na população</h2><p className="hint">Percentual de moradores em famílias beneficiárias, conforme o MDS em agosto de 2026, dividido pela população estimada pelo IBGE em 2026. Não é a porcentagem de titulares que recebem pagamentos. Os municípios sem dado ficam fora do ranking.</p>
 {erroCobertura&&<div className="notice" role="alert">{erroCobertura}</div>}
 <div className="compare-grids">{(["22","13"] as const).map(numero=><article className="compare-panel" key={numero}>
  <h3>Top 10 · {names[numero]}</h3><p className="sub">Municípios em que o candidato teve mais votos no primeiro turno; ordenados por cobertura populacional.</p>
  {!coberturas[numero]&&!erroCobertura&&<p className="hint">Carregando cobertura…</p>}
  {coberturas[numero]&&<ol className="compare-list">{coberturas[numero].resultados.map(x=><li key={x.codigo_ibge}>
   <div><Link href={"/?municipio="+x.codigo_ibge}>{x.nome} — {x.uf}</Link>
    <small>{x.pessoas?.toLocaleString("pt-BR")} pessoas em famílias beneficiárias</small></div>
   <strong>{x.cobertura_pct?.toLocaleString("pt-BR",{maximumFractionDigits:1})}%</strong>
  </li>)}</ol>}
 </article>)}</div>
 <p className="sources">MDS (pessoas em famílias beneficiárias), IBGE (população 2026), TSE (primeiro turno de 2026). Comparação descritiva entre municípios: não indica como as pessoas atendidas votaram.</p></section>
 <section className="ranking-section"><h2>Top 10 municípios</h2>{loading&&<p>Carregando…</p>}{erro&&<div role="alert" className="notice">{erro}</div>}{!loading&&dados&&!dados.disponivel&&<div className="notice">{dados.motivo}</div>}
 {!loading&&dados?.disponivel&&<div className="ranking-scroll"><table className="ranking-table"><thead><tr><th>#</th><th>Município</th><th>{metrica==="valor_total"?"Valor total":"Valor por habitante"}</th><th>Vencedor</th><th>Votação</th></tr></thead><tbody>{dados.resultados.map((m,i)=><tr key={m.codigo_ibge}><td>{i+1}</td><td><Link href={"/?municipio="+m.codigo_ibge}>{m.nome} — {m.uf}</Link></td><td>{metrica==="valor_total"?moeda(m.valor_centavos):m.centavos_por_habitante==null?"Indisponível":moeda(m.centavos_por_habitante)}</td><td>{names[m.vencedor]??"Candidato "+m.vencedor} ({m.vencedor})</td><td>{m.percentual_vencedor.toFixed(1).replace(".",",")}%</td></tr>)}</tbody></table>{!dados.resultados.length&&<p>Nenhum município encontrado para estes filtros.</p>}</div>}
 <p className="sources">O valor por habitante é um indicador financeiro, não o percentual de famílias beneficiárias. Os dados são agregados e não permitem estabelecer relações causais entre programas sociais e resultados eleitorais.</p></section><section className="ranking-section"><h2>Top 10 por habitante: Flávio Bolsonaro e Lula</h2><p className="hint">Municípios em que cada candidato foi o mais votado no primeiro turno de 2026, ordenados pelo valor acumulado do Bolsa Família por habitante entre janeiro e agosto de 2026. {uf?"UF: "+uf:"Brasil inteiro"}.</p>{erroComparativo&&<div className="notice" role="alert">{erroComparativo}</div>}<div className="compare-grids">{(["22","13"] as const).map(numero=><article className="compare-panel" key={numero}><h3>{names[numero]} ({numero})</h3><p className="sub">Municípios em que venceu</p>{!comparativos[numero]&&!erroComparativo&&<p className="hint">Carregando…</p>}{comparativos[numero]&&!comparativos[numero].disponivel&&<div className="notice">{comparativos[numero].motivo}</div>}{comparativos[numero]?.disponivel&&<ol className="compare-list">{comparativos[numero].resultados.map(m=><li key={m.codigo_ibge}><div><Link href={"/?municipio="+m.codigo_ibge}>{m.nome} — {m.uf}</Link><small>{m.percentual_vencedor.toFixed(1).replace(".",",")}% dos votos válidos listados</small></div><strong>{m.centavos_por_habitante===null?"Sem população":moeda(m.centavos_por_habitante)}</strong></li>)}</ol>}{comparativos[numero]?.disponivel&&comparativos[numero].resultados.length===0&&<p className="hint">Nenhum município com esse vencedor no recorte.</p>}</article>)}</div><p className="sources">Cada lista usa o mesmo período e indicador. O valor por habitante é acumulado nos oito meses e não representa o benefício mensal individual. Resultados eleitorais e benefícios são dados agregados, sem inferência causal.</p></section></main></>;
}
