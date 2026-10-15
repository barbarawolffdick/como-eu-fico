import { test, expect } from "./fixtures";
import { readFileSync } from "node:fs";

const snapshot = JSON.parse(readFileSync("data/public/saude_municipal.json", "utf8"));

test("saúde aparece na cidade com períodos independentes e fundo estadual separado", async ({ page, request }, testInfo) => {
  const r = await request.get("/api/saude/3550308");
  expect(r.ok()).toBeTruthy();
  const resposta = await r.json();
  expect(resposta.dados).toEqual(snapshot.registros["3550308"]);
  await page.goto("/?municipio=3550308");
  const saude = page.getByTestId("saude-municipal");
  await expect(saude.getByRole("heading", { name: "Saúde na sua cidade" })).toBeVisible();
  await expect(saude).toContainText("Acumulado de 01/2026 a 07/2026");
  await expect(saude).toContainText("R$ 701.883.633,40");
  await expect(saude).toContainText("Parcela 10/2026 · Cadastro CNES 08/2026");
  await expect(saude).toContainText("Referência: 09/10/2026");
  await page.getByRole("navigation", { name: "Indicadores da cidade" }).getByRole("link", { name: "Saúde", exact: true }).click();
  await expect(saude.getByRole("heading", { name: "Saúde na sua cidade" })).toBeInViewport();
  expect(await saude.locator(".health-table").evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
  await saude.screenshot({ path: `test-results/saude-${testInfo.project.name}.png` });
  await saude.getByText("Repasses ao fundo estadual registrado nesta cidade", { exact: true }).click();
  await expect(saude).toContainText("Não somamos esse montante ao repasse municipal");
});

test("zero explícito do consolidado não é confundido com ausência", async ({ page, request }) => {
  const r = await request.get("/api/saude/5101837");
  expect((await r.json()).dados.mais_medicos.ultimo.vagas_ocupadas).toBe(0);
  await page.goto("/?municipio=5101837");
  const saude = page.getByTestId("saude-municipal");
  await expect(saude).toContainText("Zero informado explicitamente no consolidado oficial");
  await expect(saude).toContainText("Vagas ocupadas no provimento federal");
});

test("cidade antes fora do piloto agora tem os três indicadores", async ({ page, request }) => {
  const r = await request.get("/api/saude/1504752");
  expect(await r.json()).toMatchObject({ disponivel: true, status: "NACIONAL", municipios_referencia: 5571,
    dados: snapshot.registros["1504752"] });
  await page.goto("/?municipio=1504752");
  const saude = page.getByTestId("saude-municipal");
  await expect(saude.getByRole("heading", { name: "Equipes com financiamento federal" })).toBeVisible();
  await expect(saude).toContainText("R$ 7.569.070,01");
  await expect(saude).toContainText("Referência: 09/10/2026");
  await expect(saude).not.toContainText("piloto");
});

test("ausência de repasse municipal permanece indisponível", async ({ page }) => {
  await page.goto("/?municipio=2605459");
  const saude = page.getByTestId("saude-municipal");
  const fns = saude.getByRole("article").filter({ has: page.getByRole("heading", { name: "Repasses federais para atenção primária" }) });
  await expect(fns.locator(".big")).toHaveText("Indisponível");
  await expect(fns).toContainText("Não há repasse municipal validado neste recorte. Ausência não é zero.");
});

test("Brasília mantém fundo distrital separado do indicador municipal", async ({ page, request }) => {
  const r = await request.get("/api/saude/5300108");
  expect((await r.json()).dados.fns.municipal).toBeNull();
  await page.goto("/?municipio=5300108");
  const saude = page.getByTestId("saude-municipal");
  await expect(saude).toContainText("Repasses ao fundo distrital registrado nesta cidade");
  await saude.getByText("Repasses ao fundo distrital registrado nesta cidade", { exact: true }).click();
  await expect(saude).toContainText("Não somamos esse montante ao repasse municipal");
});

for (const codigo of ["1302603", "2611606", "3304557", "4314902", "5208707"]) {
  test(`saúde nacional preserva a cidade ${codigo} sem misturar registros`, async ({ request }) => {
    const r = await request.get(`/api/saude/${codigo}`);
    const doc = await r.json();
    expect(r.ok()).toBeTruthy();
    expect(doc.dados).toEqual(snapshot.registros[codigo]);
    expect(JSON.stringify(doc).length).toBeLessThan(30_000);
  });
}

test("API de saúde rejeita códigos inválidos e municípios inexistentes", async ({ request }) => {
  expect((await request.get("/api/saude/123")).status()).toBe(400);
  expect((await request.get("/api/saude/9999999")).status()).toBe(404);
});

test("falha de rede na saúde pode ser recuperada sem virar ausência", async ({ page }) => {
  await page.route("**/api/saude/*", route => route.abort());
  await page.goto("/?municipio=3550308");
  const saude = page.getByTestId("saude-municipal");
  await expect(saude.getByRole("alert")).toContainText("Não foi possível carregar os indicadores de saúde");
  await page.unroute("**/api/saude/*");
  await saude.getByRole("button", { name: "Tentar novamente", exact: true }).click();
  await expect(saude.getByRole("heading", { name: "Repasses federais para atenção primária" })).toBeVisible();
  await expect(saude.getByRole("alert")).toHaveCount(0);
});
