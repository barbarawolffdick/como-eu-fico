import { test, expect } from "./fixtures";
import { derivarDinheiroFederal as derivar } from "../../scripts/derivar_dinheiro_federal.mjs";
import type { DinheiroFederalCidade, PibReferencia, PontoRegiao } from "../../lib/dinheiro-federal";

const derivarDinheiroFederal = (dados: unknown) => derivar(dados as Parameters<typeof derivar>[0]) as unknown as
  { cidades: Record<string, DinheiroFederalCidade>; regioes: PontoRegiao[]; pib: PibReferencia };

// Amostra mínima: três cidades na mesma região imediata, uma em outra região, ano 2025.
const meses = (valor: number) => Array.from({ length: 12 }, (_, i) => ({ mes_competencia: `2025${String(i + 1).padStart(2, "0")}`, valor_centavos: valor }));
const cidade = (codigo: string, nome: string, uf: string, rid: string, regiao: string, pib: number | null, inss: number | null, fpm: number | null, qtd: number) => [codigo, {
  municipio: { codigo_ibge: codigo, nome, uf }, regiao_imediata: { id: rid, nome: "R" + rid }, regiao, pib_centavos: pib,
  inss: inss == null ? null : { valor_ano_centavos: { total: inss }, quantidade_dezembro: { total: qtd } },
  fpm: fpm == null ? null : { valor_ano_centavos: fpm }, ausencias: fpm == null ? { fpm: "sem FPM" } : {},
}] as const;
const amostra = () => ({
  dinheiro: { ano: 2025, pib: { ano_fonte: 2023, estimado: true }, municipios_referencia: 4, registros: Object.fromEntries([
    cidade("2300001", "Polo", "CE", "230001", "Nordeste", 1000, 200, 20, 400),
    cidade("2300002", "Vizinha", "CE", "230001", "Nordeste", 100, 10, 30, 2),
    cidade("2300003", "Sem FPM", "CE", "230001", "Nordeste", 100, 50, null, 30),
    cidade("3500001", "Sul", "SP", "350001", "Sudeste", 1000, 50, 10, 150),
  ]) },
  detalhes: { registros: {
    "2300001": { bolsa_familia: meses(1), eleitoral_disponivel: true, votos_presidenciais: [{ candidato: "13", votos: 70 }, { candidato: "22", votos: 30 }] },
    "2300002": { bolsa_familia: meses(1).slice(0, 11), eleitoral_disponivel: true, votos_presidenciais: [{ candidato: "13", votos: 80 }, { candidato: "22", votos: 20 }] },
    "2300003": { bolsa_familia: meses(1), eleitoral_disponivel: false, votos_presidenciais: [] },
    "3500001": { bolsa_familia: meses(1), eleitoral_disponivel: true, votos_presidenciais: [{ candidato: "13", votos: 30 }, { candidato: "22", votos: 70 }] },
  } },
  financiamento: { registros: Object.fromEntries(["2300001", "2300002", "2300003", "3500001"].map(c => [c, { fns: [{ ano: 2025, completo: true, municipal: { valor_centavos: 5 } }] }])) },
  rankings: { registros: [{ codigo_ibge: "2300001", populacao: 1000 }, { codigo_ibge: "2300002", populacao: 1000 }, { codigo_ibge: "2300003", populacao: 1000 }, { codigo_ibge: "3500001", populacao: 1000 }] },
});

test("derivação junta fluxos do mesmo ano sem transformar ausência em zero", () => {
  const { cidades } = derivarDinheiroFederal(amostra());
  expect(cidades["2300001"].fluxos).toEqual({ inss: 200, bolsa_familia: 12, fpm: 20, sus: 5 });
  // Onze competências não fecham o ano: Bolsa Família fica nulo, com motivo.
  expect(cidades["2300002"].fluxos.bolsa_familia).toBeNull();
  expect(cidades["2300002"].ausencias.bolsa_familia).toContain("12 competências");
  expect(cidades["2300003"].fluxos.fpm).toBeNull();
  expect(cidades["2300003"].ausencias.fpm).toBe("sem FPM");
});

test("vizinhos excluem a própria cidade e cada fluxo usa o PIB de quem tem o fluxo", () => {
  const { cidades } = derivarDinheiroFederal(amostra());
  const [propria, regiao, vizinhos, estado] = cidades["2300001"].comparacoes;
  expect(propria.nome).toBe("Polo");
  expect(regiao.municipios).toBe(3);
  expect(vizinhos.nome).toBe("As 2 cidades vizinhas");
  expect(vizinhos.municipios).toBe(2);
  // FPM da região: só Polo e Vizinha têm FPM → (20 + 30) / (1000 + 100).
  expect(regiao.percentual_do_pib.fpm).toBeCloseTo(100 * 50 / 1100, 6);
  // INSS da região inclui a cidade sem FPM → (200 + 10 + 50) / 1200.
  expect(regiao.percentual_do_pib.inss).toBeCloseTo(100 * 260 / 1200, 6);
  expect(estado.nome).toBe("Ceará");
});

test("órgão pagador atípico é sinalizado pelos benefícios por 100 habitantes", () => {
  const { cidades } = derivarDinheiroFederal(amostra());
  expect(cidades["2300001"].inss_orgao_pagador_atipico).toBe(false);   // 40 por 100: no limite
  expect(cidades["2300002"].inss_orgao_pagador_atipico).toBe(true);    // 0,2 por 100
  expect(cidades["3500001"].inss_orgao_pagador_atipico).toBe(false);   // 15 por 100
});

test("pontos por região só existem com os quatro fluxos e votos válidos", () => {
  const { regioes, pib } = derivarDinheiroFederal(amostra());
  expect(pib.estimado).toBe(true);
  // A região 230001 tem Bolsa Família ausente em uma cidade, mas o fluxo agregado existe nas demais.
  expect(regioes.map(r => r.id).sort()).toEqual(["230001", "350001"]);
  const ce = regioes.find(r => r.id === "230001")!;
  expect(ce.lula_percentual).toBeCloseTo(75, 6); // (70 + 80) / 200; a cidade sem dado eleitoral não entra
});

test("API do dinheiro federal valida código e declara ausências com motivo", async ({ request }) => {
  expect((await request.get("/api/dinheiro-federal/123")).status()).toBe(400);
  expect((await request.get("/api/dinheiro-federal/9999999")).status()).toBe(404);
  const noronha = await (await request.get("/api/dinheiro-federal/2605459")).json();
  expect(noronha.cidade.fluxos.fpm).toBeNull();
  expect(noronha.cidade.ausencias.fpm).toBeTruthy();
  const nova = await (await request.get("/api/dinheiro-federal/5101837")).json();
  expect(nova.cidade.pib_centavos).toBeNull();
  expect(nova.cidade.ausencias.pib).toBeTruthy();
  expect(typeof nova.ano).toBe("number");
  expect(typeof nova.pib.estimado).toBe("boolean");
});

test("página mostra estimativa, nota do órgão pagador e não apresenta total parcial como completo", async ({ page, request }) => {
  const real = await (await request.get("/api/dinheiro-federal/2307304")).json();
  const resposta = { ...real, pib: { ano_fonte: 2023, estimado: true }, cidade: { ...real.cidade,
    pib_centavos: real.cidade.pib_centavos ?? 1_000_000_000_00,
    fluxos: { inss: 800_000_000_00, bolsa_familia: 200_000_000_00, fpm: 150_000_000_00, sus: null },
    ausencias: { sus: "Sem repasse federal ao fundo municipal de saúde validado." } } };
  await page.route("**/api/dinheiro-federal/2307304", route => route.fulfill({ json: resposta }));
  await page.goto("/cidade/2307304");
  const quanto = page.locator("#quanto");
  await expect(quanto).toContainText("(estimativa)");
  await expect(quanto).toContainText("SUS não tem dado");
  await expect(quanto).toContainText("Indisponível. Sem repasse federal ao fundo municipal de saúde validado.");
  await expect(page.locator("#para-quem")).toContainText("contados na cidade");
  await expect(page.locator("#compara")).toContainText("Comparação feita com INSS, Bolsa Família e FPM");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("cidade com órgão pagador atípico mostra o aviso e o número da região", async ({ page, request }) => {
  const api = await (await request.get("/api/dinheiro-federal/2111631")).json();
  test.skip(!api.cidade.inss_orgao_pagador_atipico, "Cidade deixou de ser atípica nesta publicação");
  await page.goto("/cidade/2111631");
  const aviso = page.locator("#para-quem").getByRole("note").filter({ hasText: "por 100 habitantes" });
  await expect(aviso).toContainText("muito abaixo do comum");
  await expect(aviso).toContainText(`Na região de ${api.cidade.regiao_imediata.nome}`);
});

test("dispersão destaca a região da cidade e trata falta de dados", async ({ page }) => {
  const pontos = { ano: 2025, pib: { ano_fonte: 2023, estimado: true }, correlacao: { brasil: 0.8, nordeste: 0.6, demais: 0.7 }, regioes: [
    { id: "230011", nome: "Juazeiro do Norte", uf: "CE", regiao: "Nordeste", federal_percentual_do_pib: 34, lula_percentual: 73 },
    { id: "350001", nome: "São Paulo", uf: "SP", regiao: "Sudeste", federal_percentual_do_pib: 5, lula_percentual: 35 },
    { id: "290001", nome: "Salvador", uf: "BA", regiao: "Nordeste", federal_percentual_do_pib: 20, lula_percentual: 70 },
  ] };
  await page.route("**/api/dinheiro-federal/regioes", route => route.fulfill({ json: pontos }));
  await page.goto("/cidade/2307304");
  const grafico = page.locator(".federal-scatter");
  await expect(grafico).toHaveAttribute("aria-label", /Região de Juazeiro do Norte: 34,0% e 73,0%/);
  await expect(grafico.locator("circle.is-current")).toHaveCount(1);
  await expect(grafico.locator("circle.is-ne, circle.is-out")).toHaveCount(2);
  await expect(page.locator("#voto")).toContainText("não entre pessoas");
  await page.unroute("**/api/dinheiro-federal/regioes");
  await page.route("**/api/dinheiro-federal/regioes", route => route.fulfill({ json: { ...pontos, regioes: [] } }));
  await page.reload();
  await expect(page.locator("#voto")).toContainText("ainda não está disponível");
  await expect(page.locator(".federal-scatter")).toHaveCount(0);
});

test("série é convertida para reais do último ano pelo IPCA médio", () => {
  const serie = { anos: ["2023", "2025"], ipca_medio_anual: { "2023": 100, "2025": 110 },
    situacao: { "2023": { inss: "completo", fpm: "incompleto: 03" }, "2025": { inss: "completo", fpm: "completo" } },
    registros: { "2300001": { inss: { "2023": 1000, "2025": 1200 }, fpm: { "2023": null, "2025": 50 } } } };
  const { cidades } = derivarDinheiroFederal({ ...amostra(), serie });
  const s = cidades["2300001"].serie!;
  expect(s.base_inflacao).toBe("2025");
  expect(s.inss["2023"]).toEqual({ nominal: 1000, real: 1100, motivo: null });
  expect(s.fpm["2023"]).toEqual({ nominal: null, real: null, motivo: "incompleto: 03" });
  expect(cidades["3500001"].serie).toBeNull();
});

test("como mudou mostra lacunas como s/d e descreve a variação real", async ({ page, request }) => {
  const real = await (await request.get("/api/dinheiro-federal/2307304")).json();
  const ponto = (nominal: number | null, realValor: number | null) => ({ nominal, real: realValor, motivo: realValor == null ? "incompleto" : null });
  const serie = { anos: ["2023", "2024", "2025"], base_inflacao: "2025",
    inss: { "2023": ponto(800, 1000_00000000), "2024": ponto(900, 1010_00000000), "2025": ponto(1000, 1005_00000000) },
    fpm: { "2023": ponto(100, 200_00000000), "2024": ponto(null, null), "2025": ponto(120, 150_00000000) } };
  await page.route("**/api/dinheiro-federal/2307304", route => route.fulfill({ json: { ...real, cidade: { ...real.cidade, serie } } }));
  await page.goto("/cidade/2307304");
  const mudou = page.locator("#mudou");
  await expect(mudou).toContainText("ficou estável de 2023 a 2025");
  await expect(mudou).toContainText("o FPM caiu 25% de 2023 a 2025");
  await expect(mudou.locator("svg text.is-gap")).toHaveCount(1);
  await expect(mudou.locator("svg")).toHaveAttribute("aria-label", /FPM: 2023 200, 2024 sem dado completo, 2025 150/);
});
