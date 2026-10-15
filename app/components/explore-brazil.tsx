"use client";

import { ChangeIndicator } from "@/app/components/ui/change-indicator";
import { DataBar } from "@/app/components/ui/data-bar";
import { Button, ActionLink } from "@/app/components/ui/button";
import { Card } from "@/app/components/ui/card";
import { SelectField } from "@/app/components/ui/select-field";
import { Feedback } from "@/app/components/ui/feedback";
import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowUpRight, HeartPulse, Users, Vote, SlidersHorizontal, ArrowLeftRight, X, ChevronLeft, ChevronRight } from "lucide-react";
import { candidatosFiltro, filtrosIniciais, metricas, parametrosExplorar, regioesBrasil, ufRegiao, type FiltrosExplorar, type MetricaExplorar, type RegistroExplorar, type ResultadoExplorar } from "@/lib/explorar";
import { nomeCandidato } from "@/lib/eleicoes";
import { useResource } from "../hooks/use-resource";
import TermHelp from "@/app/components/ui/term-help";
const temas = [
    { id: "bolsa", nome: "Bolsa Família", detalhe: "Alcance e valores registrados", metrica: "alcance", Icon: Users },
    { id: "saude", nome: "Saúde", detalhe: "Dinheiro enviado e sua evolução", metrica: "saude_habitante", Icon: HeartPulse },
    { id: "voto", nome: "Voto", detalhe: "A escolha de cada município", metrica: "votos_lider", Icon: Vote },
] as const;
const number = (value: number) => value.toLocaleString("pt-BR");
function formatValue(value: number, metric: MetricaExplorar) {
    const kind = metricas[metric].unidade;
    if (kind === "moeda")
        return (value / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
    return (kind === "variacao" && value > 0 ? "+" : "") + value.toLocaleString("pt-BR", { maximumFractionDigits: kind === "variacao" ? 2 : 1 }) + "%";
}
function ElectionLabel({ city }: {
    city: RegistroExplorar;
}) {
    if ((city.empatados ?? 0) > 1)
        return <span>Empate na primeira colocação</span>;
    if (!city.vencedor || city.percentual_vencedor == null)
        return <span>Resultado eleitoral indisponível</span>;
    return <span>{nomeCandidato(city.vencedor)}<small>{city.percentual_vencedor.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}% dos votos dos candidatos listados</small></span>;
}
export default function ExploreBrazil({ filters }: {
    filters: FiltrosExplorar;
}) {
    const router = useRouter();
    const [pending, startTransition] = useTransition();
    const [selected, setSelected] = useState<{
        code: string;
        name: string;
    }[]>([]);
    const resource = useResource<ResultadoExplorar>("/api/explorar?" + parametrosExplorar(filters), "Não foi possível carregar esta exploração. Tente novamente.");
    const data = resource.data;
    const metric = metricas[filters.metrica];
    const scope = filters.uf || filters.regiao || "Brasil inteiro";
    const activeRegion = filters.regiao || (filters.uf ? ufRegiao[filters.uf] : "");
    const voteScope = filters.vencedor === "todos" ? "Todos os resultados eleitorais" : filters.vencedor === "empate" ? "Empates eleitorais" : filters.vencedor === "sem_dado" ? "Sem resultado eleitoral" : filters.vencedor === "outros" ? "Outros candidatos mais votados" : nomeCandidato(filters.vencedor) + " mais votado";
    const max = Math.max(1, ...data?.resultados.map(row => Math.abs(row.valor)) ?? []);
    const loading = !data && !resource.error;
    function update(changes: Partial<FiltrosExplorar>) {
        const next = { ...filters, pagina: 1, ...changes };
        startTransition(() => router.push("/explorar?" + parametrosExplorar(next), { scroll: false }));
    }
    function toggle(city: RegistroExplorar) {
        setSelected(previous => previous.some(item => item.code === city.codigo_ibge) ? previous.filter(item => item.code !== city.codigo_ibge) : previous.length < 2 ? [...previous, { code: city.codigo_ibge, name: `${city.nome} — ${city.uf}` }] : previous);
    }
    return <main id="conteudo" tabIndex={-1} className="explore-page"><div className="shell">
    <div className="city-breadcrumb"><Link href="/">Início</Link><span aria-hidden="true">/</span><span>Explorar o Brasil</span></div>
    <header className="explore-heading"><p className="kicker">Um país. Muitas realidades.</p><h1>Explore os municípios brasileiros</h1><p>Escolha uma pergunta, aproxime o olhar de uma região e descubra o que os dados mostram. O voto acompanha a leitura, sem antecipar as conclusões.</p></header>
    <div className="explore-themes" role="group" aria-label="Escolha um tema">{temas.map(({ id, nome, detalhe, metrica, Icon }) => <Button key={id} aria-pressed={metric.tema === id} disabled={pending} onClick={() => update({ metrica })}><Icon size={22} aria-hidden="true"/><span><strong>{nome}</strong><small>{detalhe}</small></span><ArrowUpRight size={18} aria-hidden="true"/></Button>)}</div>
    <section className="explore-territory" aria-label="Escolha uma região"><div><span className="kicker">Por onde você quer olhar?</span><p>Brasil, região ou estado — você escolhe o recorte.</p></div><div className="explore-regions">{["", ...regioesBrasil].map(regiao => <Button key={regiao} aria-pressed={activeRegion === regiao} disabled={pending} onClick={() => update({ regiao, uf: "" })}>{regiao || "Brasil inteiro"}</Button>)}</div></section>
    <div className="explore-workspace"><Card className="explore-filters" aria-label="Filtros da exploração" as="aside"><div className="explore-filter-heading"><SlidersHorizontal size={17} aria-hidden="true"/><h2>Refine sua pergunta</h2></div>
      <SelectField label="Indicador" value={filters.metrica} disabled={pending} onChange={event => update({ metrica: event.target.value as MetricaExplorar })}>{Object.entries(metricas).filter(([, value]) => value.tema === metric.tema).map(([key, value]) => <option value={key} key={key}>{value.nome}</option>)}</SelectField>
      <SelectField label="Estado (UF)" value={filters.uf} disabled={pending} onChange={event => update({ uf: event.target.value })}><option value="">{filters.regiao ? "Todos da região" : "Todos os estados"}</option>{Object.keys(ufRegiao).filter(uf => !filters.regiao || ufRegiao[uf] === filters.regiao).sort().map(uf => <option key={uf}>{uf}</option>)}</SelectField>
      <SelectField label="Resultado eleitoral" value={filters.vencedor} disabled={pending} onChange={event => update({ vencedor: event.target.value })}><option value="todos">Todos, incluindo empates</option>{candidatosFiltro.map(code => <option key={code} value={code}>{nomeCandidato(code)}</option>)}<option value="outros">Outros candidatos (exceto Lula e Flávio)</option><option value="empate">Empate na primeira colocação</option><option value="sem_dado">Sem resultado eleitoral disponível</option></SelectField>
      <p className="hint">Filtra pelo candidato mais votado na cidade, não pelo voto de cada pessoa atendida.<TermHelp term="recorte eleitoral">As fontes descrevem municípios inteiros. Cruzar um benefício com o resultado da cidade não permite identificar como votaram os beneficiários. No recorte geral, cidades com empate ou sem resultado eleitoral não são excluídas por esse motivo.</TermHelp></p>
      <SelectField label="Ordenar" value={filters.ordem} disabled={pending} onChange={event => update({ ordem: event.target.value as "asc" | "desc" })}><option value="desc">Maiores valores primeiro</option><option value="asc">Menores valores primeiro</option></SelectField>
      <SelectField label="Cidades por página" value={filters.limite} disabled={pending} onChange={event => update({ limite: Number(event.target.value) })}>{[10, 25, 50].map(value => <option value={value} key={value}>{value}</option>)}</SelectField>
      <Button className="explore-clear" disabled={pending} onClick={() => update({ ...filtrosIniciais, metrica: filters.metrica })}>Limpar filtros</Button>
      <ActionLink href="/analises">Investigar relações territoriais <ArrowUpRight size={16} aria-hidden="true"/></ActionLink>
    </Card>
    <section className="explore-ranking" aria-labelledby="ranking-title" aria-busy={pending || loading}><header className="explore-ranking-heading"><p className="kicker">{scope} · {voteScope}</p><h2 id="ranking-title">{metric.titulo}</h2><p>{metric.descricao}</p><div className="explore-reference"><span>{data ? data.periodo : "Período indicado após a consulta"}</span><a href={data?.fonte_url || metric.url} target="_blank" rel="noreferrer">Fonte: {metric.fonte} ↗</a></div></header>
      <div className="explore-statistics" aria-label="Cobertura do recorte"><div><strong>{data ? number(data.recorte) : "—"}</strong><span>cidades no recorte</span></div><div><strong>{data ? number(data.com_dado) : "—"}</strong><span>com este indicador</span></div><div><strong>{data ? number(data.sem_dado) : "—"}</strong><span>sem dado comparável</span></div></div>
      {pending && <Feedback className="hint" kind="loading">Atualizando filtros…</Feedback>}
      {resource.error ? <Feedback kind="error"><p>{resource.error}</p><Button onClick={resource.retry}>Tentar novamente</Button></Feedback> : loading ? <Feedback className="explore-loading" kind="loading">Carregando as cidades deste recorte…</Feedback> : data && data.resultados.length === 0 ? <Feedback kind="empty" className="explore-empty"><h3>Nenhuma cidade com dado neste recorte.</h3><p>Amplie a região, troque o resultado eleitoral ou escolha outro indicador. Ausência de dado não significa zero.</p><Button onClick={() => update({ ...filtrosIniciais, metrica: filters.metrica })}>Ampliar para o Brasil</Button></Feedback> : data ? <>
        <div className="explore-list-heading" aria-hidden="true"><span>Posição e cidade</span><span>{metric.unidade === "moeda" ? filters.metrica.endsWith("habitante") ? "Valor por habitante" : "Valor total" : metric.unidade === "variacao" ? "Mudança nominal" : "Percentual"}</span><span>Resultado eleitoral · 2026</span><span>Comparar</span></div>
        <ol className="explore-results" start={(data.pagina - 1) * filters.limite + 1} aria-label="Cidades ordenadas pelo indicador">{data.resultados.map((city, index) => {
                const checked = selected.some(item => item.code === city.codigo_ibge);

                return <li key={city.codigo_ibge} className={checked ? "is-selected" : undefined}>
            <span className="explore-position">{(data.pagina - 1) * filters.limite + index + 1}</span><div className="explore-city"><Link href={"/cidade/" + city.codigo_ibge}>{city.nome} — {city.uf}</Link><small>{city.populacao == null ? "População indisponível" : `${number(city.populacao)} habitantes · IBGE ${city.ano_populacao}`}</small></div>
            <div className="explore-value">{metric.unidade === "variacao" ? <ChangeIndicator value={city.valor} variant="inline" /> : <><strong>{formatValue(city.valor, filters.metrica)}</strong><DataBar className="explore-value-bar" value={Math.abs(city.valor)} max={metric.unidade === "percentual" ? 100 : max} /></>}</div>
            <div className="explore-election"><span className="explore-mobile-label">Eleição 2026 · </span><ElectionLabel city={city}/></div>
            <label className="explore-check"><input type="checkbox" aria-label={`Comparar ${city.nome} — ${city.uf}`} checked={checked} disabled={!checked && selected.length === 2} onChange={() => toggle(city)}/><span className="explore-mobile-label">Comparar</span></label>
          </li>;
            })}</ol>
        <div className="explore-pagination"><p>{number((data.pagina - 1) * filters.limite + 1)}–{number(Math.min(data.pagina * filters.limite, data.com_dado))} de {number(data.com_dado)} cidades com dado</p><div><Button aria-label="Página anterior" disabled={pending || data.pagina === 1} onClick={() => update({ pagina: data.pagina - 1 })} size="icon"><ChevronLeft size={17} aria-hidden="true"/></Button><span>Página {data.pagina} de {data.paginas}</span><Button aria-label="Próxima página" disabled={pending || data.pagina >= data.paginas} onClick={() => update({ pagina: data.pagina + 1 })} size="icon"><ChevronRight size={17} aria-hidden="true"/></Button></div></div>
      </> : null}
      <p className="explore-ranking-note">{metric.limite} {metric.unidade === "moeda" ? "As barras usam a mesma escala relativa entre as cidades desta página; não são percentuais do orçamento. " : metric.unidade === "percentual" ? "A barra inteira representa 100%. " : ""}Municípios sem observação comparável ficam fora da lista, sem virar zero. Empates de valor são ordenados pelo código IBGE.</p>
    </section></div>
    <Card as="section" tone="muted" className="explore-next"><div><p className="kicker">Da visão geral ao detalhe</p><h2>Encontrou uma diferença que merece atenção?</h2><p>Abra a cidade para entender o contexto ou selecione duas para colocar os dados lado a lado. Um ranking ajuda a fazer perguntas; não mede sozinho a qualidade de vida ou o desempenho de uma gestão.</p></div><ActionLink href="/fontes">Como estes dados foram construídos <ArrowUpRight size={18} aria-hidden="true"/></ActionLink></Card>
    {selected.length > 0 && <Card as="aside" className="explore-compare-dock" aria-label="Cidades selecionadas para comparar"><div><span className="kicker">{selected.length} de 2 cidades selecionadas</span><div className="explore-selection-chips">{selected.map(city => <Button key={city.code} aria-label={"Remover " + city.name} onClick={() => setSelected(previous => previous.filter(item => item.code !== city.code))}>{city.name}<X size={14} aria-hidden="true"/></Button>)}</div></div><Button variant="primary" className="explore-compare-go" disabled={selected.length !== 2} onClick={() => router.push("/comparar?" + new URLSearchParams({ a: selected[0].code, b: selected[1].code }))}><ArrowLeftRight size={17} aria-hidden="true"/>Comparar cidades</Button></Card>}
  </div></main>;
}
