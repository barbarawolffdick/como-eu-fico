import { DataBar } from "@/app/components/ui/data-bar";
import { Card, CardLink } from "@/app/components/ui/card";
import { ActionLink } from "@/app/components/ui/button";
import Link from "next/link";
import { redirect } from "next/navigation";
import { ArrowUpRight, MoveRight } from "lucide-react";
import CitySearch from "./components/city-search";
import { descobertasHome } from "@/lib/home";
export const dynamic = "force-dynamic";
const periodo = (mes: string) => `${mes.slice(4)}/${mes.slice(0, 4)}`;
export default async function Home({ searchParams }: {
    searchParams: Promise<{
        municipio?: string;
    }>;
}) {
    const { municipio } = await searchParams;
    if (municipio && /^\d{7}$/.test(municipio))
        redirect("/cidade/" + municipio);
    const { ranking, mudanca } = await descobertasHome();
    const escala = Math.max(1, ...mudanca?.regioes.map(r => Math.abs(r.percentual ?? 0)) ?? []);
    return <main id="conteudo" tabIndex={-1} className="home-page">
    <section className="home-hero"><div className="shell home-hero-grid">
      <div className="home-intro"><p className="eyebrow">Política pública. Vida real.</p>
        <h1>Como sua cidade vota.<br /><em>O que muda por aí.</em></h1>
        <p className="hero-description">Entenda a relação entre escolhas políticas e a vida na sua cidade. Acompanhe recursos, serviços e benefícios com dados para formar sua própria opinião.</p>
        <div className="home-search"><CitySearch /></div>
        <p className="hero-caption">Sua cidade é o ponto de partida. O Brasil é o contexto.</p>
      </div>
      <Card className="discovery-card" tone="muted"><div className="discovery-top"><span className="eyebrow">Uma pergunta para começar</span><span className="topic-pill">Bolsa Família</span></div>
        <h2>O alcance mudou.<br />Da mesma forma em todo o Brasil?</h2>
        <p>Variação do número de famílias beneficiárias por região.</p>
        {mudanca ? <><p className="discovery-period">{periodo(mudanca.inicio)} → {periodo(mudanca.fim)} · MDS</p>
          <ul className="region-changes">{mudanca.regioes.map(r => <li key={r.regiao}>
            <div><span>{r.regiao}</span><strong>{r.percentual == null ? "Indisponível" : `${r.percentual > 0 ? "+" : ""}${r.percentual.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`}</strong></div>
            <DataBar className="region-track" value={Math.abs(r.percentual ?? 0)} max={escala} />
            {r.municipios !== r.total && <small>{r.municipios} de {r.total} municípios com dados nos dois períodos</small>}
          </li>)}</ul>
          <p className="discovery-note">Comparação das somas nos municípios com dados nos dois períodos. Barras mostram a magnitude; o sinal indica aumento ou redução.</p></> : <p role="status">Os dados desta comparação estão indisponíveis no momento.</p>}
        <ActionLink href="/analises">Investigar os dados e o contexto eleitoral <ArrowUpRight size={18} aria-hidden="true"/></ActionLink>
      </Card>
    </div></section>
    <section className="shell home-explore" aria-labelledby="explore-title"><div className="section-heading"><div><p className="kicker">Olhe além do número</p><h2 id="explore-title">Cada cidade conta uma história.</h2></div><ActionLink href="/explorar">Explorar o Brasil →</ActionLink></div>
      <div className="home-content-grid"><Card className="home-ranking"><p className="kicker">Ranking · alcance na população</p><h3>Onde o Bolsa Família alcança mais moradores?</h3>
        <p className="sub">Percentual da população da cidade que vive em famílias que recebem o Bolsa Família. {ranking && `${periodo(ranking.periodo)} · MDS / IBGE 2026.`}</p>
        {ranking?.cidades.length ? <ol className="home-ranking-list">{ranking.cidades.map((city, index) => <li key={city.codigo_ibge}>
          <span className="rank-position">{String(index + 1).padStart(2, "0")}</span><Link href={`/cidade/${city.codigo_ibge}`}>{city.nome}<small>{city.uf}</small></Link><strong>{city.percentual.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%</strong>
        </li>)}</ol> : <p>O ranking está indisponível no momento.</p>}
        <p className="hint">Cinco maiores percentuais entre cidades com dado disponível. Conta todos os integrantes dessas famílias, inclusive crianças. O pagamento é feito ao titular da família.</p>
        <ActionLink href="/explorar">Explorar os rankings <MoveRight size={18} aria-hidden="true"/></ActionLink>
      </Card>
      <div className="journey-cards"><CardLink href="/comparar" tone="accent" className="journey-card"><span className="kicker">Duas cidades, lado a lado</span><h3>O que muda de uma cidade para outra?</h3><p>Compare voto, recursos de saúde e Bolsa Família, com períodos e unidades explícitos.</p><span className="action-link button--quiet">Comparar cidades <ArrowUpRight size={18} aria-hidden="true"/></span></CardLink>
        <CardLink href="/fontes" tone="warm" className="journey-card"><span className="kicker">Informação que você pode conferir</span><h3>De onde vêm os dados?</h3><p>Conheça as fontes, os períodos e o que cada indicador permite afirmar.</p><span className="action-link button--quiet">Entender os dados <ArrowUpRight size={18} aria-hidden="true"/></span></CardLink></div>
      </div>
      <p className="home-editorial-note">Voto, financiamento e condições de vida são dimensões distintas. Relações entre dados municipais ajudam a investigar perguntas; não demonstram, sozinhas, impacto da presidência ou a motivação de cada eleitor.</p>
    </section>
  </main>;
}
