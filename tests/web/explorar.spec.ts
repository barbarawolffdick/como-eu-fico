import { test, expect } from "./fixtures";
import { readFileSync } from "node:fs";
import { filtrosIniciais, filtrarOrdenarExploracao, lerFiltros, type RegistroExplorar } from "../../lib/explorar";

const territory = JSON.parse(readFileSync("data/public/rankings_2026.json", "utf8")).registros;
const people = JSON.parse(readFileSync("data/public/pessoas_mds.json", "utf8"));
const financial = JSON.parse(readFileSync("data/public/financiamento_saude.json", "utf8")).registros;

test("filtros rejeitam recortes incompatíveis e preservam empates, zeros e valores negativos", () => {
  expect(() => lerFiltros(new URLSearchParams("regiao=Sul&uf=BA"))).toThrow();
  expect(() => lerFiltros(new URLSearchParams("metrica=__proto__"))).toThrow();
  expect(() => lerFiltros(new URLSearchParams("uf=ZZ"))).toThrow();
  const base = { ...territory[0], percentual_vencedor: 50 };
  const rows: RegistroExplorar[] = [{ ...base, codigo_ibge: "1000001", empatados: 2, valor: 0 }, { ...base, codigo_ibge: "1000002", valor: -5 }, { ...base, codigo_ibge: "1000003", valor: 2 }];
  expect(filtrarOrdenarExploracao(rows, filtrosIniciais)).toHaveLength(3);
  expect(filtrarOrdenarExploracao(rows, { ...filtrosIniciais, vencedor: "empate" })[0].valor).toBe(0);
  expect(filtrarOrdenarExploracao(rows, { ...filtrosIniciais, ordem: "asc" })[0].valor).toBe(-5);
});

test("API usa valores publicados, universo completo e páginas sem duplicatas", async ({ request }) => {
  const response = await request.get("/api/explorar");
  expect(response.ok()).toBe(true);
  const result = await response.json();
  expect(result.recorte).toBe(5571);
  expect(result.com_dado).toBe(5571);
  expect(result.resultados[0].valor).toBe(Math.max(...Object.values(people.registros).map(item => (item as { cobertura_pct: number }).cobertura_pct)));
  expect(result.resultados[0].nome).toBe("Itaubal");
  const next = await (await request.get("/api/explorar?pagina=2")).json();
  expect(next.resultados.every((city: { codigo_ibge: string }) => !result.resultados.some((old: { codigo_ibge: string }) => old.codigo_ibge === city.codigo_ibge))).toBe(true);
  const ties = await (await request.get("/api/explorar?vencedor=empate")).json();
  expect(ties.recorte).toBe(2);
  expect(ties.resultados.every((city: { empatados: number }) => city.empatados === 2)).toBe(true);
  expect((await request.get("/api/explorar?regiao=Sul&uf=BA")).status()).toBe(422);
});

test("saúde mantém período, destinatário municipal e evolução de anos completos", async ({ request }) => {
  const total = await (await request.get("/api/explorar?metrica=saude_total&uf=SP")).json();
  expect(total.periodo).toContain("01/2026 a 07/2026");
  for (const city of total.resultados) expect(city.valor).toBe(financial[city.codigo_ibge].fns.at(-1).municipal.valor_centavos);
  const df = await (await request.get("/api/explorar?metrica=saude_total&uf=DF")).json();
  expect(df.com_dado).toBe(0);
  expect(df.sem_dado).toBe(1);
  const change = await (await request.get("/api/explorar?metrica=saude_variacao&ordem=asc")).json();
  expect(change.periodo).toContain("2024 → 2025");
  expect(change.resultados[0].valor).toBeLessThan(0);
  for (const city of change.resultados) expect(city.valor).toBe(financial[city.codigo_ibge].variacao_anual_2024_2025_percentual);
});

test("entrada apresenta temas, território, cobertura e lista legível", async ({ page }, testInfo) => {
  await page.goto("/explorar");
  await expect(page.getByRole("heading", { name: "Explore os municípios brasileiros" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Bolsa Família Alcance e valores registrados" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".explore-results>li")).toHaveCount(10);
  await expect(page.locator(".explore-statistics")).toContainText("5.571");
  await expect(page.locator(".explore-reference")).toContainText("09/2026");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: `test-results/explorar-${testInfo.project.name}.png`, fullPage: true });
});

test("região, estado, paginação e histórico preservam a exploração", async ({ page }) => {
  await page.goto("/explorar");
  await page.getByRole("button", { name: "Nordeste", exact: true }).click();
  await page.getByRole("combobox", { name: "Estado (UF)", exact: true }).selectOption("BA");
  await expect(page).toHaveURL(/uf=BA/);
  await expect(page.locator(".explore-results>li")).toHaveCount(10);
  for (const city of await page.locator(".explore-city>a").all()) await expect(city).toContainText("— BA");
  await page.getByRole("button", { name: "Próxima página", exact: true }).click();
  await expect(page).toHaveURL(/pagina=2/);
  await expect(page.locator(".explore-position").first()).toHaveText("11");
  await page.reload();
  await expect(page.getByRole("combobox", { name: "Estado (UF)" })).toHaveValue("BA");
  await page.goBack();
  await expect(page).toHaveURL(/pagina=1/);
  await page.getByRole("button", { name: "Sul", exact: true }).click();
  await expect(page.getByRole("combobox", { name: "Estado (UF)" })).toHaveValue("");
  await expect(page.locator(".explore-ranking-heading")).toContainText("Sul");
});

test("temas de saúde e voto mostram indicadores próprios", async ({ page }, testInfo) => {
  await page.goto("/explorar");
  await page.getByRole("button", { name: "Saúde Dinheiro enviado e sua evolução" }).click();
  await expect(page.locator("#ranking-title")).toHaveText("Quanto dinheiro federal foi enviado à saúde por habitante?");
  await expect(page.locator(".explore-results>li")).toHaveCount(10);
  await page.getByRole("combobox", { name: "Indicador", exact: true }).selectOption("saude_variacao");
  await page.getByRole("combobox", { name: "Ordenar", exact: true }).selectOption("asc");
  await expect(page.locator(".explore-value").first().locator(".change-down")).toBeVisible();
  await expect(page.locator(".explore-reference")).toContainText("2024 → 2025");
  await page.screenshot({ path: `test-results/explorar-saude-${testInfo.project.name}.png`, fullPage: true });
  await page.getByRole("button", { name: "Voto A escolha de cada município" }).click();
  await expect(page.locator("#ranking-title")).toHaveText("Como se distribuiu a votação do candidato mais votado?");
  await expect(page.locator(".explore-reference")).toContainText("1º turno presidencial de 2026");
});

test("seleção de duas cidades atravessa os filtros e abre comparação", async ({ page }) => {
  await page.goto("/explorar");
  await expect(page.locator(".explore-results>li")).toHaveCount(10);
  const first = await page.locator(".explore-city>a").first().getAttribute("href");
  await page.locator(".explore-check input").first().check();
  await page.getByRole("button", { name: "Próxima página" }).click();
  await expect(page.locator(".explore-position").first()).toHaveText("11");
  const second = await page.locator(".explore-city>a").first().getAttribute("href");
  await page.locator(".explore-check input").first().check();
  const dock = page.getByRole("complementary", { name: "Cidades selecionadas para comparar" });
  await expect(dock).toContainText("2 de 2 cidades selecionadas");
  await dock.getByRole("button", { name: "Comparar cidades", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`a=${first!.split("/").at(-1)}&b=${second!.split("/").at(-1)}`));
  await expect(page.getByRole("heading", { name: "O que muda de uma cidade para outra?" })).toBeVisible();
});

test("recorte sem dado e falha de rede têm saídas diferentes", async ({ page }) => {
  await page.goto("/explorar?metrica=saude_total&uf=DF");
  await expect(page.getByRole("heading", { name: "Nenhuma cidade com dado neste recorte." })).toBeVisible();
  await expect(page.locator(".explore-statistics")).toContainText("1");
  await page.route("**/api/explorar?*", route => route.abort());
  await page.getByRole("button", { name: "Ampliar para o Brasil" }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText("Não foi possível carregar");
  await page.unroute("**/api/explorar?*");
  await page.getByRole("button", { name: "Tentar novamente", exact: true }).click();
  await expect(page.locator(".explore-results>li")).toHaveCount(10);
  await expect(page.locator("main").getByRole("alert")).toHaveCount(0);
});
