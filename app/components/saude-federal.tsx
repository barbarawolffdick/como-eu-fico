"use client";

import Image from "next/image";
import { Card } from "@/app/components/ui/card";
import { Feedback } from "@/app/components/ui/feedback";
import { Button } from "@/app/components/ui/button";
import SaudeMunicipal from "./saude-municipal";
import { SectionHeading } from "./dinheiro-federal";
import { Legenda, MapaArvore, Waffle, curto, numero, type BlocoArea } from "./graficos";
import type { AutorEmenda, RespostaDinheiroFederal } from "@/lib/dinheiro-federal";
import type { RespostaSaude } from "@/lib/saude";

const AREAS: Record<string, [string, string]> = {
  "ATENÇÃO DE MÉDIA E ALTA COMPLEXIDADE AMBULATORIAL E HOSPITALAR": ["Hospitais e exames especializados", "Internações, cirurgias, exames de média e alta complexidade"],
  "ATENÇÃO PRIMÁRIA": ["Atenção primária", "Postos e unidades básicas, equipes de Saúde da Família"],
  "GESTÃO DO SUS": ["Gestão do SUS", "Planejamento e organização dos serviços"],
  "VIGILÂNCIA EM SAÚDE": ["Vigilância em saúde", "Vacinação, prevenção e controle de doenças"],
  "ASSISTÊNCIA FARMACÊUTICA": ["Remédios", "Assistência farmacêutica"],
};
// Blocos abaixo desta parte do total ficam fora do desenho e são citados em texto.
const MIN_BLOCO = 0.04;
const MINUSCULAS = new Set(["de", "do", "da", "dos", "das", "e"]);
const ACENTOS: Record<string, string> = { ceara: "ceará", piaui: "piauí", parana: "paraná", amapa: "amapá", maranhao: "maranhão", goias: "goiás",
  rondonia: "rondônia", espirito: "espírito", sao: "são", comissao: "comissão", para: "pará", parlamentar: "parlamentar" };
const TIPOS: Record<string, string> = { "Emenda Individual": "individual", "Emenda de Bancada": "bancada", "Emenda de Comissão": "comissão", "Emenda de Relator": "relator" };
/** Nomes da CGU vêm em maiúsculas sem acento; aqui só a capitalização e acentos de nomes de UF. */
const nomeProprio = (t: string) => t.toLowerCase().split(/\s+/).map(p => ACENTOS[p] ?? p)
  .map((p, i) => i && MINUSCULAS.has(p) ? p : p.charAt(0).toUpperCase() + p.slice(1)).join(" ");
const periodo = (mes: string) => `${mes.slice(4, 6)}/${mes.slice(0, 4)}`;

type Emendas = RespostaDinheiroFederal["emendas"];

export default function SaudeFederal({ saude, emendas, ano }: { saude: { data: RespostaSaude | null; error: string; retry: () => void }; emendas: Emendas; ano: number }) {
  const f = saude.data?.financiamento, dados = saude.data?.dados;
  return <section id="saude" aria-labelledby="saude-title" className="federal-section">
    <SectionHeading id="saude-title" kicker="6 · Saúde" title="Como o dinheiro federal sustenta a saúde da cidade" />
    {saude.error ? <Feedback kind="error" action={<Button onClick={saude.retry}>Tentar novamente</Button>}>{saude.error}</Feedback>
      : !saude.data ? <Feedback kind="loading">Carregando a saúde da cidade…</Feedback>
      : <>
        {f && <Areas financiamento={f} ano={ano} />}
        <div className="federal-grid">
          <EmendasSaude emendas={emendas} totalSus={f?.fns.find(x => x.ano === emendas?.ano && x.completo)?.municipal?.valor_centavos ?? null} />
          {f && <QuemPagou financiamento={f} />}
        </div>
        <Rede saude={saude.data} />
        <details className="federal-details federal-more" data-testid="saude-detalhe">
          <summary>Ver todos os dados de saúde: finalidades dos repasses, equipes, unidades e equipamentos</summary>
          <SaudeMunicipal resposta={saude.data} erro="" retry={saude.retry} />
        </details>
      </>}
    {!dados && saude.data && <p className="hint">{saude.data.motivo ?? "Indicadores de saúde indisponíveis para esta cidade."}</p>}
  </section>;
}

function Areas({ financiamento, ano }: { financiamento: NonNullable<RespostaSaude["financiamento"]>; ano: number }) {
  const anos = financiamento.fns.filter(x => x.completo && x.municipal?.valor_centavos);
  const fns = anos.find(x => x.ano === ano) ?? anos.at(-1);
  if (!fns?.municipal?.valor_centavos) return <Card><h3>Para onde foi o dinheiro do SUS</h3><p>Sem repasse federal ao fundo municipal de saúde validado para um ano completo. Ausência não é zero.</p></Card>;
  const T = fns.municipal.valor_centavos;
  const areas = fns.municipal.grupos.filter(g => (g.valor_centavos ?? 0) > 0).map(g => ({ chave: g.nome, nome: (AREAS[g.nome] ?? [nomeProprio(g.nome)])[0], descricao: (AREAS[g.nome] ?? ["", ""])[1], valor: g.valor_centavos! }))
    .sort((a, b) => b.valor - a.valor);
  const grandes: BlocoArea[] = areas.filter(a => a.valor / T >= MIN_BLOCO), menores = areas.filter(a => a.valor / T < MIN_BLOCO);
  return <Card className="federal-chart">
    <h3>Para onde foi o dinheiro do SUS em {fns.ano}</h3>
    <p className="federal-lead">O governo federal mandou <b>{curto(T)}</b> para o fundo de saúde da cidade em {fns.ano}. O retângulo inteiro é esse dinheiro; cada bloco mostra quanto foi para cada área.</p>
    <MapaArvore blocos={grandes} total={T} />
    {menores.length > 0 && <p className="hint">Também: {menores.map(a => `${a.nome.toLowerCase()}, ${curto(a.valor)} (${numero(100 * a.valor / T, 1)}%)`).join("; ")}, pequenos demais para aparecer no desenho.</p>}
    <details className="federal-details"><summary>Ver tabela</summary>
      <div className="table-scroll"><table className="data-table">
        <caption className="sr-only">Repasses federais ao fundo municipal de saúde em {fns.ano}, por área</caption>
        <thead><tr><th scope="col">Área</th><th scope="col">Valor</th><th scope="col">Parte</th></tr></thead>
        <tbody>{areas.map(a => <tr key={a.chave}><th scope="row">{a.nome}</th><td>{curto(a.valor)}</td><td>{numero(100 * a.valor / T, 1)}%</td></tr>)}</tbody>
      </table></div>
    </details>
    <p className="footnote">Fonte: Fundo Nacional de Saúde, repasses ao fundo municipal em {fns.ano}. A finalidade do repasse não comprova a realização de uma compra, obra ou atendimento.</p>
  </Card>;
}

function Autor({ a, valor, para }: { a: AutorEmenda; valor: number; para?: string }) {
  const grupo = a.tipo !== "Emenda Individual";
  const nota = [a.partido_atual ? `Hoje no ${a.partido_atual}.` : "", para ? `Para: ${nomeProprio(para)}` : ""].filter(Boolean).join(" ");
  return <li>
    <span><b>{nomeProprio(a.autor)}{!grupo && a.partido ? ` (${a.partido})` : ""}</b><span className="federal-tag">{TIPOS[a.tipo] ?? a.tipo.toLowerCase()}</span></span>
    <b>{curto(valor)}</b>
    {nota && <small>{nota}</small>}
  </li>;
}

function EmendasSaude({ emendas, totalSus }: { emendas: Emendas; totalSus: number | null }) {
  if (!emendas) return <Card><h3>Quem mandou emendas para a saúde</h3><p>As emendas parlamentares ainda não estão publicadas no projeto.</p></Card>;
  const saude = emendas.autores.filter(a => a.saude_centavos > 0).sort((a, b) => b.saude_centavos - a.saude_centavos);
  const outras = emendas.autores.filter(a => a.valor_centavos - a.saude_centavos > 0).sort((a, b) => (b.valor_centavos - b.saude_centavos) - (a.valor_centavos - a.saude_centavos));
  const paraOutros = (a: AutorEmenda) => a.favorecidos.find(([f]) => !/FUNDO MUNICIPAL DE SA[UÚ]DE/i.test(f))?.[0];
  return <Card className="federal-chart">
    <h3>Quem mandou emendas para a saúde</h3>
    {saude.length ? <p><b>{curto(emendas.saude_centavos)}</b> chegaram ao fundo de saúde por emendas parlamentares em {emendas.ano}{totalSus ? `, ${numero(100 * emendas.saude_centavos / totalSus, 1)}% do dinheiro federal da saúde` : ""}.</p>
      : <p>Nenhuma emenda parlamentar foi paga ao fundo de saúde da cidade em {emendas.ano}.</p>}
    {saude.length > 0 && <ul className="federal-authors">{saude.map(a => <Autor key={a.autor} a={a} valor={a.saude_centavos} />)}</ul>}
    {outras.length > 0 && <details className="federal-details"><summary>Outras emendas recebidas na cidade em {emendas.ano} ({curto(emendas.total_centavos - emendas.saude_centavos)})</summary>
      <ul className="federal-authors">{outras.map(a => <Autor key={a.autor} a={a} valor={a.valor_centavos - a.saude_centavos} para={paraOutros(a)} />)}</ul></details>}
    <p className="footnote">Fonte: CGU, emendas parlamentares por favorecido, pagamentos de {emendas.ano} (inclui restos a pagar de anos anteriores). Partido na época da emenda, segundo a Câmara dos Deputados e o Senado. Bancadas e comissões reúnem parlamentares de vários partidos. O município é o do favorecido.</p>
  </Card>;
}

function QuemPagou({ financiamento }: { financiamento: NonNullable<RespostaSaude["financiamento"]> }) {
  const s = financiamento.siops, L = s?.fases["Despesas Liquidadas"];
  if (!s || !L?.total_centavos) return <Card><h3>Quem pagou a saúde da cidade</h3><p>A prefeitura não tem despesas de saúde do SIOPS validadas. Ausência não é zero.</p></Card>;
  const tot = L.total_centavos;
  const soma = (re: RegExp) => L.fontes.filter(x => re.test(x.nome) || re.test((x as { fonte?: string }).fonte ?? "")).reduce((t, x) => t + (x.valor_centavos ?? 0), 0);
  const uniao = soma(/Governo Federal|Transferências da União|federais/i), estado = soma(/Governo Estadual|estaduais/i);
  const q = (v: number) => Math.round(100 * v / tot);
  const qu = q(uniao), qe = q(estado), qm = Math.max(0, 100 - qu - qe);
  return <Card className="federal-chart">
    <h3>Quem pagou a saúde da cidade em {s.ano}</h3>
    <p>A prefeitura gastou <b>{curto(tot)}</b> com saúde em {s.ano}. De cada R$ 100, <b>R$ {qu}</b> vieram do governo federal.</p>
    <div className="federal-spend">
      <Waffle partes={[{ n: qu, classe: "is-c1" }, { n: qe, classe: "is-c2" }, { n: qm, classe: "is-c3" }]} rotulo={`De 100 quadrados: ${qu} governo federal, ${qe} governo estadual, ${qm} prefeitura`} />
      <Legenda itens={[{ classe: "viz-sw-1", texto: <><b>R$ {qu}</b> Governo federal</> }, { classe: "viz-sw-2", texto: <><b>R$ {qe}</b> Governo estadual</> }, { classe: "viz-sw-3", texto: <><b>R$ {qm}</b> Prefeitura</> }]} />
    </div>
    <p className="footnote">Fonte: SIOPS, despesas reconhecidas (liquidadas) declaradas pela prefeitura no {s.bimestre}º bimestre de {s.ano}. “Prefeitura” reúne impostos, transferências de impostos, recursos livres e convênios. Gasto é diferente de dinheiro recebido.</p>
  </Card>;
}

function Rede({ saude }: { saude: RespostaSaude }) {
  const f = saude.financiamento, d = saude.dados;
  const eq = Object.fromEntries((f?.equipamentos.estabelecimentos_com_equipamento_sus ?? []).map(e => [e.tipo, e.valor]));
  const esf = d?.aps?.equipes.find(e => e.tipo.startsWith("eSF"))?.financiadas ?? null;
  const fatos: [string, number | null | undefined, string][] = [
    ["hospital", f?.cnes?.ubs, "unidades básicas de saúde"],
    ["cama", f?.leitos?.leitos_sus, f?.leitos?.uti_sus != null ? `leitos SUS, ${numero(f.leitos.uti_sus)} de UTI` : "leitos SUS"],
    ["profissional", esf, "equipes de Saúde da Família com apoio federal"],
    ["estetoscopio", d?.mais_medicos.ultimo?.vagas_ocupadas, "vagas do Mais Médicos ocupadas"],
    ["raiox", eq["Raio X"], "locais com raio X pelo SUS"],
    ["dente", eq["Equipo Odontológico Completo"], "locais com atendimento odontológico pelo SUS"],
  ];
  const fontes = [f?.leitos?.competencia ? `CNES (${periodo(f.leitos.competencia)})` : "CNES",
    d?.aps ? `relatório de financiamento da APS (parcela de ${periodo(d.aps.parcela)})` : null,
    d?.mais_medicos.ultimo ? `Mais Médicos (${d.mais_medicos.ultimo.data_referencia.slice(0, 10).split("-").reverse().join("/")})` : null].filter(Boolean);
  return <Card className="federal-chart">
    <h3>A rede de saúde na cidade</h3>
    <div className="federal-facts">{fatos.map(([icone, v, texto]) => <div className="federal-fact" key={icone}>
      <Image src={`/icones/saude/${icone}.png`} alt="" width={112} height={112} className="federal-icon" />
      <b>{v != null ? numero(v) : "—"}</b><span>{v != null ? texto : `${texto}: indisponível`}</span>
    </div>)}</div>
    <p className="footnote">Fontes: {fontes.join(", ")}. Cadastros não confirmam vagas disponíveis nem atendimentos. Serviços na cidade podem atender moradores de cidades vizinhas. Ícones: Fluent Emoji 3D, Microsoft (licença MIT).</p>
  </Card>;
}
