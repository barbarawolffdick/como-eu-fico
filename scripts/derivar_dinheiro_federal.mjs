// Relaciona, em código, os fluxos federais de um mesmo ano por município (domínios independentes):
// INSS, FPM e PIB de dinheiro_federal.json; Bolsa Família de detalhes_2026.json (CGU, soma das
// 12 competências do ano); SUS de financiamento_saude.json (FNS, ano completo, fundo municipal).
// Também calcula comparações territoriais e os pontos por região imediata (fluxos × voto).
// Ausência fica nula com motivo, nunca zero.

const FLUXOS = ["inss", "bolsa_familia", "fpm", "sus"];
// Benefícios do INSS emitidos em dezembro por 100 habitantes fora desta faixa indicam deslocamento
// para o município do órgão pagador (ver research/avaliacao-inss-beneficios-municipios.md).
const INSS_POR_100_MIN = 5, INSS_POR_100_MAX = 40;
const ESTADOS = { AC: "Acre", AL: "Alagoas", AP: "Amapá", AM: "Amazonas", BA: "Bahia", CE: "Ceará", DF: "Distrito Federal",
  ES: "Espírito Santo", GO: "Goiás", MA: "Maranhão", MT: "Mato Grosso", MS: "Mato Grosso do Sul", MG: "Minas Gerais", PA: "Pará",
  PB: "Paraíba", PR: "Paraná", PE: "Pernambuco", PI: "Piauí", RJ: "Rio de Janeiro", RN: "Rio Grande do Norte", RS: "Rio Grande do Sul",
  RO: "Rondônia", RR: "Roraima", SC: "Santa Catarina", SP: "São Paulo", SE: "Sergipe", TO: "Tocantins" };

function fluxosDaCidade(codigo, r, ano, detalhes, financiamento) {
  const ausencias = { ...r.ausencias };
  const meses = (detalhes.registros[codigo]?.bolsa_familia ?? []).filter(m => m.mes_competencia.startsWith(String(ano)));
  const bolsa = meses.length === 12 && meses.every(m => Number.isSafeInteger(m.valor_centavos))
    ? meses.reduce((s, m) => s + m.valor_centavos, 0) : null;
  if (bolsa === null) ausencias.bolsa_familia = `A base da CGU não traz as 12 competências de ${ano} para esta cidade.`;
  const fns = financiamento.registros[codigo]?.fns.find(f => f.ano === ano && f.completo);
  const sus = fns?.municipal?.valor_centavos ?? null;
  if (sus === null) ausencias.sus = `Sem repasse federal ao fundo municipal de saúde validado para ${ano} completo.`;
  return {
    fluxos: { inss: r.inss?.valor_ano_centavos.total ?? null, bolsa_familia: bolsa, fpm: r.fpm?.valor_ano_centavos ?? null, sus },
    ausencias,
  };
}

function somar(grupo, codigos, cidades) {
  for (const c of codigos) {
    const x = cidades[c];
    grupo.municipios++;
    if (x.pib_centavos == null) continue;
    for (const f of FLUXOS) {
      if (x.fluxos[f] == null) continue;
      grupo.fluxo[f] += x.fluxos[f];
      grupo.pib[f] += x.pib_centavos;
    }
  }
  return grupo;
}
const vazio = () => ({ municipios: 0, fluxo: Object.fromEntries(FLUXOS.map(f => [f, 0])), pib: Object.fromEntries(FLUXOS.map(f => [f, 0])) });

// Cada fluxo é dividido pelo PIB dos municípios que têm esse fluxo; o total só existe se os quatro existirem.
function percentuais(grupo, nome, detalhe) {
  const pct = Object.fromEntries(FLUXOS.map(f => [f, grupo.pib[f] > 0 ? 100 * grupo.fluxo[f] / grupo.pib[f] : null]));
  const total = FLUXOS.every(f => pct[f] !== null) ? FLUXOS.reduce((s, f) => s + pct[f], 0) : null;
  return { nome, detalhe, municipios: grupo.municipios, percentual_do_pib: pct, total };
}

export function derivarDinheiroFederal({ dinheiro, detalhes, financiamento, rankings }) {
  const ano = dinheiro.ano;
  const pib = dinheiro.pib ?? { ano_fonte: ano, estimado: false };
  const populacao = Object.fromEntries(rankings.registros.map(r => [r.codigo_ibge, r.populacao]));
  const cidades = {};
  for (const [codigo, r] of Object.entries(dinheiro.registros)) {
    const { fluxos, ausencias } = fluxosDaCidade(codigo, r, ano, detalhes, financiamento);
    const qtd = r.inss?.quantidade_dezembro?.total ?? null;
    const pop = populacao[codigo] ?? null;
    const por100 = qtd != null && pop ? 100 * qtd / pop : null;
    cidades[codigo] = {
      municipio: r.municipio, regiao_imediata: r.regiao_imediata, regiao: r.regiao, populacao: pop,
      pib_centavos: r.pib_centavos, fluxos, ausencias,
      inss_detalhe: r.inss?.valor_ano_centavos ?? null, inss_quantidade_dezembro: r.inss?.quantidade_dezembro ?? null,
      inss_beneficios_por_100_habitantes: por100,
      inss_orgao_pagador_atipico: por100 !== null && (por100 < INSS_POR_100_MIN || por100 > INSS_POR_100_MAX),
    };
  }

  const por = chave => {
    const g = new Map();
    for (const c in cidades) { const k = chave(cidades[c]); if (!g.has(k)) g.set(k, []); g.get(k).push(c); }
    return g;
  };
  const regioesImediatas = por(x => x.regiao_imediata.id), ufs = por(x => x.municipio.uf), macro = por(x => x.regiao);
  const somaRegiao = new Map([...regioesImediatas].map(([k, cs]) => [k, somar(vazio(), cs, cidades)]));
  const somaUf = new Map([...ufs].map(([k, cs]) => [k, somar(vazio(), cs, cidades)]));
  const somaMacro = new Map([...macro].map(([k, cs]) => [k, somar(vazio(), cs, cidades)]));
  const brasil = percentuais(somar(vazio(), Object.keys(cidades), cidades), "Brasil", "");

  for (const [codigo, x] of Object.entries(cidades)) {
    const rid = x.regiao_imediata.id;
    const membros = regioesImediatas.get(rid);
    const vizinhos = membros.filter(c => c !== codigo);
    x.comparacoes = [
      percentuais(somar(vazio(), [codigo], cidades), x.municipio.nome, ""),
      percentuais(somaRegiao.get(rid), `Região de ${x.regiao_imediata.nome}`, `${membros.length} cidades, incluindo ${x.municipio.nome} (IBGE)`),
      ...(vizinhos.length ? [percentuais(somar(vazio(), vizinhos, cidades), `As ${vizinhos.length} cidades vizinhas`, `sem ${x.municipio.nome}`)] : []),
      percentuais(somaUf.get(x.municipio.uf), ESTADOS[x.municipio.uf] ?? x.municipio.uf, ""),
      percentuais(somaMacro.get(x.regiao), x.regiao, ""),
      brasil,
    ];
  }

  // Regiões imediatas: total federal / PIB × votos em Lula (13) sobre votos nos candidatos.
  const regioes = [];
  for (const [rid, cs] of regioesImediatas) {
    const g = percentuais(somaRegiao.get(rid), cidades[cs[0]].regiao_imediata.nome, "");
    let v13 = 0, vt = 0;
    for (const c of cs) {
      const d = detalhes.registros[c];
      if (!d?.eleitoral_disponivel) continue;
      for (const v of d.votos_presidenciais) { vt += v.votos; if (v.candidato === "13") v13 += v.votos; }
    }
    if (g.total === null || vt === 0) continue;
    regioes.push({ id: rid, nome: g.nome, uf: cidades[cs[0]].municipio.uf, regiao: cidades[cs[0]].regiao,
      federal_percentual_do_pib: g.total, lula_percentual: 100 * v13 / vt });
  }
  regioes.sort((a, b) => a.id.localeCompare(b.id));
  return { ano, pib, cidades, regioes, correlacao: correlacao(regioes) };
}

function correlacao(pontos) {
  const r = ps => {
    const n = ps.length; if (n < 3) return null;
    const mx = ps.reduce((s, p) => s + p.federal_percentual_do_pib, 0) / n, my = ps.reduce((s, p) => s + p.lula_percentual, 0) / n;
    let sxy = 0, sxx = 0, syy = 0;
    for (const p of ps) { const dx = p.federal_percentual_do_pib - mx, dy = p.lula_percentual - my; sxy += dx * dy; sxx += dx * dx; syy += dy * dy; }
    return sxy / Math.sqrt(sxx * syy);
  };
  return { brasil: r(pontos), nordeste: r(pontos.filter(p => p.regiao === "Nordeste")), demais: r(pontos.filter(p => p.regiao !== "Nordeste")) };
}
