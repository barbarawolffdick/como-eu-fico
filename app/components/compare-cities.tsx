"use client";

import { DataBar } from "@/app/components/ui/data-bar";
import { Feedback } from "@/app/components/ui/feedback";
import { Button, ActionLink } from "@/app/components/ui/button";
import { Card } from "@/app/components/ui/card";
import { useState, useTransition, type ReactNode } from "react";
import { mediaPorBeneficiario, leituraCobertura, type BeneficiariosCidade } from "@/lib/bolsa-familia";
import { AjudaBolsa } from "./alcance-bolsa";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeftRight, ArrowUpRight, Link2, HeartPulse, Users, Vote } from "lucide-react";
import CitySearch from "./city-search";
import TermHelp from "@/app/components/ui/term-help";
import { useResource } from "../hooks/use-resource";
import { placar, porHabitante, ultimoMesComum, type CidadeDetalhe, type CoberturaCidade } from "@/lib/comparacao";
import { nomeCandidato } from "@/lib/eleicoes";
import type { RespostaSaude } from "@/lib/saude";
type Mode = "total" | "habitante";
type BolsaMode = "pessoa" | "familia" | "total";
type State = "ready" | "loading" | "error";
const numero = (value: number) => value.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
const moeda = (value: number) => (value / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const pct = (value: number) => value.toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + "%";
const mes = (value: string) => value.slice(4) + "/" + value.slice(0, 4);
const dia = (value: string) => value.slice(0, 10).split("-").reverse().join("/");
function useCity(code: string) {
    const detail = useResource<CidadeDetalhe>("/api/municipios/" + code, "Não foi possível consultar a cidade. Confira a escolha ou tente novamente.");
    const health = useResource<RespostaSaude>("/api/saude/" + code, "Não foi possível carregar os dados de saúde.");
    const coverage = useResource<CoberturaCidade>("/api/cobertura?municipio=" + code, "Não foi possível carregar os dados de alcance do Bolsa Família.");
    const beneficiaries = useResource<BeneficiariosCidade>("/api/beneficiarios/" + code, "Não foi possível consultar as contagens de pessoas e famílias.");
    return { detail, health, coverage, beneficiaries };
}
type City = ReturnType<typeof useCity>;
function state(resource: {
    data: unknown;
    error: string;
}): State { return resource.error ? "error" : resource.data ? "ready" : "loading"; }
function ResourceError({ resource, city }: {
    resource: {
        error: string;
        retry: () => void;
    };
    city: string;
}) {
    return resource.error ? <Feedback kind="error" className="compare-error"><p><strong>{city}:</strong> {resource.error}</p><Button onClick={resource.retry}>Tentar novamente — {city}</Button></Feedback> : null;
}
function ComparisonRow({ title, description, values, periods, states = ["ready", "ready"], comparable, reason, format, differenceFormat = format, names, testId, scale, readings }: {
    title: string;
    description: string;
    values: [
        number | null,
        number | null
    ];
    periods: [
        string,
        string
    ];
    states?: [
        State,
        State
    ];
    comparable: boolean;
    reason: string;
    format: (value: number) => string;
    differenceFormat?: (value: number) => string;
    names: [
        string,
        string
    ];
    testId: string;
    scale?: number;
    readings?: [ReactNode, ReactNode];
}) {
    const valid = comparable && states.every(s => s === "ready") && values.every(value => value != null);
    const max = scale ?? Math.max(1, ...values.filter((value): value is number => value != null).map(Math.abs));
    const delta = valid ? values[0]! - values[1]! : null;
    return <Card className="comparison-row" data-testid={testId}>
    <div className="comparison-row-heading"><h3>{title}</h3><p>{description}</p></div>
    <div className="comparison-values">{values.map((value, index) => <div key={index} className={"comparison-value city-color-" + index}>
      <span className="comparison-city-label"><span className="city-key">{index === 0 ? "A" : "B"}</span>{names[index]}</span>
      <strong>{states[index] === "loading" ? "Carregando…" : states[index] === "error" ? "Falha na consulta" : value == null ? "Indisponível" : format(value)}</strong>
      {readings?.[index] && <p className="comparison-explanation">{readings[index]}</p>}
      <span className="comparison-period">{periods[index]}</span>
      {valid && <DataBar className="comparison-bar" value={Math.abs(value ?? 0)} max={max} />}
    </div>)}</div>
    <p className={"comparison-reading " + (valid ? "" : "comparison-limited")}>
      {delta != null ? delta === 0 ? "Mesmo valor nas duas cidades neste indicador." : <>Diferença: <strong>{differenceFormat(Math.abs(delta))}</strong> a mais em <strong>{delta > 0 ? names[0] : names[1]}</strong>.<span className="comparison-rounding">Calculada antes do arredondamento dos valores exibidos.</span></> : states.some(s => s === "loading") ? "Aguardando os dados das duas cidades." : states.some(s => s === "error") ? "Recupere a consulta para comparar este indicador." : reason}
    </p>
  </Card>;
}
function CitySlot({ data, code, index, onSelect }: {
    data: City;
    code: string;
    index: number;
    onSelect: (code: string) => void;
}) {
    const city = data.detail.data?.municipio;
    return <Card className={"comparison-slot city-color-" + index} aria-label={"Cidade " + (index === 0 ? "A" : "B")} as="section">
    <p className="comparison-slot-label"><span className="city-key">{index === 0 ? "A" : "B"}</span>{index === 0 ? "Primeira cidade" : "Segunda cidade"}</p>
    <h2>{city ? `${city.nome} — ${city.uf}` : data.detail.error ? "Confira a cidade" : "Carregando cidade…"}</h2>
    <p className="comparison-population">{city?.populacao != null ? `${numero(city.populacao)} habitantes · IBGE ${city.ano_populacao}` : city ? "População indisponível" : `Código IBGE ${code}`}</p>
    <CitySearch label={"Escolher cidade " + (index === 0 ? "A" : "B")} onSelect={city => onSelect(city.codigo_ibge)}/>
    {city && <ActionLink href={"/cidade/" + code}>Ver página da cidade <ArrowUpRight size={15} aria-hidden="true"/></ActionLink>}
    <ResourceError resource={data.detail} city={index === 0 ? "Cidade A" : "Cidade B"}/>
  </Card>;
}
function ElectionComparison({ cities, names }: {
    cities: [
        CidadeDetalhe,
        CidadeDetalhe
    ];
    names: [
        string,
        string
    ];
}) {
    const scores = cities.map(placar);
    const candidates = [...new Set(cities.flatMap((city, index) => scores[index] ? city.votos_presidenciais.map(v => v.candidato) : []))]
        .sort((a, b) => ((scores[0]?.percentuais[b] ?? 0) + (scores[1]?.percentuais[b] ?? 0)) - ((scores[0]?.percentuais[a] ?? 0) + (scores[1]?.percentuais[a] ?? 0)) || a.localeCompare(b));
    return <section className="compare-section" aria-labelledby="compare-vote-title"><div className="compare-section-heading"><Vote size={21} aria-hidden="true"/><div><p className="kicker">O contexto eleitoral</p><h2 id="compare-vote-title">Como cada cidade votou?</h2></div><span className="compare-source-tag">TSE · 1º turno de 2026</span></div>
    <div className="comparison-election-cards">{scores.map((score, index) => <Card className={"comparison-election-card city-color-" + index} key={index}>
      <span className="comparison-city-label"><span className="city-key">{index === 0 ? "A" : "B"}</span>{names[index]}</span>
      {score ? <><p>{score.empate ? "Empate na primeira colocação" : nomeCandidato(score.lider.candidato)}</p><strong>{pct(score.percentuais[score.lider.candidato])}</strong><small>{score.empate ? "Para cada candidato empatado na liderança." : "Dos votos dos candidatos listados."} Base: {numero(score.total)} votos.</small></> : <p>Dados eleitorais indisponíveis.</p>}
    </Card>)}</div>
    <details className="compare-votes-details"><summary>Ver a distribuição de votos por candidato</summary><div className="compare-votes-table"><table className="data-table"><caption>Percentuais calculados sobre os votos dos candidatos listados em cada cidade.</caption><thead><tr><th>Candidato</th><th>A · {names[0]}</th><th>B · {names[1]}</th></tr></thead><tbody>{candidates.map(code => <tr key={code}><th scope="row">{nomeCandidato(code)} ({code})</th>{scores.map((score, index) => <td key={index}>{score?.percentuais[code] == null ? "Indisponível" : pct(score.percentuais[code])}</td>)}</tr>)}</tbody></table></div></details>
    <p className="compare-section-note">O resultado municipal descreve votos agregados. Ele não revela como votaram os beneficiários nem por que cada pessoa escolheu um candidato.</p>
  </section>;
}
export default function CompareCities({ a, b, example, mode = "habitante", bolsaMode = "pessoa" }: {
    a: string;
    b: string;
    example: boolean;
    mode?: Mode;
    bolsaMode?: BolsaMode;
}) {
    const first = useCity(a);
    const second = useCity(b);
    const router = useRouter();
    const [pending, startTransition] = useTransition();
    const [notice, setNotice] = useState("");
    const [shared, setShared] = useState("");
    const details: [
        CidadeDetalhe | null,
        CidadeDetalhe | null
    ] = [first.detail.data, second.detail.data];
    const names: [
        string,
        string
    ] = details.map((data, index) => data ? `${data.municipio.nome} — ${data.municipio.uf}` : "Cidade " + (index === 0 ? "A" : "B")) as [
        string,
        string
    ];
    const health = [first.health.data, second.health.data];
    const transfers = health.map(data => data?.financiamento?.fns.at(-1));
    const coverage = [first.coverage.data, second.coverage.data];
    const beneficiaries = [first.beneficiaries.data, second.beneficiaries.data];
    const month = details[0] && details[1] ? ultimoMesComum(details[0], details[1]) : null;
    const healthPeriod = transfers.map(data => data ? `${mes(data.inicio)} a ${mes(data.fim)}${data.completo ? " · ano completo" : " · parcial"}` : "FNS · período indisponível") as [
        string,
        string
    ];
    const healthCompatible = !!transfers[0] && !!transfers[1] && transfers[0].inicio === transfers[1].inicio && transfers[0].fim === transfers[1].fim && transfers[0].completo === transfers[1].completo;
    const populationsCompatible = !!details[0]?.municipio.ano_populacao && details[0]?.municipio.ano_populacao === details[1]?.municipio.ano_populacao;
    const coverageCompatible = !!coverage[0] && !!coverage[1] && coverage[0].periodo === coverage[1].periodo;
    const normalize = (value: number | null | undefined, index: number) => mode === "total" ? value ?? null : details[index] ? porHabitante(value, details[index]!) : null;
    function navigate(nextA: string, nextB: string, nextMode = mode, nextBolsaMode = bolsaMode) {
        setNotice("");
        setShared("");
        const params = new URLSearchParams({ a: nextA, b: nextB, modo: nextMode, bolsa: nextBolsaMode });
        startTransition(() => router.push("/comparar?" + params, { scroll: false }));
    }
    function choose(code: string, index: number) {
        if (code === (index === 0 ? b : a)) {
            setNotice("Essa cidade já está na comparação. Escolha uma cidade diferente.");
            return;
        }
        navigate(index === 0 ? code : a, index === 1 ? code : b);
    }
    async function share() {
        try {
            await navigator.clipboard.writeText(window.location.href);
            setShared("Link copiado. Ele preserva as cidades e a unidade escolhida.");
        }
        catch {
            setShared("Para compartilhar, copie o endereço desta página no navegador.");
        }
    }
    return <main id="conteudo" tabIndex={-1} className="compare-page"><div className="shell">
    <div className="city-breadcrumb"><Link href="/">Início</Link><span aria-hidden="true">/</span><span>Comparar cidades</span></div>
    <header className="compare-heading"><div><p className="kicker">Duas cidades. Outras perspectivas.</p><h1>O que muda de uma cidade para outra?</h1><p>Coloque o voto, os recursos de saúde e o Bolsa Família lado a lado. Mesmas perguntas, com atenção ao período e ao tamanho de cada cidade.</p></div><Button className="compare-share" onClick={share}><Link2 size={17} aria-hidden="true"/>Copiar link</Button></header>
    {shared && <p className="hint" role="status">{shared}</p>}
    {example && <p className="compare-example">Começamos com São Paulo e Rio de Janeiro como exemplo. Você pode trocar qualquer uma das cidades abaixo.</p>}
    <div className="comparison-selectors"><CitySlot data={first} code={a} index={0} onSelect={code => choose(code, 0)}/><Button className="swap-cities" aria-label="Inverter as cidades" disabled={pending || a === b} onClick={() => navigate(b, a)} size="icon"><ArrowLeftRight size={20} aria-hidden="true"/></Button><CitySlot data={second} code={b} index={1} onSelect={code => choose(code, 1)}/></div>
    {(notice || a === b) && <Feedback kind="error">{notice || "Escolha duas cidades diferentes para comparar."}</Feedback>}
    {pending && <Feedback className="hint" kind="loading">Atualizando comparação…</Feedback>}
    {details[0] && details[1] && a !== b ? <div aria-busy={pending}>
      <div className="comparison-legend" aria-label="Cidades em comparação">{names.map((name, index) => <span className={"city-color-" + index} key={index}><span className="city-key">{index === 0 ? "A" : "B"}</span>{name}</span>)}</div>
      <div className="comparison-controls"><div><strong>Como comparar os recursos de saúde?</strong><p>A saúde atende a população inteira; aqui a referência é o total de moradores.<TermHelp term="comparação por habitante">Dividimos o valor registrado pela população estimada do IBGE. Não é um pagamento a cada morador. Alcance populacional e votos continuam em percentual; vagas continuam em quantidade.</TermHelp></p></div><div className="comparison-mode" role="group" aria-label="Unidade dos valores em dinheiro"><Button aria-pressed={mode === "habitante"} disabled={pending} onClick={() => navigate(a, b, "habitante")}>Por habitante</Button><Button aria-pressed={mode === "total"} disabled={pending} onClick={() => navigate(a, b, "total")}>Valor total</Button></div></div>
      <ElectionComparison cities={[details[0], details[1]]} names={names}/>
      <section className="compare-section" aria-labelledby="compare-health-title"><div className="compare-section-heading"><HeartPulse size={21} aria-hidden="true"/><div><p className="kicker">Saúde na vida cotidiana</p><h2 id="compare-health-title">Dinheiro enviado e presença de profissionais</h2></div><span className="compare-source-tag">FNS · Ministério da Saúde</span></div>
        <ResourceError resource={first.health} city={names[0]}/><ResourceError resource={second.health} city={names[1]}/>
        <ComparisonRow testId="compare-health-money" title={mode === "habitante" ? "Dinheiro federal para saúde por habitante" : "Dinheiro federal enviado à saúde da cidade"} description={mode === "habitante" ? "Valor enviado ao fundo municipal dividido pela população estimada. Não é dinheiro pago a cada morador." : "Dinheiro enviado do fundo federal ao fundo de saúde administrado pela cidade. Receber não comprova atendimento realizado."} names={names} values={[normalize(transfers[0]?.municipal?.valor_centavos, 0), normalize(transfers[1]?.municipal?.valor_centavos, 1)]} format={moeda} states={[state(first.health), state(second.health)]} periods={healthPeriod.map((period, index) => period + (mode === "habitante" ? ` · população IBGE ${details[index]?.municipio.ano_populacao ?? "indisponível"}` : "")) as [
            string,
            string
        ]} comparable={healthCompatible && (mode === "total" || populationsCompatible)} reason={!healthCompatible && transfers.every(Boolean) ? "Períodos diferentes: os valores ficam separados, sem calcular diferença." : mode === "habitante" && !populationsCompatible ? "As referências de população são diferentes ou indisponíveis. Não calculamos uma diferença por habitante." : "Não há valor municipal ou população suficiente para comparar. Indisponível não significa zero."}/>
        <ComparisonRow testId="compare-doctors" title="Mais Médicos: vagas ocupadas" description="Vagas ocupadas no provimento federal, não o total de médicos da cidade nem a quantidade de atendimentos. Esta medida continua em quantidade." names={names} values={[health[0]?.dados?.mais_medicos.ultimo?.vagas_ocupadas ?? null, health[1]?.dados?.mais_medicos.ultimo?.vagas_ocupadas ?? null]} states={[state(first.health), state(second.health)]} periods={health.map(data => data?.dados?.mais_medicos.ultimo ? dia(data.dados.mais_medicos.ultimo.data_referencia) : "Referência indisponível") as [
            string,
            string
        ]} comparable={!!health[0]?.dados?.mais_medicos.ultimo && health[0]?.dados?.mais_medicos.ultimo?.data_referencia === health[1]?.dados?.mais_medicos.ultimo?.data_referencia} format={numero} reason="Referências diferentes ou vagas indisponíveis: não calculamos uma diferença. Um zero informado pela fonte é preservado."/>
        <p className="compare-section-note">Recursos municipais ficam separados de recursos estaduais ou distritais sediados na cidade. Valores monetários sem ajuste pela inflação. <Link href="/fontes">Entenda as fontes e os recortes.</Link></p>
      </section>
      <section className="compare-section" aria-labelledby="compare-benefit-title"><div className="compare-section-heading"><Users size={21} aria-hidden="true"/><div><p className="kicker">Renda e proteção social</p><h2 id="compare-benefit-title">Bolsa Família: alcance e dinheiro registrado</h2></div><span className="compare-source-tag">MDS · CGU · IBGE</span></div>
        <ResourceError resource={first.coverage} city={names[0]}/><ResourceError resource={second.coverage} city={names[1]}/>
        <ComparisonRow testId="compare-benefit-coverage" scale={100} title="Moradores em famílias que recebem Bolsa Família" description="Percentual da população inteira da cidade que vive em famílias beneficiárias. Inclui o titular e os demais integrantes. A barra inteira representa todos os moradores." readings={coverage.map(item => item?.disponivel && item.municipio.cobertura_pct != null && item.municipio.pessoas != null ? <>{leituraCobertura(item.municipio.cobertura_pct)}<br />{numero(item.municipio.pessoas)} de {numero(item.municipio.populacao)} moradores.</> : null) as [ReactNode, ReactNode]} names={names} values={coverage.map(item => item?.disponivel ? item.municipio.cobertura_pct : null) as [
            number | null,
            number | null
        ]} format={pct} differenceFormat={value => value.toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " pontos percentuais"} states={[state(first.coverage), state(second.coverage)]} periods={coverage.map(item => item ? `${mes(item.periodo)} · população IBGE 2026` : "Referência indisponível") as [
            string,
            string
        ]} comparable={coverageCompatible} reason={coverage.every(Boolean) && !coverageCompatible ? "Meses diferentes: os percentuais ficam separados, sem calcular diferença." : "Alcance populacional indisponível em uma das cidades. Não substituímos ausência por zero."}/>
        <div className="comparison-controls"><div><strong>Quanto isso representa para quem faz parte do programa?</strong><p>Escolha a média por pessoa da família, a média por família ou o total da cidade. <AjudaBolsa /></p></div>
          <div className="comparison-mode" role="group" aria-label="Como dividir os valores do Bolsa Família">
            {([ ["pessoa", "Por pessoa da família"], ["familia", "Por família"], ["total", "Total na cidade"] ] as const).map(([value, label]) => <Button key={value} aria-pressed={bolsaMode === value} disabled={pending} onClick={() => navigate(a, b, mode, value)}>{label}</Button>)}
          </div>
        </div>
        <ResourceError resource={first.beneficiaries} city={names[0]}/><ResourceError resource={second.beneficiaries} city={names[1]}/>
        {beneficiaries.map((item, i) => item?.aviso && <Feedback key={i} kind="notice"><p>{names[i]}: {item.aviso}</p><Button onClick={i === 0 ? first.beneficiaries.retry : second.beneficiaries.retry}>Consultar pessoas novamente — {names[i]}</Button></Feedback>)}
        <ComparisonRow testId="compare-benefit-money"
          title={bolsaMode === "pessoa" ? "Valor registrado por pessoa da família beneficiária" : bolsaMode === "familia" ? "Valor médio registrado por família beneficiária" : "Valor registrado do Bolsa Família na cidade"}
          description={bolsaMode === "pessoa" ? "Dividimos o valor do mês somente pelos moradores de famílias beneficiárias no mesmo mês. Essa média não é um pagamento individual a cada integrante." : bolsaMode === "familia" ? "Dividimos o valor registrado pelas famílias beneficiárias do mesmo mês. O valor de cada família pode ser diferente da média." : "Soma dos valores das parcelas registradas na CGU no último mês com dados nas duas cidades. Não comprova saque."}
          names={names} values={details.map((item, index) => {
            const valor = item?.bolsa_familia.find(row => row.mes_competencia === month)?.valor_centavos;
            const quantidade = month ? beneficiaries[index]?.periodos[month] : null;
            return bolsaMode === "total" ? valor ?? null : mediaPorBeneficiario(valor, bolsaMode === "pessoa" ? quantidade?.pessoas : quantidade?.familias);
          }) as [number | null, number | null]}
          states={bolsaMode === "total" ? [state(first.detail), state(second.detail)] : [state(first.beneficiaries), state(second.beneficiaries)]}
          readings={beneficiaries.map(item => {
            const registro = month ? item?.periodos[month] : null;
            const n = bolsaMode === "pessoa" ? registro?.pessoas : registro?.familias;
            return bolsaMode !== "total" && n != null ? `Base da divisão: ${numero(n)} ${bolsaMode === "pessoa" ? "pessoas em famílias beneficiárias" : "famílias beneficiárias"}.` : null;
          }) as [ReactNode, ReactNode]}
          format={moeda} periods={[0, 1].map(() => month ? `${mes(month)} · último mês comum` : "Sem mês comum publicado") as [string, string]}
          comparable={!!month} reason={!month ? "Não há um mês com observações nas duas cidades. Não comparamos meses diferentes." : "Não há contagem de beneficiários validada para esse mês em uma das cidades. Não usamos pessoas de outro mês nem a população inteira."}/>

        <p className="compare-section-note">Alcance MDS e valores CGU têm períodos e conceitos próprios. Cada par acima usa a mesma medida; não somamos essas informações.</p>
      </section>
      <Card as="aside" tone="muted" className="comparison-takeaway"><p className="kicker">Comparar é o começo da investigação</p><h2>Diferenças abrem perguntas. Os dados ajudam a aprofundar.</h2><p>População, rede regional de serviços e necessidades locais influenciam a leitura. Um valor maior não comprova melhor atendimento, nem explica o voto. Esta comparação é descritiva.</p><div><ActionLink href="/analises">Investigar relações territoriais <ArrowUpRight size={17} aria-hidden="true"/></ActionLink><ActionLink href="/fontes">Conferir fontes e metodologia <ArrowUpRight size={17} aria-hidden="true"/></ActionLink></div></Card>
    </div> : a !== b && !first.detail.error && !second.detail.error ? <Feedback className="city-loading" kind="loading">Preparando os dados das duas cidades…</Feedback> : null}
  </div></main>;
}
