// Gera derivados de leitura rápida a partir dos snapshots canônicos de data/public.
// Os snapshots continuam sendo a única fonte; os derivados são reconstruídos a cada
// build (npm run build / npm run dev) e não são versionados.
//
// - fragmentos por UF (dois primeiros dígitos do código IBGE) dos arquivos por cidade;
// - índice de busca com nomes normalizados (sem acentos);
// - projeção enxuta do financiamento usada pela exploração nacional;
// - dinheiro federal por cidade (fragmentado por UF) e por região imediata (scripts/derivar_dinheiro_federal.mjs);
// - emendas parlamentares do ano mais recente, por UF;
// - manifesto com SHA-256 e metadados (tudo exceto `registros`) de cada snapshot.
import { createHash } from "node:crypto";
import { mkdir, readdir, readFile, rename, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { derivarDinheiroFederal } from "./derivar_dinheiro_federal.mjs";

const raiz = process.cwd();
const origem = join(raiz, "data/public");
const destinoFinal = join(raiz, "data/derivados");
const destino = destinoFinal + ".tmp";
const snapshots = ["rankings_2026.json", "detalhes_2026.json", "familias_mds.json", "pessoas_mds.json",
  "saude_municipal.json", "financiamento_saude.json", "pessoas_mds_mensal.json"];
// Um arquivo por ano (dinheiro_federal.json, dinheiro_federal_2025.json...); a página usa o ano mais recente.
const federais = (await readdir(origem)).filter(f => /^dinheiro_federal(_\d{4})?\.json$/.test(f)).sort();
const emendas = (await readdir(origem)).filter(f => /^emendas_\d{4}\.json$/.test(f)).sort();
const serieFederal = (await readdir(origem)).includes("dinheiro_federal_serie.json") ? ["dinheiro_federal_serie.json"] : [];
const fragmentados = { "detalhes_2026.json": "municipios", "saude_municipal.json": "municipios_referencia", "financiamento_saude.json": "municipios" };

const falha = mensagem => { throw Error("fragmentar_snapshots: " + mensagem); };
const normalizar = texto => texto.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLocaleLowerCase("pt-BR");

async function gravar(caminho, dados) {
  await mkdir(join(caminho, ".."), { recursive: true });
  await writeFile(caminho, JSON.stringify(dados));
}

await rm(destino, { recursive: true, force: true });
const manifesto = { esquema: 1, gerado_em: new Date().toISOString(), snapshots: {} };
const carregados = {};
for (const arquivo of [...snapshots, ...federais, ...serieFederal, ...emendas]) {
  const bytes = await readFile(join(origem, arquivo));
  const dados = JSON.parse(bytes.toString("utf8"));
  const { registros, ...metadados } = dados;
  manifesto.snapshots[arquivo] = { sha256: createHash("sha256").update(bytes).digest("hex"), bytes: bytes.length, metadados };
  carregados[arquivo] = dados;
}

for (const [arquivo, campoTotal] of Object.entries(fragmentados)) {
  const dados = carregados[arquivo];
  const nome = arquivo.replace(/\.json$/, "");
  const porUf = {};
  for (const [codigo, registro] of Object.entries(dados.registros)) {
    if (!/^\d{7}$/.test(codigo)) falha(`${arquivo}: código inválido ${codigo}`);
    (porUf[codigo.slice(0, 2)] ??= {})[codigo] = registro;
  }
  const total = Object.values(porUf).reduce((soma, registros) => soma + Object.keys(registros).length, 0);
  if (total !== Object.keys(dados.registros).length || total !== dados[campoTotal]) falha(`${arquivo}: ${total} registros fragmentados, esperado ${dados[campoTotal]}`);
  for (const [uf, registros] of Object.entries(porUf)) await gravar(join(destino, nome, uf + ".json"), { registros });
  manifesto.snapshots[arquivo].fragmentos = Object.keys(porUf).sort();
}

// Mesmo universo e campos que /api/municipios já devolvia, ordenado como antes.
const busca = Object.values(carregados["detalhes_2026.json"].registros)
  .map(({ municipio: { codigo_ibge, nome, uf, populacao, ano_populacao } }) => ({ codigo_ibge, nome, uf, populacao, ano_populacao, chave: normalizar(nome ?? "") }))
  .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
await gravar(join(destino, "busca_municipios.json"), busca);

// Somente os campos lidos por lib/explorar-dados.ts; valores copiados sem recalcular.
const financiamento = carregados["financiamento_saude.json"];
await gravar(join(destino, "explorar_saude.json"), { registros: Object.fromEntries(Object.entries(financiamento.registros).map(([codigo, r]) => [codigo, {
  municipio: { ano_populacao: r.municipio.ano_populacao },
  fns: r.fns.map(({ ano, inicio, fim, completo, municipal }) => ({ ano, inicio, fim, completo, municipal: municipal && { valor_centavos: municipal.valor_centavos } })),
  variacao_anual_2024_2025_percentual: r.variacao_anual_2024_2025_percentual,
  centavos_por_habitante: r.centavos_por_habitante,
}])) });

const federalAtual = federais.reduce((a, b) => (carregados[b].ano > carregados[a].ano ? b : a));
manifesto.dinheiro_federal_atual = federalAtual;
const federal = derivarDinheiroFederal({ dinheiro: carregados[federalAtual], detalhes: carregados["detalhes_2026.json"],
  financiamento, rankings: carregados["rankings_2026.json"], serie: carregados["dinheiro_federal_serie.json"] ?? null });
const federalPorUf = {};
for (const [codigo, registro] of Object.entries(federal.cidades)) (federalPorUf[codigo.slice(0, 2)] ??= {})[codigo] = registro;
if (Object.keys(federal.cidades).length !== carregados[federalAtual].municipios_referencia) falha("dinheiro federal: cobertura incompleta");
for (const [uf, registros] of Object.entries(federalPorUf)) await gravar(join(destino, "dinheiro_federal", uf + ".json"), { registros });
manifesto.snapshots[federalAtual].fragmentos = Object.keys(federalPorUf).sort();
await gravar(join(destino, "dinheiro_federal_regioes.json"), { ano: federal.ano, pib: federal.pib, regioes: federal.regioes, correlacao: federal.correlacao, enxame: federal.enxame });

// Emendas: só o ano mais recente, fragmentado por UF. Cidade sem registro = nenhuma emenda paga no ano.
if (emendas.length) {
  const atual = emendas.at(-1), dados = carregados[atual];
  if (dados.esquema !== 1) falha(`${atual}: esquema inesperado`);
  const porUf = {};
  for (const [codigo, registro] of Object.entries(dados.registros)) {
    if (!federal.cidades[codigo]) falha(`${atual}: código fora do cadastro ${codigo}`);
    (porUf[codigo.slice(0, 2)] ??= {})[codigo] = registro;
  }
  if (Object.keys(dados.registros).length !== dados.municipios_com_emendas) falha(`${atual}: contagem de municípios divergente`);
  for (const uf of Object.keys(federalPorUf)) await gravar(join(destino, "emendas", uf + ".json"), { registros: porUf[uf] ?? {} });
  manifesto.snapshots[atual].fragmentos = Object.keys(federalPorUf).sort();
  manifesto.emendas_atual = atual;
}

await gravar(join(destino, "manifesto.json"), manifesto);
await rm(destinoFinal, { recursive: true, force: true });
await rename(destino, destinoFinal);
console.log(`Derivados gerados em data/derivados: ${busca.length} municípios, ${manifesto.snapshots["detalhes_2026.json"].fragmentos.length} UFs.`);
