"use client";

import { Card } from "@/app/components/ui/card";
import { Feedback } from "@/app/components/ui/feedback";
import { Button } from "@/app/components/ui/button";
import VotosMunicipais from "./votos-municipais";
import { BarraVotos, Colunas, Dispersao, EnxameCidades, Fluxo, Legenda, Waffle, curto, numero, type FolhaFluxo, type Referencia } from "./graficos";
import { nomeCandidato } from "@/lib/eleicoes";
import {
  FLUXOS, NOMES_FLUXO, PARA_PESSOAS, PARA_PREFEITURA,
  type Comparacao, type DinheiroFederalCidade, type Fluxo as TipoFluxo, type RespostaRegioes,
} from "@/lib/dinheiro-federal";

const NOME_CURTO: Record<TipoFluxo, string> = { inss: "INSS", bolsa_familia: "Bolsa Família", fpm: "FPM", sus: "SUS" };
const lista = (itens: string[]) => itens.length < 2 ? itens.join("") : itens.slice(0, -1).join(", ") + " e " + itens.at(-1);
const percentual = (v: number, casas = 1) => numero(v, casas) + "%";
export function reaisCompacto(centavos: number) {
  const reais = centavos / 100;
  if (Math.abs(reais) >= 1e9) return `R$ ${numero(reais / 1e9, 2)} ${Math.abs(reais) < 2e9 ? "bilhão" : "bilhões"}`;
  if (Math.abs(reais) >= 1e6) return `R$ ${numero(reais / 1e6, Math.abs(reais) < 1e7 ? 1 : 0)} milhões`;
  return `R$ ${numero(reais, 0)}`;
}

export function SectionHeading({ id, kicker, title }: { id: string; kicker: string; title: string }) {
  return <div className="section-heading"><div><p className="kicker">{kicker}</p><h2 id={id}>{title}</h2></div></div>;
}

type Props = { ano: number; pibEstimado: boolean; pibAnoFonte: number; cidade: DinheiroFederalCidade };

/** Seções 1 a 5: quanto chega, para quem, como mudou, comparação e voto. */
export default function DinheiroFederal({ ano, pibEstimado, pibAnoFonte, cidade, votos, regioes }: Props & {
  votos: { candidato: string; votos: number }[];
  regioes: { data: RespostaRegioes | null; error: string; retry: () => void };
}) {
  return <>
    <QuantoChega ano={ano} pibEstimado={pibEstimado} pibAnoFonte={pibAnoFonte} cidade={cidade} />
    <ParaQuem ano={ano} cidade={cidade} />
    <ComoMudou cidade={cidade} />
    <ComparaRegiao ano={ano} pibEstimado={pibEstimado} cidade={cidade} regioes={regioes} />
    <VotoERelacao votos={votos} regioes={regioes} regiaoId={cidade.regiao_imediata.id} regiaoNome={cidade.regiao_imediata.nome} />
  </>;
}

function QuantoChega({ ano, pibEstimado, pibAnoFonte, cidade }: Props) {
  const disponiveis = FLUXOS.filter(f => cidade.fluxos[f] != null);
  const faltam = FLUXOS.filter(f => cidade.fluxos[f] == null);
  const soma = disponiveis.reduce((s, f) => s + (cidade.fluxos[f] ?? 0), 0);
  const share = cidade.pib_centavos ? 100 * soma / cidade.pib_centavos : null;
  const quadrados = share === null ? 0 : Math.min(100, Math.round(share));
  return <section id="quanto" aria-labelledby="quanto-title" className="federal-section">
    <SectionHeading id="quanto-title" kicker="1 · Quanto chega" title={`Quanto dinheiro federal chegou à cidade em ${ano}?`} />
    <Card className="federal-hero">
      {disponiveis.length ? <>
        <div className="federal-hero-top">
          <p className="big federal-big">{reaisCompacto(soma)}</p>
          <p className="federal-lead">chegaram a {cidade.municipio.nome} em {ano} em aposentadorias, Bolsa Família e repasses à prefeitura. São cerca de <b>{reaisCompacto(soma / 365)} por dia</b>.</p>
          {faltam.length > 0 && <p className="hint">{lista(faltam.map(f => NOME_CURTO[f]))} não {faltam.length > 1 ? "têm" : "tem"} dado para {ano} nesta cidade; o total considera {lista(disponiveis.map(f => NOME_CURTO[f]))}.</p>}
        </div>
        {share !== null ? <div className="federal-hero-compare">
          <div className="federal-hero-text">
            <p className="federal-sentence">De cada <b>R$ 100</b> produzidos na cidade, <b>R$ {numero(share, 0)}</b> {share >= 1.5 ? "vieram" : "veio"} do governo federal{pibEstimado ? " (estimativa)" : ""}.</p>
            <p className="hint">A economia da cidade produziu cerca de {reaisCompacto(cidade.pib_centavos!)} em {ano}{pibEstimado ? " (estimativa)" : ""}. Cada quadrado é R$ 1 de cada R$ 100.{share > 100 ? " O dinheiro federal supera a produção local; todos os quadrados ficam preenchidos." : ""}</p>
          </div>
          <figure className="federal-hero-fig">
            <Waffle partes={[{ n: quadrados, classe: "is-c1" }]} rotulo={`${quadrados} de 100 quadrados representam o dinheiro federal`} />
            <figcaption><Legenda itens={[{ classe: "viz-sw-1", texto: "Dinheiro federal" }, { classe: "viz-sw-0", texto: "Restante da economia" }]} /></figcaption>
          </figure>
        </div> : <p className="hint">Sem PIB municipal para comparar com a economia da cidade. {cidade.ausencias.pib ?? ""}</p>}
      </> : <Feedback kind="empty">Não há dados de dinheiro federal para esta cidade em {ano}. Ausência não é zero.</Feedback>}
    </Card>
    <p className="footnote">{pibEstimado
      ? `O PIB mais recente das cidades é de ${pibAnoFonte}. Para comparar com o dinheiro de ${ano}, aplicamos ao PIB da cidade o crescimento da economia do país no período; o resultado é uma estimativa. `
      : ""}Soma ilustrativa de vias com naturezas diferentes: benefícios pagos a pessoas e repasses à prefeitura. Valores sem desconto da inflação.</p>
  </section>;
}

function ParaQuem({ ano, cidade }: { ano: number; cidade: DinheiroFederalCidade }) {
  const F = cidade.fluxos, d = cidade.inss_detalhe;
  const soma = (fs: TipoFluxo[]) => fs.every(f => F[f] != null) ? fs.reduce((s, f) => s + F[f]!, 0) : null;
  const pessoas = soma(PARA_PESSOAS), prefeitura = soma(PARA_PREFEITURA);
  const total = pessoas != null && prefeitura != null ? pessoas + prefeitura : null;
  const folhas: FolhaFluxo[] = [
    ...(d ? [
      { nome: "Aposentadorias", valor: d.aposentadorias, grupo: "pessoas" as const },
      { nome: "BPC e assistenciais", valor: d.assistencial_e_legislacao_especifica, grupo: "pessoas" as const },
      { nome: "Pensões por morte", valor: d.pensoes_por_morte, grupo: "pessoas" as const },
      { nome: "Auxílios e outros", valor: d.auxilios + d.outros_previdenciarios, grupo: "pessoas" as const },
    ] : F.inss != null ? [{ nome: "INSS", valor: F.inss, grupo: "pessoas" as const }] : []),
    ...(F.bolsa_familia != null ? [{ nome: "Bolsa Família", valor: F.bolsa_familia, grupo: "pessoas" as const }] : []),
    ...(F.fpm != null ? [{ nome: "FPM, uso livre", valor: F.fpm, grupo: "prefeitura" as const }] : []),
    ...(F.sus != null ? [{ nome: "SUS, saúde", valor: F.sus, grupo: "prefeitura" as const }] : []),
  ].filter(f => f.valor > 0);
  const regiaoInss = cidade.comparacoes[1]?.percentual_do_pib.inss;
  const por100 = cidade.inss_beneficios_por_100_habitantes, q = cidade.inss_quantidade_dezembro;
  const faltam = FLUXOS.filter(f => F[f] == null);
  return <section id="para-quem" aria-labelledby="para-quem-title" className="federal-section">
    <SectionHeading id="para-quem-title" kicker="2 · Para quem" title="Para onde vai esse dinheiro?" />
    {total ? <p className="federal-lead"><b>{numero(Math.round(100 * pessoas! / total))} de cada 100 reais</b> chegam diretamente às pessoas, como aposentadorias, benefícios e Bolsa Família. O restante vai para a prefeitura manter serviços.</p> : null}
    <Card className="federal-chart">
      {folhas.length ? <Fluxo folhas={folhas} rotulos={{ pessoas: "Pessoas", prefeitura: "Prefeitura" }} /> : <Feedback kind="empty">Sem dados de dinheiro federal para desenhar o fluxo. Ausência não é zero.</Feedback>}
      {faltam.length > 0 && <p className="hint">Sem dado em {ano}: {lista(faltam.map(f => `${NOME_CURTO[f]} (${(cidade.ausencias[f] ?? "indisponível").replace(/\.$/, "")})`))}.</p>}
      {cidade.inss_orgao_pagador_atipico && por100 !== null
        ? <p className="federal-callout" role="note">Esta cidade tem {numero(por100, 1)} benefícios do INSS por 100 habitantes, {por100 < 5 ? "muito abaixo" : "muito acima"} do comum. Os benefícios são contados na cidade da agência que paga: {por100 < 5 ? "parte dos moradores recebe em cidades vizinhas" : "a cidade paga benefícios de moradores de cidades vizinhas"}.{regiaoInss != null ? ` Na região de ${cidade.regiao_imediata.nome}, o INSS equivale a ${percentual(regiaoInss)} da economia.` : ""}</p>
        : <p className="hint">Aposentadorias e benefícios do INSS são contados na cidade onde são pagos, que nem sempre é a cidade onde o beneficiário mora.{q ? ` Em dezembro de ${ano}, foram ${numero(q.total)} benefícios pagos pela cidade.` : ""}</p>}
      <details className="federal-details"><summary>Ver tabela</summary>
        <div className="table-scroll"><table className="data-table">
          <caption className="sr-only">Dinheiro federal por destino em {ano}</caption>
          <thead><tr><th scope="col">Destino</th><th scope="col">Valor no ano</th><th scope="col">Parte do total</th></tr></thead>
          <tbody>{folhas.map(f => <tr key={f.nome}><th scope="row">{f.nome} <small>({f.grupo === "pessoas" ? "pessoas" : "prefeitura"})</small></th><td>{reaisCompacto(f.valor)}</td>
            <td>{percentual(100 * f.valor / folhas.reduce((s, x) => s + x.valor, 0))}</td></tr>)}</tbody>
        </table></div>
        <p className="hint">FPM: parte dos impostos federais que a Constituição destina aos municípios, de uso livre. SUS: atenção primária, hospitais, vigilância e gestão. Não inclui convênios, obras e outros repasses ainda não integrados ao projeto.</p>
      </details>
    </Card>
  </section>;
}

function ComoMudou({ cidade }: { cidade: DinheiroFederalCidade }) {
  const serie = cidade.serie;
  if (!serie) return null;
  const anos = serie.anos;
  const pontos = (f: "inss" | "fpm") => anos.filter(a => serie[f][a].real != null);
  const inssAnos = pontos("inss"), fpmAnos = pontos("fpm");
  const variacao = (f: "inss" | "fpm", campo: "real" | "nominal", de: string, ate: string) => 100 * (serie[f][ate][campo]! / serie[f][de][campo]! - 1);
  // Variação real: abaixo de 2% em módulo é tratada como estabilidade, para não destacar oscilações pequenas.
  const frase = (sujeito: string, v: number, de: string, ate: string) => Math.abs(v) < 2
    ? `Descontada a inflação, ${sujeito} ficou estável de ${de} a ${ate} (${v >= 0 ? "+" : "−"}${percentual(Math.abs(v), 0)}).`
    : `Descontada a inflação, ${sujeito} ${v > 0 ? "cresceu" : "caiu"} ${percentual(Math.abs(v), 0)} de ${de} a ${ate}.`;
  const mi = (c: number | null) => c == null ? "s/d" : numero(c / 1e8);
  return <section id="mudou" aria-labelledby="mudou-title" className="federal-section">
    <SectionHeading id="mudou-title" kicker="3 · Como mudou" title="Como esse dinheiro mudou nos últimos anos?" />
    {inssAnos.length >= 2 && <p className="federal-lead">{frase("o INSS pago na cidade", variacao("inss", "real", inssAnos[0], inssAnos.at(-1)!), inssAnos[0], inssAnos.at(-1)!)} Sem descontar a inflação, a variação parece de {percentual(variacao("inss", "nominal", inssAnos[0], inssAnos.at(-1)!), 0)}.{fpmAnos.length >= 2 ? " " + frase("o FPM", variacao("fpm", "real", fpmAnos[0], fpmAnos.at(-1)!), fpmAnos[0], fpmAnos.at(-1)!) : ""}</p>}
    <Card className="federal-chart">
      <Legenda itens={[{ classe: "viz-sw-1", texto: "INSS" }, { classe: "viz-sw-3", texto: "FPM" }]} />
      <Colunas dados={{ anos, base: serie.base_inflacao, series: [
        { id: "inss", nome: "INSS", classe: "viz-c1", valores: anos.map(a => serie.inss[a].real) },
        { id: "fpm", nome: "FPM", classe: "viz-c3", valores: anos.map(a => serie.fpm[a].real) },
      ] }} />
      <p className="hint">R$ milhões por ano, em reais de {serie.base_inflacao} (IPCA).</p>
      <details className="federal-details"><summary>Ver tabela</summary>
        <div className="table-scroll"><table className="data-table">
          <caption className="sr-only">INSS e FPM por ano, em milhões de reais de {serie.base_inflacao}</caption>
          <thead><tr><th scope="col">Ano</th><th scope="col">INSS</th><th scope="col">FPM</th></tr></thead>
          <tbody>{anos.map(a => <tr key={a}><th scope="row">{a}</th><td>{mi(serie.inss[a].real)}</td><td>{mi(serie.fpm[a].real)}</td></tr>)}</tbody>
        </table></div>
      </details>
      <p className="footnote">Valores de cada ano convertidos para reais de {serie.base_inflacao} pelo IPCA médio do ano. “s/d”: o dado da fonte está incompleto nesse ano (meses ausentes, publicados pela metade ou com nomes de municípios ainda sem correspondência revisada), por isso não mostramos o total. Bolsa Família e SUS ganham suas séries quando os anos anteriores forem integrados.</p>
    </Card>
  </section>;
}

function ComparaRegiao({ ano, pibEstimado, cidade, regioes }: { ano: number; pibEstimado: boolean; cidade: DinheiroFederalCidade; regioes: { data: RespostaRegioes | null; error: string; retry: () => void } }) {
  const linhas = cidade.comparacoes;
  const [propria, regiao] = linhas;
  const vizinhos = linhas.find(l => l.nome.startsWith("As ") && l.detalhe.startsWith("sem "));
  const estado = linhas.at(-3), brasil = linhas.at(-1);
  const enxame = regioes.data?.enxame;
  const acima = enxame && propria.total !== null ? enxame.pontos.filter(p => p[4] > propria.total!).length : null;
  const referencias: Referencia[] = [brasil, estado, regiao, vizinhos].filter((l): l is Comparacao => !!l && l.total !== null)
    .map(l => ({ nome: l === regiao ? "Região" : l === vizinhos ? "Vizinhas" : l.nome, valor: l.total! }));
  return <section id="compara" aria-labelledby="compara-title" className="federal-section">
    <SectionHeading id="compara-title" kicker="4 · Comparação" title="O dinheiro federal pesa mais ou menos aqui do que no resto do país?" />
    {propria.total !== null && acima !== null && enxame ? <p className="federal-lead">Em <b>{percentual(100 * acima / enxame.pontos.length, 0)}</b> das cidades brasileiras, o dinheiro federal pesa mais do que em {cidade.municipio.nome} ({percentual(propria.total, 0)} da economia).{vizinhos?.total != null ? ` Nas ${vizinhos.nome.slice(3)}, chega a ${percentual(vizinhos.total, 0)}.` : ""}</p>
      : propria.total === null ? <p className="federal-lead">A comparação usa os quatro tipos de dinheiro; {cidade.municipio.nome} não tem todos para {ano}. A tabela abaixo mostra o que existe.</p> : null}
    <Card className="federal-chart">
      {regioes.error ? <Feedback kind="error" action={<Button onClick={regioes.retry}>Tentar novamente</Button>}>{regioes.error}</Feedback>
        : !enxame ? <Feedback kind="loading">Carregando as cidades do país…</Feedback>
        : <>
          <Legenda itens={[{ classe: "viz-sw-1", texto: "Cidades do Nordeste", ponto: true }, { classe: "viz-sw-2", texto: "Demais cidades", ponto: true }, { classe: "viz-sw-ink", texto: cidade.municipio.nome, ponto: true }]} />
          <EnxameCidades enxame={enxame} codigo={cidade.municipio.codigo_ibge} nomeCidade={cidade.municipio.nome} referencias={referencias} />
          <p className="hint">Cada ponto é uma cidade. Quanto mais à direita, maior a parte da economia local que vem do dinheiro federal. Linhas tracejadas: {lista(referencias.map(r => r.nome === "Região" ? `região de ${cidade.regiao_imediata.nome}` : r.nome === "Vizinhas" ? "cidades vizinhas" : r.nome))}. Passe o mouse ou toque para ver o nome de uma cidade.</p>
        </>}
      <details className="federal-details"><summary>Ver por tipo de dinheiro</summary>
        <div className="table-scroll"><table className="data-table data-table--wide">
          <caption className="sr-only">Dinheiro federal como percentual da economia em {ano}, por tipo e território</caption>
          <thead><tr><th scope="col">Território</th>{FLUXOS.map(f => <th scope="col" key={f}>{NOMES_FLUXO[f]}</th>)}<th scope="col">Total</th></tr></thead>
          <tbody>{linhas.map(l => <tr key={l.nome}><th scope="row">{l.nome}{l.detalhe && <small> · {l.detalhe}</small>}</th>
            {FLUXOS.map(f => <td key={f}>{l.percentual_do_pib[f] != null ? percentual(l.percentual_do_pib[f]!) : "—"}</td>)}
            <td>{l.total != null ? percentual(l.total) : "—"}</td></tr>)}</tbody>
        </table></div>
        <p className="hint">Percentual da economia{pibEstimado ? " estimada" : ""} de {ano}. “—”: sem dado para este território. Como o INSS é contado na cidade onde é pago, a região inteira é a comparação mais justa entre lugares.</p>
      </details>
    </Card>
  </section>;
}

function VotoERelacao({ votos, regioes, regiaoId, regiaoNome }: { votos: { candidato: string; votos: number }[]; regioes: { data: RespostaRegioes | null; error: string; retry: () => void }; regiaoId: string; regiaoNome: string }) {
  const ordenados = [...votos].sort((a, b) => b.votos - a.votos || a.candidato.localeCompare(b.candidato));
  const total = ordenados.reduce((s, v) => s + v.votos, 0);
  const principais = ordenados.slice(0, 3), resto = ordenados.slice(3);
  const partes = [...principais.map(v => ({ nome: nomeCandidato(v.candidato), votos: v.votos })),
    ...(resto.length ? [{ nome: `Outros ${resto.length}`, votos: resto.reduce((s, v) => s + v.votos, 0), outros: true }] : [])];
  const R = regioes.data;
  return <section id="voto" aria-labelledby="voto-title" className="federal-section">
    <SectionHeading id="voto-title" kicker="5 · Voto" title="Como a cidade votou, e como votaram lugares parecidos?" />
    <Card className="federal-chart">
      <h3>Votação presidencial · 2026 · 1º turno</h3>
      {total > 0 ? <>
        <BarraVotos partes={partes} total={total} />
        <p className="hint">TSE, {numero(total)} votos nos candidatos.{principais[2] ? ` ${nomeCandidato(principais[2].candidato)} teve ${percentual(100 * principais[2].votos / total)}.` : ""}{resto.length ? ` Os outros ${resto.length} candidatos somaram ${percentual(100 * partes.at(-1)!.votos / total)}.` : ""} Todos os candidatos na mesma cor: o gráfico mostra tamanho, não lado.</p>
        <details className="federal-details"><summary>Ver todos os candidatos</summary><VotosMunicipais votos={votos} /></details>
      </> : <p>Dados eleitorais indisponíveis. Ausência não significa zero.</p>}
    </Card>
    {regioes.error ? <Feedback kind="error" action={<Button onClick={regioes.retry}>Tentar novamente</Button>}>{regioes.error}</Feedback>
      : !R ? <Feedback kind="loading">Carregando a comparação entre regiões…</Feedback>
      : R.regioes.length ? <Card className="federal-chart">
        <h3>Onde o dinheiro federal pesa mais, Lula teve mais votos</h3>
        <p>Cada ponto é uma das {numero(R.regioes.length)} regiões do país. A relação aparece no Nordeste e também no restante do Brasil.</p>
        <Legenda itens={[{ classe: "viz-sw-1", texto: "Regiões do Nordeste", ponto: true }, { classe: "viz-sw-2", texto: "Demais regiões", ponto: true }, { classe: "viz-sw-ink", texto: `Região de ${regiaoNome}`, ponto: true }]} />
        <Dispersao pontos={R.regioes.map(p => ({ id: p.id, nome: p.nome, uf: p.uf, ne: p.regiao === "Nordeste", x: p.federal_percentual_do_pib, y: p.lula_percentual }))}
          destaque={regiaoId} rotuloDestaque={`Região de ${regiaoNome}`} eixoX="Dinheiro federal como parte da economia" eixoY="Votos em Lula, 1º turno 2026" />
        <details className="federal-details"><summary>Ver dados da região de {regiaoNome}</summary>
          <p className="hint">{(() => { const a = R.regioes.find(p => p.id === regiaoId);
            return a ? `Dinheiro federal: ${percentual(a.federal_percentual_do_pib)} da economia. Votos em Lula: ${percentual(a.lula_percentual)}.` : "A região não tem os quatro tipos de dinheiro disponíveis para este ano."; })()}</p>
        </details>
        <p className="footnote">Associação entre lugares, não entre pessoas: não mostra que quem recebe dinheiro federal votou em Lula, nem que o dinheiro causou o voto. Regiões com mais dinheiro federal também tendem a ser mais pobres e mais envelhecidas, fatores que podem explicar as duas coisas.{R.correlacao.brasil != null ? ` Correlação: ${numero(R.correlacao.brasil, 2)} no Brasil; ${numero(R.correlacao.nordeste ?? 0, 2)} no Nordeste; ${numero(R.correlacao.demais ?? 0, 2)} nas demais regiões.` : ""}</p>
      </Card> : <Feedback kind="empty">A relação entre regiões depende dos quatro tipos de dinheiro para o mesmo ano e ainda não está disponível.</Feedback>}
  </section>;
}

export { curto };
