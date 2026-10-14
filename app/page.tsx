"use client";

import { useEffect, useState } from "react";
import { Search, ArrowUpRight } from "lucide-react";
import Link from "next/link";

type Municipio = { codigo_ibge: string; nome: string | null; uf: string | null; populacao: number | null; ano_populacao: number | null };
type Bolsa = { mes_competencia: string; parcelas: number; valor_centavos: number };
type Voto = { candidato: string; votos: number };
type Detalhe = { municipio: Municipio; bolsa_familia: Bolsa[]; votos_presidenciais: Voto[]; eleitoral_disponivel: boolean };

const br = new Intl.NumberFormat("pt-BR");
const reais = (centavos: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(centavos / 100);
// Nomes de urna para Presidente, eleição 2026. Fonte: catálogo TSE 2026.
const nomesDeUrna: Record<string, string> = {
  "13": "Lula",
  "14": "Renan Santos",
  "16": "Hertz Dias",
  "21": "Edmilson Costa",
  "22": "Flávio Bolsonaro",
  "27": "Clariana Barão",
  "29": "Rui Costa Pimenta",
  "30": "Zema",
  "35": "Veterinário Wilson Grassi",
  "55": "Ronaldo Caiado",
  "70": "Escritor Augusto Cury",
  "80": "Samara",
};
const candidato = (n: string) => nomesDeUrna[n] ?? "Candidato " + n;
const competencia = (m: string) => m.slice(4, 6) + "/" + m.slice(0, 4);
async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    let message = "A consulta falhou.";
    try { const body = await response.json(); message = body.detail || message; } catch {}
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [choices, setChoices] = useState<Municipio[]>([]);
  const [detail, setDetail] = useState<Detalhe | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const code = new URLSearchParams(window.location.search).get("municipio");
    if (code && /^\d{7}$/.test(code)) void show(code);
    // Restore a direct-link lookup once, without resetting it during typing.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!query.trim()) { setChoices([]); return; }
    const controller = new AbortController();
    const timeout = setTimeout(async () => {
      try {
        const rows = await getJson<Municipio[]>("/api/municipios?q=" + encodeURIComponent(query.trim()));
        if (!controller.signal.aborted) { setChoices(rows); setError(""); }
      } catch (e) {
        if (!controller.signal.aborted) { setChoices([]); setError((e as Error).message); }
      }
    }, 200);
    return () => { clearTimeout(timeout); controller.abort(); };
  }, [query]);

  async function show(code: string) {
    setLoading(true); setError("");
    try {
      const data = await getJson<Detalhe>("/api/municipios/" + code);
      setDetail(data); setChoices([]); setQuery("");
      window.history.replaceState(null, "", "?municipio=" + code);
    } catch (e) { setError((e as Error).message); }
    finally { setLoading(false); }
  }

  const serie = detail?.bolsa_familia ?? [];
  const ultimo = serie.at(-1);
  const maior = Math.max(1, ...serie.map(x => x.valor_centavos));
  const votos = detail?.votos_presidenciais ?? [];
  const totalVotos = votos.reduce((s, v) => s + v.votos, 0);

  return <>
    <header className="masthead"><div className="shell">
      <div className="topbar"><span className="brand">Como Eu Fico</span><Link href="/explorar" className="tag">Explorar o Brasil →</Link></div>
      <div className="hero"><div className="eyebrow">O Brasil, município por município</div>
        <h1>O que acontece na sua cidade?</h1>
        <p>Consulte dados públicos sobre o Bolsa Família, a eleição presidencial de 2026 e o território onde você vive. Sem presumir relações de causa e efeito.</p>
      </div>
    </div></header>
    <main className="shell main">
      <div className="searchpanel">
        <label htmlFor="busca" className="inputlabel">Encontre seu município</label>
        <div className="searchfield"><Search size={19} aria-hidden="true" />
          <input id="busca" autoComplete="off" placeholder="Nome do município ou código IBGE" value={query} onChange={e => setQuery(e.target.value)} />
        </div>
        {choices.length > 0 && <div className="choices" role="listbox" aria-label="Resultados da busca">
          {choices.map(m => <button className="choice" role="option" aria-selected="false" key={m.codigo_ibge} onClick={() => void show(m.codigo_ibge)}>
            <span>{m.nome ?? "Município sem nome"} — {m.uf ?? "UF não informada"}</span><small>IBGE {m.codigo_ibge}</small>
          </button>)}
        </div>}
        <p className="hint">Busca por nome ou código IBGE. A consulta usa as fontes municipais integradas, sem inventar dados ausentes.</p>
      </div>
      {error && <div className="notice" role="alert">{error}</div>}
      {loading && <div className="hint" role="status">Consultando dados do município…</div>}
      {detail ? <div className="results">
        <div className="resulttop"><div><span className="kicker">Consulta municipal · IBGE {detail.municipio.codigo_ibge}</span>
          <h2>{detail.municipio.nome ?? "Município"} — {detail.municipio.uf ?? "UF"}</h2>
          <div className="population">{detail.municipio.populacao != null ? "População estimada: " + br.format(detail.municipio.populacao) + " habitantes · IBGE " + detail.municipio.ano_populacao : "População IBGE ainda não disponível nesta base"}</div>
        </div><ArrowUpRight size={24} aria-hidden="true" /></div>
        <div className="cards">
          <article className="card"><h3>Bolsa Família</h3>
            {ultimo ? <><span className="kicker">Última competência: {competencia(ultimo.mes_competencia)}</span>
              <div className="big" style={{marginTop:10}}>{reais(ultimo.valor_centavos)}</div>
              <p className="sub">{br.format(ultimo.parcelas)} parcelas registradas nessa competência</p>
              <div className="chart" role="img" aria-label={"Evolução mensal dos valores registrados do Bolsa Família, de " + competencia(serie[0].mes_competencia) + " até " + competencia(ultimo.mes_competencia)}>
                {serie.map(p => <div key={p.mes_competencia} className="bar" title={competencia(p.mes_competencia) + ": " + reais(p.valor_centavos)} style={{height:(100 * p.valor_centavos / maior) + "%"}} />)}
              </div><div className="chartlabels"><span>{competencia(serie[0].mes_competencia)}</span><span>{competencia(ultimo.mes_competencia)}</span></div>
              <p className="sub">Acumulado das {serie.length} competências: {reais(serie.reduce((s,p) => s+p.valor_centavos,0))}</p>
            </> : <p className="sub">Sem registros mensais disponíveis. Ausência não significa zero.</p>}
            <div className="footnote">Fonte: CGU / Portal da Transparência. Valores agregados por competência. Parcelas não equivalem a famílias únicas nem comprovam saque.</div>
          </article>
          <article className="card"><h3>Votação presidencial · 2026</h3>
            {votos.length && totalVotos > 0 ? <>{votos.map(v => {
              const p = 100 * v.votos / totalVotos;
              return <div className="vote" key={v.candidato}><div className="voterow"><span>{candidato(v.candidato)} ({v.candidato})</span><strong>{p.toFixed(1).replace(".", ",")}%</strong></div>
                <div className="track"><div className="fill" style={{width:p+"%"}} /></div><p className="sub">{br.format(v.votos)} votos</p></div>;
            })}<p className="sub">Total de votos dos candidatos listados: {br.format(totalVotos)}</p></> :
              <p className="sub">Dados eleitorais indisponíveis. Ausência não significa zero.</p>}
            <div className="footnote">Fonte: TSE. Primeiro turno da eleição presidencial de 2026. Dados agregados por município não demonstram comportamento individual ou causalidade com políticas públicas.</div>
          </article>
        </div>
        <div className="sources">Fontes: TSE (votação), CGU (Bolsa Família) e IBGE (território e população, quando disponível). Os períodos e conceitos das fontes são independentes.</div>
      </div> : <div className="empty"><strong>Comece pelo seu município.</strong><span>Escolha uma cidade para conhecer os indicadores disponíveis.</span></div>}
    </main>
    <footer className="footer"><div className="shell">Como Eu Fico · Consulta descritiva de dados públicos. Nenhuma associação apresentada implica causalidade.</div></footer>
  </>;
}
