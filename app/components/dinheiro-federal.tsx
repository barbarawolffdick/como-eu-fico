"use client";

import { Card } from "@/app/components/ui/card";
import { DataBar } from "@/app/components/ui/data-bar";
import { Feedback } from "@/app/components/ui/feedback";
import { Button } from "@/app/components/ui/button";
import { useResource } from "@/app/hooks/use-resource";
import VotosMunicipais from "./votos-municipais";
import {
  FLUXOS, NOMES_FLUXO, PARA_PESSOAS, PARA_PREFEITURA, totalFederal,
  type Comparacao, type Fluxo, type RespostaDinheiroFederal, type RespostaRegioes,
} from "@/lib/dinheiro-federal";

const NOME_CURTO: Record<Fluxo, string> = { inss: "INSS", bolsa_familia: "Bolsa Família", fpm: "FPM", sus: "SUS" };
const lista = (itens: string[]) => itens.length < 2 ? itens.join("") : itens.slice(0, -1).join(", ") + " e " + itens.at(-1);
const numero = (v: number, casas = 0) => v.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });
const percentual = (v: number, casas = 1) => numero(v, casas) + "%";
export function reaisCompacto(centavos: number) {
  const reais = centavos / 100;
  if (Math.abs(reais) >= 1e9) return `R$ ${numero(reais / 1e9, 2)} ${Math.abs(reais) < 2e9 ? "bilhão" : "bilhões"}`;
  if (Math.abs(reais) >= 1e6) return `R$ ${numero(reais / 1e6, Math.abs(reais) < 1e7 ? 1 : 0)} milhões`;
  return `R$ ${numero(reais, 0)}`;
}

function SectionHeading({ id, kicker, title }: { id: string; kicker: string; title: string }) {
  return <div className="section-heading"><div><p className="kicker">{kicker}</p><h2 id={id}>{title}</h2></div></div>;
}

function Ausente({ motivo }: { motivo?: string }) {
  return <span className="hint federal-absent">Indisponível. {motivo ?? "Ausência não é zero."}</span>;
}

export default function DinheiroFederal({ codigo, votos }: { codigo: string; votos: { candidato: string; votos: number }[] }) {
  const resposta = useResource<RespostaDinheiroFederal>("/api/dinheiro-federal/" + codigo, "Não foi possível carregar o dinheiro federal da cidade.");
  const regioes = useResource<RespostaRegioes>("/api/dinheiro-federal/regioes", "Não foi possível carregar a comparação entre regiões.");
  if (resposta.error) return <section id="quanto" aria-labelledby="quanto-title"><SectionHeading id="quanto-title" kicker="1 · Quanto chega" title="Quanto dinheiro federal chegou à cidade?" />
    <Feedback kind="error" action={<Button onClick={resposta.retry}>Tentar novamente</Button>}>{resposta.error}</Feedback></section>;
  if (!resposta.data) return <Feedback kind="loading">Calculando o dinheiro federal da cidade…</Feedback>;
  const { ano, pib, cidade } = resposta.data;
  return <>
    <QuantoChega ano={ano} pibEstimado={pib.estimado} pibAnoFonte={pib.ano_fonte} cidade={cidade} />
    <ParaQuem ano={ano} cidade={cidade} />
    <ComoMudou cidade={cidade} />
    <ComparaRegiao ano={ano} pibEstimado={pib.estimado} cidade={cidade} />
    <VotoERelacao votos={votos} regioes={regioes.data} erro={regioes.error} retry={regioes.retry} regiaoId={cidade.regiao_imediata.id} regiaoNome={cidade.regiao_imediata.nome} />
  </>;
}

function QuantoChega({ ano, pibEstimado, pibAnoFonte, cidade }: { ano: number; pibEstimado: boolean; pibAnoFonte: number; cidade: RespostaDinheiroFederal["cidade"] }) {
  const disponiveis = FLUXOS.filter(f => cidade.fluxos[f] != null);
  const soma = disponiveis.reduce((s, f) => s + (cidade.fluxos[f] ?? 0), 0);
  const completo = totalFederal(cidade.fluxos) !== null;
  const share = cidade.pib_centavos ? 100 * soma / cidade.pib_centavos : null;
  const maior = Math.max(1, ...disponiveis.map(f => cidade.fluxos[f] ?? 0));
  return <section id="quanto" aria-labelledby="quanto-title" className="federal-section">
    <SectionHeading id="quanto-title" kicker="1 · Quanto chega" title={`Quanto dinheiro federal chegou à cidade em ${ano}?`} />
    <Card className="federal-hero">
      {disponiveis.length ? <>
        <p className="big federal-big">{reaisCompacto(soma)}</p>
        <p className="federal-lead">chegaram a {cidade.municipio.nome} em {ano} por aposentadorias, Bolsa Família e repasses federais à prefeitura. São cerca de <b>{reaisCompacto(soma / 365)} por dia</b>.</p>
        {!completo && <p className="hint">{lista(FLUXOS.filter(f => cidade.fluxos[f] == null).map(f => NOME_CURTO[f]))} não {FLUXOS.filter(f => cidade.fluxos[f] == null).length > 1 ? "têm" : "tem"} dado para {ano} nesta cidade; o total considera {lista(disponiveis.map(f => NOME_CURTO[f]))}.</p>}
        {share !== null ? <div className="federal-scale">
          <p>É como se, a cada <b>R$ 100</b> produzidos na cidade, <b>R$ {numero(share, 0)}</b> viessem do governo federal{pibEstimado ? " (estimativa)" : ""}.</p>
          <div className="federal-stack" role="img" aria-label={`Dinheiro federal: ${percentual(share, 0)} da economia da cidade`}><span style={{ width: `${Math.min(100, share)}%` }} /></div>
          <div className="federal-scale-labels" aria-hidden="true"><b>Dinheiro federal · {percentual(share, 0)}</b><span>Restante da economia · {percentual(Math.max(0, 100 - share), 0)}</span></div>
          <p className="hint">A barra inteira representa tudo o que a economia da cidade produziu em {ano}, cerca de {reaisCompacto(cidade.pib_centavos!)}{pibEstimado ? " (estimativa)" : ""}.</p>
        </div> : <p className="hint">Sem PIB municipal para comparar com a economia da cidade. {cidade.ausencias.pib ?? ""}</p>}
        <ul className="federal-flows">{FLUXOS.map(f => <li key={f}>
          <span>{NOMES_FLUXO[f]}</span>
          {cidade.fluxos[f] != null ? <><b>{reaisCompacto(cidade.fluxos[f]!)}</b>
            {cidade.pib_centavos ? <small>{percentual(100 * cidade.fluxos[f]! / cidade.pib_centavos)} da economia</small> : null}
            <DataBar value={cidade.fluxos[f]!} max={maior} /></> : <Ausente motivo={cidade.ausencias[f]} />}
        </li>)}</ul>
      </> : <Feedback kind="empty">Não há dados de dinheiro federal para esta cidade em {ano}. Ausência não é zero.</Feedback>}
    </Card>
    <p className="footnote">{pibEstimado
      ? `O PIB mais recente das cidades é de ${pibAnoFonte}. Para comparar com o dinheiro de ${ano}, aplicamos ao PIB da cidade o crescimento da economia do país no período; o resultado é uma estimativa. `
      : ""}Soma ilustrativa de vias com naturezas diferentes: benefícios pagos a pessoas e repasses à prefeitura. Valores sem desconto da inflação.</p>
  </section>;
}

function Linha({ nome, valor, detalhe, filho = false }: { nome: string; valor: number | null; detalhe?: string; filho?: boolean }) {
  return <div className={`federal-row${filho ? " federal-row--child" : ""}`}><span>{nome}</span>{valor != null ? <b>{reaisCompacto(valor)}</b> : <span className="hint">Indisponível</span>}{detalhe && <p className="hint">{detalhe}</p>}</div>;
}

function ParaQuem({ ano, cidade }: { ano: number; cidade: RespostaDinheiroFederal["cidade"] }) {
  const soma = (fs: Fluxo[]) => fs.every(f => cidade.fluxos[f] != null) ? fs.reduce((s, f) => s + cidade.fluxos[f]!, 0) : null;
  const pessoas = soma(PARA_PESSOAS), prefeitura = soma(PARA_PREFEITURA);
  const total = pessoas != null && prefeitura != null ? pessoas + prefeitura : null;
  const d = cidade.inss_detalhe, q = cidade.inss_quantidade_dezembro;
  const regiaoInss = cidade.comparacoes[1]?.percentual_do_pib.inss;
  const por100 = cidade.inss_beneficios_por_100_habitantes;
  return <section id="para-quem" aria-labelledby="para-quem-title" className="federal-section">
    <SectionHeading id="para-quem-title" kicker="2 · Para quem" title="Para quem vai esse dinheiro?" />
    {total ? <p className="federal-lead">Cerca de {numero(Math.round(10 * pessoas! / total), 0)} em cada 10 reais chegam diretamente às pessoas. O restante vai para a prefeitura manter serviços.</p> : null}
    <div className="federal-grid">
      <Card>
        <h3>Para as pessoas{pessoas != null ? ` · ${reaisCompacto(pessoas)}` : ""}</h3>
        <div className="federal-rows">
          <Linha nome={NOMES_FLUXO.inss} valor={cidade.fluxos.inss} />
          {d && <>
            <Linha filho nome="Aposentadorias" valor={d.aposentadorias} />
            <Linha filho nome="BPC e outros benefícios assistenciais" valor={d.assistencial_e_legislacao_especifica} detalhe="Inclui o BPC para idosos e pessoas com deficiência de baixa renda" />
            <Linha filho nome="Pensões por morte" valor={d.pensoes_por_morte} />
            <Linha filho nome="Auxílios e outros" valor={d.auxilios + d.outros_previdenciarios} />
          </>}
          {cidade.inss_orgao_pagador_atipico && por100 !== null
            ? <p className="federal-callout" role="note">Esta cidade tem {numero(por100, 1)} benefícios do INSS por 100 habitantes, {por100 < 5 ? "muito abaixo" : "muito acima"} do comum. Os benefícios são contados na cidade da agência que paga: {por100 < 5 ? "parte dos moradores recebe em cidades vizinhas" : "a cidade paga benefícios de moradores de cidades vizinhas"}.{regiaoInss != null ? ` Na região de ${cidade.regiao_imediata.nome}, o INSS equivale a ${percentual(regiaoInss)} da economia.` : ""}</p>
            : <p className="hint federal-note">Os benefícios do INSS são contados na cidade onde são pagos, que nem sempre é a cidade onde o beneficiário mora.{q ? ` Em dezembro de ${ano}, foram ${numero(q.total)} benefícios pagos pela cidade.` : ""}</p>}
          <Linha nome={NOMES_FLUXO.bolsa_familia} valor={cidade.fluxos.bolsa_familia} detalhe={cidade.fluxos.bolsa_familia == null ? cidade.ausencias.bolsa_familia : undefined} />
        </div>
      </Card>
      <Card>
        <h3>Para a prefeitura{prefeitura != null ? ` · ${reaisCompacto(prefeitura)}` : ""}</h3>
        <div className="federal-rows">
          <Linha nome="FPM" valor={cidade.fluxos.fpm} detalhe={cidade.fluxos.fpm == null ? cidade.ausencias.fpm : "Parte dos impostos federais que a Constituição destina aos municípios, de uso livre"} />
          <Linha nome="SUS, fundo municipal de saúde" valor={cidade.fluxos.sus} detalhe={cidade.fluxos.sus == null ? cidade.ausencias.sus : "Atenção primária, hospitais, vigilância e gestão"} />
        </div>
        <p className="hint">Não inclui convênios, obras e outros repasses ainda não integrados ao projeto.</p>
      </Card>
    </div>
  </section>;
}

function ComoMudou({ cidade }: { cidade: RespostaDinheiroFederal["cidade"] }) {
  const serie = cidade.serie;
  if (!serie) return null;
  const anos = serie.anos;
  const pontos = (f: "inss" | "fpm") => anos.filter(a => serie[f][a].real != null);
  const inssAnos = pontos("inss"), fpmAnos = pontos("fpm");
  const variacao = (f: "inss" | "fpm", campo: "real" | "nominal", de: string, ate: string) => 100 * (serie[f][ate][campo]! / serie[f][de][campo]! - 1);
  const W = 640, H = 230, L = 44, B = 196, T = 16;
  const maxv = Math.max(1, ...anos.flatMap(a => [serie.inss[a].real ?? 0, serie.fpm[a].real ?? 0]));
  const passo = maxv / 1e8 > 600 ? 300 : maxv / 1e8 > 150 ? 100 : maxv / 1e8 > 30 ? 20 : 5;
  const topo = Math.ceil(maxv / 1e8 / passo) * passo;
  const y = (centavos: number) => B - (B - T) * (centavos / 1e8) / topo;
  const grupo = (W - L - 10) / anos.length;
  const largura = Math.min(26, grupo / 2 - 4);
  const mi = (c: number) => numero(c / 1e8, 0);
  const rotulo = (f: "inss" | "fpm") => f === "inss" ? "INSS" : "FPM";
  // Variação real: abaixo de 2% em módulo é tratada como estabilidade, para não destacar oscilações pequenas.
  const frase = (sujeito: string, v: number, de: string, ate: string) => Math.abs(v) < 2
    ? `Descontada a inflação, ${sujeito.charAt(0).toLowerCase() + sujeito.slice(1)} ficou estável de ${de} a ${ate} (${v >= 0 ? "+" : "−"}${percentual(Math.abs(v), 0)}).`
    : `Descontada a inflação, ${sujeito.charAt(0).toLowerCase() + sujeito.slice(1)} ${v > 0 ? "cresceu" : "caiu"} ${percentual(Math.abs(v), 0)} de ${de} a ${ate}.`;
  return <section id="mudou" aria-labelledby="mudou-title" className="federal-section">
    <SectionHeading id="mudou-title" kicker="3 · Como mudou" title="Como esse dinheiro mudou nos últimos anos?" />
    <Card className="federal-chart">
      {inssAnos.length >= 2 && <p className="federal-lead">{frase("O INSS pago pela cidade", variacao("inss", "real", inssAnos[0], inssAnos.at(-1)!), inssAnos[0], inssAnos.at(-1)!)} Sem descontar a inflação, a variação parece de {percentual(variacao("inss", "nominal", inssAnos[0], inssAnos.at(-1)!), 0)}.{fpmAnos.length >= 2 ? " " + frase("O FPM", variacao("fpm", "real", fpmAnos[0], fpmAnos.at(-1)!), fpmAnos[0], fpmAnos.at(-1)!) : ""}</p>}
      <div className="federal-legend"><span><i className="federal-dot federal-dot--bar-inss" />INSS</span><span><i className="federal-dot federal-dot--bar-fpm" />FPM</span></div>
      <svg className="federal-series" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Valores anuais em milhões de reais de ${serie.base_inflacao}. INSS: ${anos.map(a => `${a} ${serie.inss[a].real != null ? mi(serie.inss[a].real!) : "sem dado"}`).join(", ")}. FPM: ${anos.map(a => `${a} ${serie.fpm[a].real != null ? mi(serie.fpm[a].real!) : "sem dado completo"}`).join(", ")}.`}>
        {[0, 1, 2, 3].map(i => { const v = topo * i / 3; return <g key={i}><line x1={L} y1={B - (B - T) * i / 3} x2={W - 6} y2={B - (B - T) * i / 3} /><text x={L - 6} y={B - (B - T) * i / 3 + 4} textAnchor="end">{numero(v, 0)}</text></g>; })}
        {anos.map((a, i) => { const x0 = L + i * grupo + (grupo - 2 * largura - 4) / 2; return <g key={a}>
          {(["inss", "fpm"] as const).map((f, j) => { const v = serie[f][a].real; const xb = x0 + j * (largura + 4);
            return v == null ? <text key={f} x={xb + largura / 2} y={B - 6} textAnchor="middle" className="is-gap">s/d</text>
              : <path key={f} className={`is-${f}`} d={`M${xb} ${B} V${y(v) + 4} a4 4 0 0 1 4 -4 H${xb + largura - 4} a4 4 0 0 1 4 4 V${B} Z`}><title>{`${a} · ${rotulo(f)}: R$ ${mi(v)} milhões em reais de ${serie.base_inflacao}`}</title></path>; })}
          <text x={L + i * grupo + grupo / 2} y={B + 16} textAnchor="middle">{a}</text></g>; })}
        {inssAnos.length > 0 && [inssAnos[0], inssAnos.at(-1)!].filter((a, i, l) => l.indexOf(a) === i).map(a => { const i = anos.indexOf(a); const x0 = L + i * grupo + (grupo - 2 * largura - 4) / 2;
          return <text key={"v" + a} className="is-value" x={x0 + largura / 2} y={y(serie.inss[a].real!) - 6} textAnchor="middle">{mi(serie.inss[a].real!)}</text>; })}
        <text x={L} y={H - 2}>R$ milhões por ano, em reais de {serie.base_inflacao} (IPCA)</text>
      </svg>
      <p className="footnote">Valores de cada ano convertidos para reais de {serie.base_inflacao} pelo IPCA médio do ano. “s/d”: o dado da fonte está incompleto nesse ano (meses ausentes, publicados pela metade ou com nomes de municípios ainda sem correspondência revisada), por isso não mostramos o total. Bolsa Família e SUS ganham suas séries quando os anos anteriores forem integrados.</p>
    </Card>
  </section>;
}

function ComparaRegiao({ ano, pibEstimado, cidade }: { ano: number; pibEstimado: boolean; cidade: RespostaDinheiroFederal["cidade"] }) {
  const vias = FLUXOS.filter(f => cidade.fluxos[f] != null);
  const parcial = vias.length < FLUXOS.length;
  const totalDe = (l: Comparacao) => vias.length && vias.every(f => l.percentual_do_pib[f] != null) ? vias.reduce((s, f) => s + l.percentual_do_pib[f]!, 0) : null;
  const linhas = cidade.comparacoes.map(l => ({ ...l, total: totalDe(l) }));
  const escala = Math.max(10, Math.ceil(Math.max(0, ...linhas.map(l => l.total ?? 0)) / 10) * 10);
  const [propria, regiao, vizinhos] = linhas;
  const temVizinhos = vizinhos && vizinhos.nome.startsWith("As ");
  return <section id="compara" aria-labelledby="compara-title" className="federal-section">
    <SectionHeading id="compara-title" kicker="4 · Comparação" title="O dinheiro federal pesa mais ou menos aqui?" />
    <Card>
      {parcial && <p className="hint federal-compare-note">Comparação feita com {lista(vias.map(f => NOME_CURTO[f]))}, as vias com dado para {cidade.municipio.nome} em {ano}.</p>}
      <ul className="federal-compare">{linhas.map((l, i) => <li key={l.nome} className={i === 0 ? "is-current" : undefined}>
        <span>{l.nome}{l.detalhe && <small>{l.detalhe}</small>}</span>
        {l.total !== null ? <><b>{percentual(l.total, 0)}</b><DataBar value={l.total} max={escala} label={`${l.nome}: ${percentual(l.total, 0)} da economia`} /></> : <span className="hint">Indisponível</span>}
      </li>)}</ul>
      {propria.total !== null && regiao?.total != null && <p className="federal-insight">{temVizinhos && vizinhos.total !== null
        ? `Em ${cidade.municipio.nome}, o dinheiro federal equivale a ${numero(propria.total, 0)} de cada R$ 100 produzidos; nas cidades vizinhas, a ${numero(vizinhos.total, 0)}. Como o INSS é contado na cidade onde é pago, a região inteira (${percentual(regiao.total, 0)}) é a comparação mais justa com o estado.`
        : `Em ${cidade.municipio.nome}, o dinheiro federal equivale a ${numero(propria.total, 0)} de cada R$ 100 produzidos.`}</p>}
      <details className="federal-details"><summary>Ver por tipo de dinheiro</summary>
        <div className="table-scroll"><table className="data-table data-table--wide">
          <caption className="sr-only">Dinheiro federal como percentual da economia em {ano}, por tipo e território</caption>
          <thead><tr><th scope="col">Território</th>{FLUXOS.map(f => <th scope="col" key={f}>{NOMES_FLUXO[f]}</th>)}<th scope="col">Total</th></tr></thead>
          <tbody>{cidade.comparacoes.map((l: Comparacao) => <tr key={l.nome}><th scope="row">{l.nome}</th>
            {FLUXOS.map(f => <td key={f}>{l.percentual_do_pib[f] != null ? percentual(l.percentual_do_pib[f]!) : "—"}</td>)}
            <td>{l.total != null ? percentual(l.total) : "—"}</td></tr>)}</tbody>
        </table></div>
        <p className="hint">Percentual da economia{pibEstimado ? " estimada" : ""} de {ano}. “—”: sem dado para este território. Escala das barras: {escala}% da economia.</p>
      </details>
    </Card>
  </section>;
}

function VotoERelacao({ votos, regioes, erro, retry, regiaoId, regiaoNome }: { votos: { candidato: string; votos: number }[]; regioes: RespostaRegioes | null; erro: string; retry: () => void; regiaoId: string; regiaoNome: string }) {
  return <section id="voto" aria-labelledby="voto-title" className="federal-section">
    <SectionHeading id="voto-title" kicker="5 · Voto" title="Como a cidade votou, e como votaram lugares parecidos?" />
    <Card>
      <h3>Votação presidencial · 2026</h3>
      <VotosMunicipais votos={votos} />
      <p className="hint">TSE, 1º turno de 2026, percentuais sobre os votos nos candidatos.</p>
    </Card>
    {erro ? <Feedback kind="error" action={<Button onClick={retry}>Tentar novamente</Button>}>{erro}</Feedback>
      : !regioes ? <Feedback kind="loading">Carregando a comparação entre regiões…</Feedback>
      : regioes.regioes.length ? <Card className="federal-chart">
        <h3>Onde o dinheiro federal pesa mais, Lula teve mais votos</h3>
        <p className="federal-lead">Cada ponto é uma das {numero(regioes.regioes.length)} regiões do país. A relação aparece tanto no Nordeste quanto no restante do Brasil.</p>
        <Dispersao regioes={regioes} destaque={regiaoId} nomeDestaque={regiaoNome} />
        <p className="footnote">Associação entre lugares, não entre pessoas: não mostra que quem recebe dinheiro federal votou em Lula, nem que o dinheiro causou o voto. Regiões com mais dinheiro federal também tendem a ser mais pobres e mais envelhecidas, fatores que podem explicar as duas coisas.{regioes.correlacao.brasil != null ? ` Correlação: ${numero(regioes.correlacao.brasil, 2)} no Brasil; ${numero(regioes.correlacao.nordeste ?? 0, 2)} no Nordeste; ${numero(regioes.correlacao.demais ?? 0, 2)} nas demais regiões.` : ""}</p>
      </Card> : <Feedback kind="empty">A relação entre regiões depende dos quatro tipos de dinheiro para o mesmo ano e ainda não está disponível.</Feedback>}
  </section>;
}

function Dispersao({ regioes, destaque, nomeDestaque }: { regioes: RespostaRegioes; destaque: string; nomeDestaque: string }) {
  const W = 640, H = 380, L = 48, R = 14, T = 12, B = 330;
  const xMax = Math.max(10, Math.ceil(Math.max(...regioes.regioes.map(p => p.federal_percentual_do_pib)) / 10) * 10);
  const px = (v: number) => L + (W - L - R) * v / xMax;
  const py = (v: number) => B - (B - T) * v / 100;
  const atual = regioes.regioes.find(p => p.id === destaque);
  const pontos = [...regioes.regioes].sort((a, b) => Number(a.regiao === "Nordeste") - Number(b.regiao === "Nordeste")).filter(p => p.id !== destaque);
  return <>
    <div className="federal-legend"><span><i className="federal-dot federal-dot--ne" />Regiões do Nordeste</span><span><i className="federal-dot federal-dot--out" />Demais regiões</span><span><i className="federal-dot federal-dot--current" />Região de {nomeDestaque}</span></div>
    <svg className="federal-scatter" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${regioes.regioes.length} regiões imediatas: dinheiro federal como parte da economia e votos em Lula.${atual ? ` Região de ${nomeDestaque}: ${percentual(atual.federal_percentual_do_pib)} e ${percentual(atual.lula_percentual)}.` : ""}`}>
      {Array.from({ length: xMax / 10 + 1 }, (_, i) => i * 10).map(v => <g key={"x" + v}><line x1={px(v)} y1={T} x2={px(v)} y2={B} /><text x={px(v)} y={B + 16} textAnchor="middle">{v}%</text></g>)}
      {[0, 25, 50, 75, 100].map(v => <g key={"y" + v}><line x1={L} y1={py(v)} x2={W - R} y2={py(v)} /><text x={L - 6} y={py(v) + 4} textAnchor="end">{v}%</text></g>)}
      {pontos.map(p => <circle key={p.id} cx={px(p.federal_percentual_do_pib)} cy={py(p.lula_percentual)} r={4} className={p.regiao === "Nordeste" ? "is-ne" : "is-out"}>
        <title>{`${p.nome} (${p.uf}): dinheiro federal ${percentual(p.federal_percentual_do_pib)} da economia · Lula ${percentual(p.lula_percentual)}`}</title></circle>)}
      {atual && <><circle cx={px(atual.federal_percentual_do_pib)} cy={py(atual.lula_percentual)} r={7} className="is-current"><title>{`Região de ${nomeDestaque}: ${percentual(atual.federal_percentual_do_pib)} · Lula ${percentual(atual.lula_percentual)}`}</title></circle>
        <text className="is-label" x={Math.min(px(atual.federal_percentual_do_pib) + 11, W - 190)} y={py(atual.lula_percentual) + 4}>Região de {nomeDestaque}</text></>}
      <text x={(W + L) / 2} y={H - 4} textAnchor="middle">Dinheiro federal como parte da economia</text>
      <text x={12} y={(T + B) / 2} textAnchor="middle" transform={`rotate(-90 12 ${(T + B) / 2})`}>Votos em Lula, 1º turno 2026</text>
    </svg>
    <details className="federal-details"><summary>Ver dados da região de {nomeDestaque}</summary>
      <p className="hint">{atual ? `Dinheiro federal: ${percentual(atual.federal_percentual_do_pib)} da economia. Votos em Lula: ${percentual(atual.lula_percentual)}.` : "A região não tem os quatro tipos de dinheiro disponíveis para este ano."}</p>
    </details>
  </>;
}
