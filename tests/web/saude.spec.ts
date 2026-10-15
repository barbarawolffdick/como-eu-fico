import { test, expect } from "./fixtures";
import { readFileSync } from "node:fs";

const snapshot = JSON.parse(readFileSync("data/public/saude_piloto.json", "utf8"));

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
  await expect(saude).toContainText("Referência: 05/10/2026");
  expect(await saude.locator(".health-table").evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
  await saude.screenshot({ path: `test-results/saude-${testInfo.project.name}.png` });
  await saude.getByText("Repasses ao fundo estadual registrado nesta cidade", { exact: true }).click();
  await expect(saude).toContainText("Não somamos esse montante ao repasse municipal");
});

test("ausência no Mais Médicos não é zero", async ({ page }) => {
  await page.goto("/?municipio=5101837");
  const saude = page.getByTestId("saude-municipal");
  await expect(saude.getByRole("heading", { name: "Mais Médicos na cidade" })).toBeVisible();
  await expect(saude).toContainText("A consulta oficial não retornou observações para esta cidade. Ausência não é zero.");
});

test("cidade fora do piloto informa escopo e permite abrir outra cidade", async ({ page, request }) => {
  const r = await request.get("/api/saude/1504752");
  expect(await r.json()).toMatchObject({ disponivel: false, dados: null, status: "PILOTO" });
  await page.goto("/?municipio=1504752");
  const saude = page.getByTestId("saude-municipal");
  await expect(saude).toContainText("Esta cidade ainda não faz parte do piloto de saúde");
  await saude.getByRole("link", { name: "Sobral", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Sobral — CE" })).toBeVisible();
  await expect(page.getByTestId("saude-municipal").getByRole("heading", { name: "Equipes com financiamento federal" })).toBeVisible();
});

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
