"use client";

import AlcanceBolsa from "./alcance-bolsa";
import VotosMunicipais from "./votos-municipais";
import { mediaPorBeneficiario, type BeneficiariosCidade } from "@/lib/bolsa-familia";
import { Feedback } from "@/app/components/ui/feedback";
import { Button, ActionLink } from "@/app/components/ui/button";
import { Card, CardLink } from "@/app/components/ui/card";
import Link from "next/link";
import { ArrowUpRight, MapPin } from "lucide-react";
import CitySearch from "./city-search";
import CitySections from "./city-sections";
import SaudeMunicipal from "./saude-municipal";
import DinheiroFederal from "./dinheiro-federal";
import { useResource } from "../hooks/use-resource";
import type { RespostaSaude } from "@/lib/saude";
import { nomeCandidato as candidato } from "@/lib/eleicoes";
type Municipio = {
    codigo_ibge: string;
    nome: string | null;
    uf: string | null;
    populacao: number | null;
    ano_populacao: number | null;
};
type Bolsa = {
    mes_competencia: string;
    parcelas: number;
    valor_centavos: number;
};
type Voto = {
    candidato: string;
    votos: number;
};
type Detalhe = {
    municipio: Municipio;
    bolsa_familia: Bolsa[];
    votos_presidenciais: Voto[];
    eleitoral_disponivel: boolean;
};
type Cobertura = {
    periodo: string;
    fonte: string;
    disponivel: boolean;
    municipio: {
        pessoas: number | null;
        populacao: number;
        cobertura_pct: number | null;
    };
};
const br = new Intl.NumberFormat("pt-BR");
const reais = (centavos: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(centavos / 100);
const competencia = (m: string) => m.slice(4, 6) + "/" + m.slice(0, 4);
const percentual = (n: number) => n.toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + "%";
export default function CityPage({ codigo }: {
    codigo: string;
}) {
    const city = useResource<Detalhe>("/api/municipios/" + codigo, "Não foi possível consultar esta cidade. Confira o código ou tente novamente.");
    const coverage = useResource<Cobertura>("/api/cobertura?municipio=" + codigo, "Não foi possível carregar a cobertura. Tente novamente.");
    const health = useResource<RespostaSaude>("/api/saude/" + codigo, "Não foi possível carregar os indicadores de saúde. Tente novamente.");
    const beneficiaries = useResource<BeneficiariosCidade>("/api/beneficiarios/" + codigo, "Não foi possível consultar as contagens de pessoas e famílias.");
    const detail = city.data;
    const cobertura = coverage.data;
    const erroCobertura = coverage.error;
    const serie = [...(detail?.bolsa_familia ?? [])].sort((a, b) => a.mes_competencia.localeCompare(b.mes_competencia));
    const ultimo = serie.at(-1);
    const denominadores = ultimo ? beneficiaries.data?.periodos[ultimo.mes_competencia] : null;
    const mediaPessoa = mediaPorBeneficiario(ultimo?.valor_centavos, denominadores?.pessoas);
    const mediaFamilia = mediaPorBeneficiario(ultimo?.valor_centavos, denominadores?.familias);
    const moedaMedia = (valor: number) => (valor / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
    const maior = Math.max(1, ...serie.map(x => x.valor_centavos));
    const votos = detail?.eleitoral_disponivel ? [...detail.votos_presidenciais].sort((a, b) => b.votos - a.votos || a.candidato.localeCompare(b.candidato)) : [];
    const totalVotos = votos.reduce((s, v) => s + v.votos, 0);
    const lider = votos[0];
    const empate = !!lider && votos.filter(v => v.votos === lider.votos).length > 1;
    return <main id="conteudo" tabIndex={-1} className="city-page">
    <div className="shell"><div className="city-breadcrumb"><Link href="/">Início</Link><span aria-hidden="true">/</span><span>Minha cidade</span></div>
      {city.error ? <Feedback kind="error"><h1>Não foi possível abrir a cidade</h1><p>{city.error}</p><Button onClick={city.retry}>Tentar novamente</Button><p><Link href="/">Buscar outra cidade →</Link></p></Feedback> : !detail ? <Feedback className="city-loading" kind="loading">Consultando dados do município…</Feedback> : <>
        <header className="city-heading"><div><p className="kicker"><MapPin size={14} aria-hidden="true"/> Sua cidade em perspectiva</p><h1>{detail.municipio.nome ?? "Município"} — {detail.municipio.uf ?? "UF"}</h1>
          <p className="population">{detail.municipio.populacao != null ? "População estimada: " + br.format(detail.municipio.populacao) + " habitantes · IBGE " + detail.municipio.ano_populacao : "População IBGE ainda não disponível nesta base"}</p>
          <p className="hint">{lider && totalVotos > 0 && !empate ? `${candidato(lider.candidato)} teve ${percentual(100 * lider.votos / totalVotos)} dos votos no 1º turno de 2026 · ` : ""}Código IBGE {codigo} · Cada indicador tem seu próprio período de referência.</p><ActionLink href={"/comparar?a=" + codigo} className="city-compare-action">Comparar com outra cidade <ArrowUpRight size={17} aria-hidden="true"/></ActionLink></div><CitySearch compact/></header>
        <CitySections />
        <DinheiroFederal key={codigo} codigo={codigo} votos={detail.eleitoral_disponivel ? detail.votos_presidenciais : []} />
        <section id="sustenta" aria-labelledby="sustenta-title" className="federal-section"><div className="section-heading"><div><p className="kicker">6 · O que sustenta</p><h2 id="sustenta-title">O que esse dinheiro sustenta na cidade?</h2></div></div>
          <div className="cards">
            <CardLink href="#titulo-saude"><h3>Saúde</h3><p className="sub">Repasses, unidades, leitos, equipamentos e equipes do SUS na cidade, cada um com seu período.</p><span className="action-link">Ver saúde em detalhe <ArrowUpRight size={17} aria-hidden="true"/></span></CardLink>
            <CardLink href="#dados-bolsa"><h3>Bolsa Família</h3><p className="sub">{cobertura?.disponivel && cobertura.municipio.cobertura_pct != null ? `${percentual(cobertura.municipio.cobertura_pct)} dos moradores vivem em famílias beneficiárias (${competencia(cobertura.periodo)}).` : "Alcance na população, valor por pessoa e valores mês a mês."}</p><span className="action-link">Ver Bolsa Família <ArrowUpRight size={17} aria-hidden="true"/></span></CardLink>
          </div>
        </section>
        <SaudeMunicipal resposta={health.data} erro={health.error} retry={health.retry}/>
        <section id="dados-bolsa" className="ranking-section" aria-labelledby="bolsa-title"><div className="section-heading"><div><p className="kicker">Renda e proteção social</p><h2 id="bolsa-title">Bolsa Família na sua cidade</h2><p className="hint">Alcance na população e valores registrados são medidas diferentes, com períodos próprios.</p></div></div><div className="cards benefit-cards">
          <Card><h3>Moradores em famílias que recebem Bolsa Família</h3>
            {erroCobertura ? <Feedback kind="error"><p>{erroCobertura}</p><Button onClick={() => coverage.retry()}>Tentar novamente</Button></Feedback> : !cobertura ? <Feedback kind="loading">Carregando cobertura…</Feedback> : cobertura.disponivel && cobertura.municipio.cobertura_pct != null ?
                <><span className="kicker">Moradores em famílias beneficiárias · {competencia(cobertura.periodo)}</span>
                <div className="big">{cobertura.municipio.cobertura_pct.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%</div>
                <p className="coverage-unit">da população da cidade</p><AlcanceBolsa pessoas={cobertura.municipio.pessoas!} populacao={cobertura.municipio.populacao} percentual={cobertura.municipio.cobertura_pct} />
              </> :
                <p className="sub">Cobertura populacional ainda não disponível para este município. Ausência não é zero.</p>}
            <div className="footnote">Fonte: MDS / VIS DATA 3. População: IBGE 2026. É a proporção de moradores que integram famílias beneficiárias, não de titulares que recebem pagamentos. {cobertura?.fonte && <a href={cobertura.fonte} target="_blank" rel="noreferrer">Ver fonte.</a>}</div>
          </Card>
          <Card data-testid="media-bolsa-cidade"><h3>Valor por pessoa da família</h3>
            <p className="kicker">{ultimo ? competencia(ultimo.mes_competencia) : "Competência indisponível"} · média calculada</p>
            <div className="big">{!beneficiaries.data && !beneficiaries.error ? "Carregando…" : mediaPessoa == null ? "Indisponível" : moedaMedia(mediaPessoa)}</div>
            <p className="sub">Valor do Bolsa Família registrado na cidade dividido somente pelos moradores de famílias beneficiárias no mesmo mês.</p>
            {denominadores?.pessoas != null && <p className="hint">Base: {br.format(denominadores.pessoas)} pessoas em famílias beneficiárias.</p>}
            {mediaFamilia != null && <p className="sub"><strong>{moedaMedia(mediaFamilia)} por família</strong>, considerando {br.format(denominadores!.familias!)} famílias no mesmo mês.</p>}
            {denominadores?.pessoas != null && denominadores.familias != null && denominadores.familias > 0 && <p className="hint">Média de {(denominadores.pessoas / denominadores.familias).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} pessoas por família beneficiária, calculada com as contagens do mesmo mês.</p>}
            {mediaPessoa == null && beneficiaries.data && <p className="hint">Sem contagem de pessoas validada para o mês do valor. Não usamos a população inteira nem pessoas de outro mês.</p>}
            {beneficiaries.error && <Feedback kind="error"><p>{beneficiaries.error}</p><Button onClick={beneficiaries.retry}>Tentar novamente</Button></Feedback>}
            <div className="footnote">Fontes: valores CGU e pessoas/famílias MDS, na competência indicada. É uma divisão dos totais municipais; não é um pagamento separado para cada integrante nem o valor exato recebido por cada família. Os registros não comprovam saque.</div>
          </Card>
          <Card className="benefit-history"><h3>Valores registrados ao longo do tempo</h3>
            {ultimo ? <><span className="kicker">Última competência: {competencia(ultimo.mes_competencia)}</span>
              <div className="big money-value">{reais(ultimo.valor_centavos)}</div>
              <p className="sub">{br.format(ultimo.parcelas)} registros de parcelas do benefício nessa competência</p>
              <div className="chart" role="img" aria-label={"Evolução mensal dos valores registrados do Bolsa Família, de " + competencia(serie[0].mes_competencia) + " até " + competencia(ultimo.mes_competencia)}>
                {serie.map(p => <div key={p.mes_competencia} className="bar" title={competencia(p.mes_competencia) + ": " + reais(p.valor_centavos)} style={{ height: (100 * p.valor_centavos / maior) + "%" }}/>)}
              </div><div className="chartlabels"><span>{competencia(serie[0].mes_competencia)}</span><span>{competencia(ultimo.mes_competencia)}</span></div>
              <p className="sub">Acumulado das {serie.length} competências: {reais(serie.reduce((s, p) => s + p.valor_centavos, 0))}</p>
            </> : <p className="sub">Sem registros mensais disponíveis. Ausência não significa zero.</p>}
            <div className="footnote">Fonte: CGU / Portal da Transparência. Valores agregados por competência. Parcelas são registros de parcelas do benefício na base CGU, não famílias únicas. Os registros não comprovam saque.</div>
          </Card>
        </div></section>
        <Card as="section" tone="muted" id="fontes-cidade" className="city-sources" aria-labelledby="fontes-title"><div><p className="kicker">Confira a informação</p><h2 id="fontes-title">Os dados têm origem. E limites.</h2><p>Fontes: TSE (votação), INSS e Ministério da Previdência (benefícios), Tesouro Nacional (FPM), CGU e MDS (Bolsa Família), IBGE (território, população e PIB) e Ministério da Saúde (indicadores do SUS). Os períodos e conceitos das fontes são independentes.</p></div><ActionLink href="/fontes">Fontes e metodologia <ArrowUpRight size={18} aria-hidden="true"/></ActionLink></Card>
      </>}
    </div>
  </main>;
}
