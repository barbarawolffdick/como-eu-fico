"use client";

// Gráficos da página da cidade. SVG desenhado na largura real do contêiner, para que o texto
// mantenha o tamanho da escala tipográfica em qualquer tela. Cores: tokens --color-viz-*.
import { useEffect, useRef, useState, type ReactNode, type MouseEvent } from "react";
import { hierarchy, treemap } from "d3-hierarchy";
import type { Enxame } from "@/lib/dinheiro-federal";

export const numero = (v: number, casas = 0) => v.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });
/** Valor curto para rótulos: R$ 1,2 bi, R$ 143 mi, R$ 950 mil. */
export function curto(centavos: number) {
  const r = centavos / 100;
  if (Math.abs(r) >= 1e9) return `R$ ${numero(r / 1e9, 2)} bi`;
  if (Math.abs(r) >= 1e6) return `R$ ${numero(r / 1e6, Math.abs(r) >= 1e7 ? 0 : 1)} mi`;
  if (Math.abs(r) >= 1e3) return `R$ ${numero(r / 1e3, 0)} mil`;
  return `R$ ${numero(r, 0)}`;
}

/** Largura do contêiner, atualizada ao redimensionar. Começa com `inicial` para o primeiro desenho. */
export function useLargura<T extends HTMLElement>(inicial = 720) {
  const ref = useRef<T>(null);
  const [largura, setLargura] = useState(inicial);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const medir = () => { const w = Math.round(el.getBoundingClientRect().width); if (w > 0) setLargura(w); };
    medir();
    const obs = new ResizeObserver(medir);
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return [ref, largura] as const;
}

type Dica = { x: number; y: number; conteudo: ReactNode } | null;
/** Dica flutuante posicionada dentro do contêiner do gráfico. */
function useDica() {
  const [dica, setDica] = useState<Dica>(null);
  const mostrar = (ev: MouseEvent<Element>, conteudo: ReactNode) => {
    const caixa = (ev.currentTarget as Element).closest(".viz-wrap")?.getBoundingClientRect();
    if (!caixa) return;
    const x = ev.clientX - caixa.left, y = ev.clientY - caixa.top;
    setDica({ x: Math.min(x + 14, caixa.width - 200), y: y + 14, conteudo });
  };
  const esconder = () => setDica(null);
  const elemento = dica ? <div className="viz-tooltip" style={{ left: Math.max(0, dica.x), top: dica.y }} role="presentation">{dica.conteudo}</div> : null;
  return { mostrar, esconder, elemento };
}

// ——— Waffle de 100 quadrados ———
export function Waffle({ partes, rotulo, className = "" }: { partes: { n: number; classe: string }[]; rotulo: string; className?: string }) {
  const quadrados: string[] = [];
  for (const p of partes) for (let i = 0; i < p.n && quadrados.length < 100; i++) quadrados.push(p.classe);
  while (quadrados.length < 100) quadrados.push("");
  return <div className={`viz-waffle ${className}`} role="img" aria-label={rotulo}>{quadrados.map((c, i) => <i key={i} className={c || undefined} />)}</div>;
}

export function Legenda({ itens }: { itens: { classe: string; texto: ReactNode; ponto?: boolean }[] }) {
  return <p className="viz-legend">{itens.map((it, i) => <span key={i}><i className={`${it.classe}${it.ponto ? " is-dot" : ""}`} aria-hidden="true" />{it.texto}</span>)}</p>;
}

// ——— Fluxo: governo federal → pessoas / prefeitura → cada via ———
export type FolhaFluxo = { nome: string; valor: number; grupo: "pessoas" | "prefeitura" };
export function Fluxo({ folhas, rotulos }: { folhas: FolhaFluxo[]; rotulos: Record<"pessoas" | "prefeitura", string> }) {
  const [ref, W] = useLargura<HTMLDivElement>();
  const { mostrar, esconder, elemento } = useDica();
  const total = folhas.reduce((s, f) => s + f.valor, 0);
  if (!total) return null;
  const estreito = W < 560;
  const nw = 14, GAP = estreito ? 6 : 10, GRUPO = estreito ? 56 : 44, MIN = estreito ? 38 : 22;
  const x0 = 150, x1 = estreito ? 0 : Math.round(W * 0.42), x2 = estreito ? Math.round(W * 0.4) : Math.round(W * 0.66);
  const H = estreito ? 380 : 400;
  const k = (H - GAP * (folhas.length - 2) - GRUPO) / total;
  // Folhas: altura proporcional; centros a pelo menos MIN px para os rótulos não se sobreporem.
  let y = 0, centro = -Infinity, anterior: string | null = null;
  const fs = folhas.map(f => {
    if (anterior && anterior !== f.grupo) y += GRUPO; else if (anterior) y += GAP;
    anterior = f.grupo;
    const h = Math.max(2, f.valor * k);
    const y0 = Math.max(y, centro + MIN - h / 2);
    centro = y0 + h / 2;
    y = y0 + h;
    return { ...f, h, y0, cy: centro };
  });
  const altura = y;
  const grupos = (["pessoas", "prefeitura"] as const).map(g => {
    const membros = fs.filter(f => f.grupo === g);
    const v = membros.reduce((s, f) => s + f.valor, 0), h = v * k;
    return membros.length ? { id: g, v, h, y0: (membros[0].y0 + membros.at(-1)!.y0 + membros.at(-1)!.h) / 2 - h / 2, membros } : null;
  }).filter(g => g !== null);
  const fita = (xa: number, ya0: number, ya1: number, xb: number, yb0: number, yb1: number) => {
    const m = (xa + xb) / 2;
    return `M${xa},${ya0} C${m},${ya0} ${m},${yb0} ${xb},${yb0} L${xb},${yb1} C${m},${yb1} ${m},${ya1} ${xa},${ya1} Z`;
  };
  const raizH = total * k, raizY = (altura - raizH) / 2;
  let ry = raizY;
  const pct = (v: number) => numero(100 * v / total, 1) + "%";
  return <div className="viz-wrap" ref={ref}>
    <svg className="viz" width={W} height={altura + (estreito ? 58 : 40)} viewBox={`0 ${estreito ? -46 : -28} ${W} ${altura + (estreito ? 58 : 40)}`} role="img"
      aria-label={"Fluxo do dinheiro federal: " + folhas.map(f => `${f.nome} ${curto(f.valor)}`).join(", ")}>
      {!estreito && grupos.map(g => { const d = fita(x0 + nw, ry, ry + g.h, x1, g.y0, g.y0 + g.h); ry += g.h;
        return <path key={g.id} className={`viz-link is-${g.id}`} d={d} onMouseMove={ev => mostrar(ev, <><b>{rotulos[g.id]}</b><br />{curto(g.v)} · {pct(g.v)}</>)} onMouseLeave={esconder} />; })}
      {grupos.map(g => { let py = g.y0; return g.membros.map(f => { const d = fita(x1 + nw, py, py + f.valor * k, x2, f.y0, f.y0 + f.h); py += f.valor * k;
        return <path key={f.nome} className={`viz-link is-${g.id}`} d={d} onMouseMove={ev => mostrar(ev, <><b>{f.nome}</b><br />{curto(f.valor)} · {pct(f.valor)} do total</>)} onMouseLeave={esconder} />; }); })}
      {!estreito && <>
        <rect className="viz-ink" x={x0} y={raizY} width={nw} height={raizH} rx={4} />
        <text className="is-strong" x={x0 - 12} y={altura / 2 - 4} textAnchor="end">Governo federal</text>
        <text className="is-value" x={x0 - 12} y={altura / 2 + 16} textAnchor="end">{curto(total)}</text>
      </>}
      {grupos.map(g => <g key={g.id}>
        <rect className={`viz-node is-${g.id}`} x={x1} y={g.y0} width={nw} height={g.h} rx={4} />
        {estreito ? <>
          <text className="is-strong is-halo" x={x1} y={g.y0 - 28}>{rotulos[g.id]}</text>
          <text className="is-value is-halo" x={x1} y={g.y0 - 10}>{curto(g.v)}</text>
        </> : <text className="is-strong is-halo" x={x1 + nw / 2} y={g.y0 - 10} textAnchor="middle">{rotulos[g.id]} · {curto(g.v)}</text>}
      </g>)}
      {fs.map(f => <g key={f.nome}>
        <rect className={`viz-node is-${f.grupo}`} x={x2} y={f.y0} width={nw} height={f.h} rx={3} />
        {estreito ? <>
          <text className="is-strong" x={x2 + nw + 10} y={f.cy - 3}>{f.nome}</text>
          <text className="is-value" x={x2 + nw + 10} y={f.cy + 15}>{curto(f.valor)}</text>
        </> : <>
          <text className="is-strong" x={x2 + nw + 12} y={f.cy + 5}>{f.nome}</text>
          <text className="is-value" x={W} y={f.cy + 5} textAnchor="end">{curto(f.valor)}</text>
        </>}
      </g>)}
    </svg>
    {elemento}
  </div>;
}

// ——— Colunas por ano (INSS e FPM, em reais do último ano) ———
export type SerieColunas = { anos: string[]; series: { id: string; nome: string; classe: string; valores: (number | null)[] }[]; base: string };
export function Colunas({ dados }: { dados: SerieColunas }) {
  const [ref, W] = useLargura<HTMLDivElement>();
  const { mostrar, esconder, elemento } = useDica();
  const H = 260, m = { l: 44, r: 8, t: 22, b: 30 };
  const maxv = Math.max(1, ...dados.series.flatMap(s => s.valores.map(v => v ?? 0))) / 1e8;
  const passo = escalaPasso(maxv * 1.1);
  const topo = Math.ceil(maxv * 1.1 / passo) * passo;
  const y = (mi: number) => H - m.b - (H - m.b - m.t) * mi / topo;
  const banda = (W - m.l - m.r) / dados.anos.length, interno = banda * 0.75, barra = interno / dados.series.length - 3;
  const ticks = Array.from({ length: Math.floor(topo / passo) + 1 }, (_, i) => i * passo);
  const primeira = dados.series[0];
  const extremos = [0, dados.anos.length - 1].filter((i, j, l) => l.indexOf(i) === j && primeira.valores[i] != null);
  return <div className="viz-wrap" ref={ref}>
    <svg className="viz" width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img"
      aria-label={`Valores anuais em milhões de reais de ${dados.base}. ` + dados.series.map(s => `${s.nome}: ` + dados.anos.map((a, i) => `${a} ${s.valores[i] != null ? numero(s.valores[i]! / 1e8) : "sem dado"}`).join(", ")).join(". ")}>
      {ticks.map(t => <g key={t}><line className="viz-grid" x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} /><text x={m.l - 8} y={y(t) + 4} textAnchor="end">{numero(t)}</text></g>)}
      {dados.anos.map((a, i) => { const xa = m.l + i * banda + (banda - interno) / 2;
        return <g key={a}>
          {dados.series.map((s, j) => { const v = s.valores[i], xx = xa + j * (barra + 3);
            return v == null ? <text key={s.id} className="is-gap" x={xx + barra / 2} y={H - m.b - 6} textAnchor="middle">s/d</text>
              : <rect key={s.id} className={s.classe} x={xx} width={Math.max(1, barra)} y={y(v / 1e8)} height={y(0) - y(v / 1e8)} rx={Math.min(4, barra / 3)}
                onMouseMove={ev => mostrar(ev, <><b>{a} · {s.nome}</b><br />R$ {numero(v / 1e8)} milhões em reais de {dados.base}</>)} onMouseLeave={esconder} />; })}
          <text x={m.l + i * banda + banda / 2} y={H - 8} textAnchor="middle">{W < 420 ? "’" + a.slice(2) : a}</text>
        </g>; })}
      {extremos.map(i => <text key={"v" + i} className="is-value" x={m.l + i * banda + (banda - interno) / 2 + barra / 2} y={y(primeira.valores[i]! / 1e8) - 6} textAnchor="middle">{numero(primeira.valores[i]! / 1e8)}</text>)}
    </svg>
    {elemento}
  </div>;
}
function escalaPasso(max: number) {
  const bruto = max / 4, p = 10 ** Math.floor(Math.log10(bruto)), n = bruto / p;
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10) * p;
}

// ——— Enxame de todas as cidades ———
export type Referencia = { nome: string; valor: number };
export function EnxameCidades({ enxame, codigo, nomeCidade, referencias }: { enxame: Enxame; codigo: string; nomeCidade: string; referencias: Referencia[] }) {
  const [ref, W] = useLargura<HTMLDivElement>();
  const { mostrar, esconder, elemento } = useDica();
  const estreito = W < 560;
  const modo = estreito ? "estreito" : "largo";
  const m = estreito ? { l: 4, r: 8, t: 72, b: 30 } : { l: 128, r: 10, t: 72, b: 30 };
  const util = W - m.l - m.r;
  const faixas = estreito ? { ne: m.t + 72, demais: m.t + 72 + 150 } : { ne: m.t + 50, demais: m.t + 50 + 150 };
  const H = faixas.demais + (estreito ? 70 : 90) + m.b;
  const escalaY = util / enxame.larguras[modo];
  const x = (v: number) => m.l + util * Math.min(v, enxame.max) / enxame.max;
  const yDe = (p: Enxame["pontos"][number]) => (p[3] ? faixas.ne : faixas.demais) + (estreito ? p[6] : p[5]) * Math.min(1.25, Math.max(0.8, escalaY));
  const raio = enxame.raios[modo] * 0.9;
  const atual = enxame.pontos.find(p => p[0] === codigo);
  const ticks = [0, 20, 40, 60, 80].filter(t => t <= enxame.max);
  // Rótulos das referências empilhados em até quatro níveis: cada um vai ao nível mais baixo onde não encosta no anterior.
  const fins: number[] = [];
  const ordenadas = [...referencias].sort((a, b) => a.valor - b.valor).map(r => {
    const largura = `${r.nome} ${numero(r.valor)}%`.length * 6.5 + 8;
    const inicio = Math.min(x(r.valor), W - largura);
    let nivel = fins.findIndex(fim => fim < inicio);
    if (nivel < 0) nivel = Math.min(fins.length, 3);
    fins[nivel] = inicio + largura;
    return { ...r, nivel, inicio };
  });
  return <div className="viz-wrap" ref={ref}>
    <svg className="viz" width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img"
      aria-label={`${numero(enxame.pontos.length)} cidades pela parte da economia que vem do dinheiro federal.${atual ? ` ${nomeCidade}: ${numero(atual[4], 1)}%.` : ""}`}>
      {ticks.map(t => <g key={t}><line className="viz-grid" x1={x(t)} x2={x(t)} y1={m.t - 6} y2={H - m.b} />
        <text x={x(t)} y={H - 8} textAnchor={t === 0 && estreito ? "start" : "middle"}>{t === enxame.max ? `${t}%+` : `${t}%`}</text></g>)}
      {estreito
        ? <><text className="is-strong is-halo" x={m.l} y={faixas.ne - 38}>Nordeste</text><text className="is-strong is-halo" x={m.l} y={faixas.demais - 62}>Demais regiões</text></>
        : <><text className="is-strong" x={0} y={faixas.ne + 4}>Nordeste</text><text className="is-strong" x={0} y={faixas.demais + 4}>Demais regiões</text></>}
      <g onMouseLeave={esconder}>{enxame.pontos.map(p => p[0] === codigo ? null :
        <circle key={p[0]} cx={x(p[4])} cy={yDe(p)} r={raio} className={p[3] ? "viz-c1 is-soft" : "viz-c2"}
          onMouseMove={ev => mostrar(ev, <><b>{p[1]} ({p[2]})</b><br />{numero(p[4], 1)}% da economia</>)} />)}</g>
      {ordenadas.map(r => { const yy = m.t - 10 - r.nivel * 16;
        return <g key={r.nome} className="viz-ref"><line x1={x(r.valor)} x2={x(r.valor)} y1={yy + 4} y2={H - m.b} />
          <text className="is-halo" x={r.inicio + 4} y={yy}>{r.nome} {numero(r.valor)}%</text></g>; })}
      {atual && <>
        <circle className="viz-ink is-ring" cx={x(atual[4])} cy={atual[3] ? faixas.ne : faixas.demais} r={6} />
        <text className="is-strong is-halo" x={x(atual[4]) + (x(atual[4]) < W / 2 ? 10 : -10)} y={(atual[3] ? faixas.ne : faixas.demais) + 4} textAnchor={x(atual[4]) < W / 2 ? "start" : "end"}>{nomeCidade} {numero(atual[4])}%</text>
      </>}
    </svg>
    {elemento}
  </div>;
}

// ——— Voto: uma barra 100% ———
export function BarraVotos({ partes, total }: { partes: { nome: string; votos: number; outros?: boolean }[]; total: number }) {
  const [ref, W] = useLargura<HTMLDivElement>();
  const { mostrar, esconder, elemento } = useDica();
  const H = 74;
  let acc = 0;
  const pct = (v: number) => numero(100 * v / total, 1) + "%";
  return <div className="viz-wrap" ref={ref}>
    <svg className="viz" width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={partes.map(p => `${p.nome} ${pct(p.votos)}`).join(", ")}>
      {partes.map((p, i) => { const x0 = W * acc / total, w = W * p.votos / total; acc += p.votos;
        return <g key={p.nome}>
          <rect className={p.outros ? "viz-c0" : "viz-vote"} x={x0 + (i ? 3 : 0)} y={30} width={Math.max(0, w - (i ? 3 : 0))} height={36} rx={4}
            onMouseMove={ev => mostrar(ev, <><b>{p.nome}</b><br />{numero(p.votos)} votos · {pct(p.votos)}</>)} onMouseLeave={esconder} />
          {w > 96 && <text className="is-strong" x={x0 + (i ? 3 : 0)} y={20}>{p.nome} {pct(p.votos)}</text>}
        </g>; })}
    </svg>
    {elemento}
  </div>;
}

// ——— Dispersão: regiões imediatas ———
export type PontoDispersao = { id: string; nome: string; uf: string; ne: boolean; x: number; y: number };
export function Dispersao({ pontos, destaque, rotuloDestaque, eixoX, eixoY }: { pontos: PontoDispersao[]; destaque: string; rotuloDestaque: string; eixoX: string; eixoY: string }) {
  const [ref, W] = useLargura<HTMLDivElement>();
  const { mostrar, esconder, elemento } = useDica();
  const estreito = W < 560;
  const H = estreito ? 360 : 420, m = { l: estreito ? 36 : 48, r: 16, t: estreito ? 32 : 12, b: 44 };
  const xMax = Math.max(10, Math.ceil(Math.max(...pontos.map(p => p.x)) / 10) * 10);
  const px = (v: number) => m.l + (W - m.l - m.r) * v / xMax, py = (v: number) => H - m.b - (H - m.b - m.t) * v / 100;
  const passoX = xMax / 10 > (estreito ? 4 : 7) ? 20 : 10;
  const atual = pontos.find(p => p.id === destaque);
  // Rótulo à direita do ponto só se couber (largura estimada pelo número de caracteres).
  const cabe = !!atual && px(atual.x) + 12 + rotuloDestaque.length * 7.5 < W;
  const ordem = pontos.filter(p => p.id !== destaque).sort((a, b) => Number(a.ne) - Number(b.ne));
  return <div className="viz-wrap" ref={ref}>
    <svg className="viz" width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img"
      aria-label={`${pontos.length} regiões imediatas: ${eixoX.toLowerCase()} e ${eixoY.toLowerCase()}.${atual ? ` ${rotuloDestaque}: ${numero(atual.x, 1)}% e ${numero(atual.y, 1)}%.` : ""}`}>
      {Array.from({ length: Math.floor(xMax / passoX) + 1 }, (_, i) => i * passoX).map(t => <g key={"x" + t}><line className="viz-grid" x1={px(t)} x2={px(t)} y1={m.t} y2={H - m.b} /><text x={px(t)} y={H - m.b + 18} textAnchor="middle">{t}%</text></g>)}
      {[0, 25, 50, 75, 100].map(t => <g key={"y" + t}><line className="viz-grid" x1={m.l} x2={W - m.r} y1={py(t)} y2={py(t)} /><text x={m.l - 8} y={py(t) + 4} textAnchor="end">{t}%</text></g>)}
      <text x={(W + m.l) / 2} y={H - 4} textAnchor="middle">{eixoX}</text>
      {estreito ? <text x={0} y={12}>{eixoY}</text>
        : <text x={12} y={(H - m.b) / 2} textAnchor="middle" transform={`rotate(-90 12 ${(H - m.b) / 2})`}>{eixoY}</text>}
      <g onMouseLeave={esconder}>{ordem.map(p => <circle key={p.id} cx={px(p.x)} cy={py(p.y)} r={estreito ? 3 : 4} className={p.ne ? "viz-c1 is-soft" : "viz-c2"}
        onMouseMove={ev => mostrar(ev, <><b>{p.nome} ({p.uf})</b><br />{eixoX}: {numero(p.x, 1)}%<br />{eixoY}: {numero(p.y, 1)}%</>)} />)}</g>
      {atual && <>
        <circle className="viz-ink is-ring" cx={px(atual.x)} cy={py(atual.y)} r={7} />
        <text className="is-strong is-halo" x={px(atual.x) + (cabe ? 12 : -12)} y={py(atual.y) + 4} textAnchor={cabe ? "start" : "end"}>{rotuloDestaque}</text>
      </>}
    </svg>
    {elemento}
  </div>;
}

// ——— Mapa de árvore: o retângulo inteiro é o total; cada bloco, uma parte ———
export type BlocoArea = { nome: string; descricao: string; valor: number };
export function MapaArvore({ blocos, total }: { blocos: BlocoArea[]; total: number }) {
  const [ref, W] = useLargura<HTMLDivElement>();
  const { mostrar, esconder, elemento } = useDica();
  const H = W < 560 ? 420 : 340;
  type No = { nome?: string; valor?: number; children?: BlocoArea[] } & Partial<BlocoArea>;
  const raiz = hierarchy<No>({ children: blocos }).sum(d => d.valor ?? 0).sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
  treemap<No>().size([W, H]).paddingInner(3).round(true)(raiz);
  // Blocos maiores no tom escuro do degradê; menores no tom claro.
  return <div className="viz-wrap" ref={ref}>
    <svg className="viz" width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img"
      aria-label={`${curto(total)} divididos por área: ` + blocos.map(b => `${b.nome} ${numero(100 * b.valor / total, 1)}%`).join(", ")}>
      {raiz.leaves().map((n, i) => {
        const r = n as typeof n & { x0: number; x1: number; y0: number; y1: number };
        const w = r.x1 - r.x0, h = r.y1 - r.y0, pct = 100 * (n.value ?? 0) / total, escuro = i < 2;
        const d = n.data as BlocoArea;
        return <g key={d.nome} transform={`translate(${r.x0},${r.y0})`} className={escuro ? "viz-tile is-dark" : "viz-tile"}
          onMouseMove={ev => mostrar(ev, <><b>{d.nome}</b><br />{curto(d.valor)} · {numero(pct, 1)}% do total<br />{d.descricao}</>)} onMouseLeave={esconder}>
          <rect width={w} height={h} rx={6} />
          {w > 150 && h > 70 ? <>
            <text className="is-number" x={16} y={38}>{numero(pct)}%</text>
            <text className="is-name" x={16} y={64}>{d.nome}</text>
            {h > 110 && <text className="is-sub" x={16} y={88}>{curto(d.valor)} no ano</text>}
            {h > 150 && w > 300 && <text className="is-sub" x={16} y={h - 18}>{d.descricao}</text>}
          </> : w > 60 && h > 40 ? <>
            <text className="is-name" x={10} y={26}>{numero(pct)}%</text>
            {w > 90 && <text className="is-sub" x={10} y={46}>{d.nome.length * 7 > w - 16 ? d.nome.slice(0, Math.max(4, Math.floor((w - 16) / 7))) + "…" : d.nome}</text>}
          </> : null}
        </g>;
      })}
    </svg>
    {elemento}
  </div>;
}

// ——— Pictograma de 100 pessoas ———
export function Pessoas({ n, rotulo }: { n: number; rotulo: string }) {
  return <div className="viz-people" role="img" aria-label={rotulo}>
    {Array.from({ length: 100 }, (_, i) => <svg key={i} viewBox="0 0 10 20" aria-hidden="true" className={i < n ? "is-on" : undefined}><circle cx="5" cy="3.4" r="3" /><path d="M1 20 V11 a4 4 0 0 1 8 0 V20 Z" /></svg>)}
  </div>;
}

// ——— Linha mensal ———
export function LinhaMensal({ meses }: { meses: { mes: string; valor: number }[] }) {
  const [ref, W] = useLargura<HTMLDivElement>();
  const { mostrar, esconder, elemento } = useDica();
  if (meses.length < 2) return null;
  const H = 260, m = { l: 44, r: 52, t: 26, b: 28 };
  const maxv = Math.max(...meses.map(d => d.valor)) / 1e8;
  const passo = escalaPasso(maxv * 1.15), topo = Math.ceil(maxv * 1.15 / passo) * passo;
  const x = (i: number) => m.l + (W - m.l - m.r) * i / (meses.length - 1);
  const y = (c: number) => H - m.b - (H - m.b - m.t) * (c / 1e8) / topo;
  const linha = meses.map((d, i) => `${i ? "L" : "M"}${x(i)},${y(d.valor)}`).join(" ");
  const area = `${linha} L${x(meses.length - 1)},${y(0)} L${x(0)},${y(0)} Z`;
  const rot = (mes: string) => `${mes.slice(4)}/${mes.slice(2, 4)}`;
  const marcas = meses.map((d, i) => ({ d, i })).filter(({ d, i }) => i === 0 || i === meses.length - 1 || (d.mes.endsWith("01") && i > 2 && i < meses.length - 3));
  const fim = meses.at(-1)!;
  const ticks = Array.from({ length: Math.floor(topo / passo) + 1 }, (_, i) => i * passo);
  return <div className="viz-wrap" ref={ref}>
    <svg className="viz" width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img"
      aria-label={`Valor mensal de ${rot(meses[0].mes)} a ${rot(fim.mes)}, em milhões de reais. Último mês: ${curto(fim.valor)}.`}>
      <text x={m.l} y={10}>R$ milhões por mês</text>
      {ticks.map(t => <g key={t}><line className="viz-grid" x1={m.l} x2={W - m.r} y1={y(t * 1e8)} y2={y(t * 1e8)} /><text x={m.l - 8} y={y(t * 1e8) + 4} textAnchor="end">{numero(t, passo < 1 ? 1 : 0)}</text></g>)}
      <path d={area} className="viz-area" />
      <path d={linha} className="viz-line" />
      {meses.map((d, i) => <circle key={d.mes} cx={x(i)} cy={y(d.valor)} r={8} className="viz-hit" onMouseMove={ev => mostrar(ev, <><b>{rot(d.mes)}</b><br />{curto(d.valor)}</>)} onMouseLeave={esconder} />)}
      <circle className="viz-c1 is-ring" cx={x(meses.length - 1)} cy={y(fim.valor)} r={4.5} />
      <text className="is-value" x={x(meses.length - 1) + 8} y={y(fim.valor) - 10} textAnchor="end">{curto(fim.valor)}</text>
      {marcas.map(({ d, i }) => <text key={d.mes} x={x(i)} y={H - 8} textAnchor={i === 0 ? "start" : i === meses.length - 1 ? "end" : "middle"}>{rot(d.mes)}</text>)}
    </svg>
    {elemento}
  </div>;
}
