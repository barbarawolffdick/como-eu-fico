import { test, expect } from "./fixtures";
import { readFileSync } from "node:fs";
import { descobertasHome } from "../../lib/home";

test("descobertas regionais usam somas em municípios comparáveis e ranking usa a fonte", async () => {
  const data = await descobertasHome();
  const familias = JSON.parse(readFileSync("data/public/familias_mds.json", "utf8"));
  const municipios = JSON.parse(readFileSync("data/public/rankings_2026.json", "utf8")).registros;
  const pessoas = JSON.parse(readFileSync("data/public/pessoas_mds.json", "utf8"));
  const sul = municipios.filter((m: { uf: string }) => ["PR", "RS", "SC"].includes(m.uf));
  const [inicio, fim] = familias.periodos;
  const pares = sul.filter((m: { codigo_ibge: string }) => Number.isInteger(familias.registros[inicio][m.codigo_ibge]) && Number.isInteger(familias.registros[fim][m.codigo_ibge]));
  const antes = pares.reduce((sum: number, m: { codigo_ibge: string }) => sum + familias.registros[inicio][m.codigo_ibge], 0);
  const depois = pares.reduce((sum: number, m: { codigo_ibge: string }) => sum + familias.registros[fim][m.codigo_ibge], 0);
  expect(data.mudanca?.regioes.find(r => r.regiao === "Sul")).toMatchObject({ antes, depois, municipios: pares.length, total: sul.length, percentual: 100 * (depois - antes) / antes });
  expect(data.ranking?.cidades[0].percentual).toBe(Math.max(...Object.values(pessoas.registros).map(x => (x as { cobertura_pct: number }).cobertura_pct)));
});

test("entrada apresenta descobertas reais e links para investigar", async ({ page }, testInfo) => {
  const data = await descobertasHome();
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Como sua cidade vota.");
  const nav = page.getByRole("navigation", { name: "Navegação principal" });
  await expect(nav.getByRole("link", { name: "Minha cidade" })).toHaveAttribute("aria-current", "page");
  await expect(page.locator(".region-changes li")).toHaveCount(5);
  await expect(page.locator(".home-ranking-list li")).toHaveCount(5);
  await expect(page.locator(".home-ranking-list a").first()).toHaveAttribute("href", `/cidade/${data.ranking?.cidades[0].codigo_ibge}`);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: `test-results/home-revamp-${testInfo.project.name}.png`, fullPage: true });
  await page.getByRole("link", { name: "Investigar os dados e o contexto eleitoral" }).click();
  await expect(page).toHaveURL(/\/analises$/);
});

test("busca por teclado, troca de cidade e histórico preservam o município", async ({ page }) => {
  await page.goto("/");
  const search = page.getByRole("combobox", { name: "Encontre seu município" });
  await search.fill("3550308");
  await expect(page.getByRole("option")).toHaveCount(1);
  await search.press("ArrowDown");
  await search.press("Enter");
  await expect(page).toHaveURL(/\/cidade\/3550308$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("São Paulo — SP");
  const change = page.getByRole("combobox", { name: "Trocar de cidade" });
  await change.fill("3304557");
  await page.getByRole("option").click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Rio de Janeiro — RJ");
  await page.goBack();
  await expect(page).toHaveURL(/\/cidade\/3550308$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("São Paulo — SP");
});

test("links antigos abrem a cidade e os temas seguem a ordem do conteúdo", async ({ page }, testInfo) => {
  await page.goto("/?municipio=1504752");
  await expect(page).toHaveURL(/\/cidade\/1504752$/);
  await expect(page.getByRole("heading", { name: /^Quanto dinheiro federal chegou à cidade em \d{4}\?$/ })).toBeVisible();
  await expect(page.locator("#quanto")).not.toContainText("Calculando");
  await page.locator("#quanto").screenshot({ path: `test-results/quanto-chega-${testInfo.project.name}.png` });
  const links = page.getByRole("navigation", { name: "Indicadores da cidade" });
  for (const name of ["Quanto chega", "Para quem", "Como mudou", "Comparação", "Voto", "Saúde", "Bolsa Família", "Fontes"]) {
    const link = links.getByRole("link", { name, exact: true });
    const href = await link.getAttribute("href");
    await link.click();
    await expect(page.locator(href!)).toBeInViewport();
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("placar preserva empate e indisponibilidade eleitoral", async ({ page }) => {
  const detalhes = JSON.parse(readFileSync("data/public/detalhes_2026.json", "utf8"));
  const original = detalhes.registros["3550308"];
  await page.route("**/api/municipios/3550308", route => route.fulfill({ json: {
    ...original, eleitoral_disponivel: true, votos_presidenciais: [{ candidato: "13", votos: 100 }, { candidato: "22", votos: 100 }],
  } }));
  await page.goto("/cidade/3550308");
  const cabecalho = page.locator(".city-heading");
  const voto = page.locator("#voto");
  await voto.getByText("Ver todos os candidatos").click();
  // Empate: o cabeçalho não aponta vencedor e a lista mostra os dois com 50%.
  await expect(voto.locator(".vote")).toHaveCount(2);
  await expect(voto.locator(".vote").first()).toContainText("50%");
  await expect(voto.locator(".vote").last()).toContainText("50%");
  await expect(cabecalho).not.toContainText("dos votos no 1º turno");
  await page.unroute("**/api/municipios/3550308");
  await page.route("**/api/municipios/3550308", route => route.fulfill({ json: { ...original, eleitoral_disponivel: false } }));
  await page.reload();
  await expect(voto).toContainText("Dados eleitorais indisponíveis.");
  await expect(voto.locator(".vote")).toHaveCount(0);
  await expect(cabecalho).not.toContainText("dos votos no 1º turno");
  await expect(voto).not.toContainText("0 votos");
});

test("falha municipal permite nova tentativa e cidade inexistente não fica carregando", async ({ page }) => {
  await page.route("**/api/municipios/3550308", route => route.abort());
  await page.goto("/cidade/3550308");
  await expect(page.locator("main").getByRole("alert")).toContainText("Não foi possível consultar esta cidade");
  await page.unroute("**/api/municipios/3550308");
  await page.getByRole("button", { name: "Tentar novamente" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("São Paulo — SP");
  await page.goto("/cidade/9999999");
  await expect(page.locator("main").getByRole("alert")).toBeVisible();
  await expect(page.getByText("Consultando dados do município…")).toHaveCount(0);
});

test("busca ignora acentos e prioriza o nome exato", async ({ request }) => {
  const nomes = async (q: string) => (await (await request.get("/api/municipios?limit=3&q=" + encodeURIComponent(q))).json() as { nome: string; uf: string }[]).map(x => `${x.nome}/${x.uf}`);
  expect((await nomes("sao paulo"))[0]).toBe("São Paulo/SP");
  expect(await nomes("SÃO PAULO")).toEqual(await nomes("sao paulo"));
  expect((await nomes("brasilia"))[0]).toBe("Brasília/DF");
  expect((await nomes("natal"))[0]).toBe("Natal/RN");
  expect(await nomes("3550308")).toEqual(["São Paulo/SP"]);
});
