import { test, expect } from "./fixtures";
import { readFileSync } from "node:fs";
import { mediaPorBeneficiario, pessoasTabulares, leituraCobertura } from "../../lib/bolsa-familia";

const detalhes = JSON.parse(readFileSync("data/public/detalhes_2026.json", "utf8")).registros;
const pessoas = JSON.parse(readFileSync("data/public/pessoas_mds_mensal.json", "utf8")).registros;
const familias = JSON.parse(readFileSync("data/public/familias_mds.json", "utf8")).registros;
const fixture = JSON.parse(readFileSync("tests/fixtures/pessoas_mds_tabular.json", "utf8"));
const moeda = (v: number) => (v / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

test("média exige denominador positivo e série preserva agosto e setembro distintos", () => {
  expect(mediaPorBeneficiario(0, 100)).toBe(0);
  for (const n of [null, undefined, 0, -1, 1.5]) expect(mediaPorBeneficiario(100, n)).toBeNull();
  expect(mediaPorBeneficiario(null, 100)).toBeNull();
  const html = "var strJsondados = '" + JSON.stringify(fixture.consultas["3550308"].linhas) + "';";
  const city = { codigo_ibge: "3550308", nome: "São Paulo", uf: "SP" };
  expect(pessoasTabulares(html, city)).toEqual({ "202608": 1650898, "202609": 1652769 });
  expect(() => pessoasTabulares(html, { ...city, uf: "RJ" })).toThrow();
  expect(leituraCobertura(91.6)).toContain("92 em cada 100 moradores");
  expect(leituraCobertura(.1)).toContain("Menos de 1");
});

test("API identifica cidade, competência e proveniência sem confundir pessoas e famílias", async ({ request }) => {
  expect((await request.get("/api/beneficiarios/invalido")).status()).toBe(400);
  expect((await request.get("/api/beneficiarios/9999999")).status()).toBe(404);
  const response = await request.get("/api/beneficiarios/3138203");
  expect(response.ok()).toBe(true);
  const body = await response.json();
  expect(body.codigo_ibge).toBe("3138203");
  expect(body.periodos["202608"]).toEqual({ pessoas: pessoas["3138203"].periodos["202608"], familias: familias["202608"]["3138203"] });
  expect(body.periodos["202609"].familias).toBeNull();
  expect(body.fontes.pessoas.sha256).toMatch(/^[a-f0-9]{64}$/);
  expect(body.fontes.pessoas.url).toContain("codigo=3138203");
  expect(body.aviso).toBeNull();
});

test("percentual explica toda a população e a modal distingue família e titular", async ({ page }, testInfo) => {
  await page.goto("/cidade/3550308");
  const bolsa = page.locator("#dados-bolsa");
  await expect(bolsa).toContainText("da população da cidade");
  await expect(bolsa).toContainText("em cada 100 moradores");
  const trigger = bolsa.getByRole("button", { name: "Entender: Quem entra na conta do Bolsa Família?" });
  await trigger.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("Titular:");
  await expect(dialog).toContainText("Não é uma porcentagem dentro de cada família");
  const box = await dialog.boundingBox();
  expect(box!.x).toBeGreaterThanOrEqual(0);
  expect(box!.x + box!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  await dialog.screenshot({ path: `test-results/bolsa-explicacao-${testInfo.project.name}.png` });
  await page.keyboard.press("Tab");
  expect(await page.evaluate(() => document.activeElement?.closest("dialog") != null)).toBe(true);
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(trigger).toBeFocused();
  expect(await page.evaluate(() => document.body.style.overflow)).not.toBe("hidden");
});

test("Bolsa Família divide por pessoas ou famílias do mesmo mês, nunca pela população inteira", async ({ page }, testInfo) => {
  await page.goto("/comparar?a=3138203&b=3304557");
  const row = page.getByTestId("compare-benefit-money");
  const valor = detalhes["3138203"].bolsa_familia.find((x: { mes_competencia: string }) => x.mes_competencia === "202608").valor_centavos;
  await expect(row.getByRole("heading")).toHaveText("Valor registrado por pessoa da família beneficiária");
  await expect(row.locator(".comparison-value").first()).toContainText(moeda(valor / pessoas["3138203"].periodos["202608"]));
  await expect(row.locator(".comparison-value").first()).not.toContainText(moeda(valor / detalhes["3138203"].municipio.populacao));
  await expect(row).toContainText("08/2026");
  await page.getByRole("button", { name: "Por família", exact: true }).click();
  await expect(page).toHaveURL(/bolsa=familia/);
  await expect(row.locator(".comparison-value").first()).toContainText(moeda(valor / familias["202608"]["3138203"]));
  await row.screenshot({ path: `test-results/media-bolsa-${testInfo.project.name}.png` });
});

test("sem pessoas no mês, a comparação não usa setembro como substituto de agosto", async ({ page }) => {
  await page.route("**/api/beneficiarios/3304557", async route => {
    const body = await (await route.fetch()).json();
    body.periodos["202608"].pessoas = null;
    await route.fulfill({ json: body });
  });
  await page.goto("/comparar");
  const row = page.getByTestId("compare-benefit-money");
  await expect(row.locator(".comparison-value").nth(1)).toContainText("Indisponível");
  await expect(row.locator(".comparison-reading")).not.toContainText("Diferença:");
  await expect(row.locator(".comparison-bar")).toHaveCount(0);
  await page.getByRole("button", { name: "Por família", exact: true }).click();
  await expect(row.locator(".comparison-value").nth(1)).not.toContainText("Indisponível");
});

test("resumo eleitoral mostra três candidatos e expande sem recalcular os percentuais", async ({ page }) => {
  await page.goto("/cidade/3550308");
  for (const selector of ["#voto"]) {
    const box = page.locator(selector);
    await expect(box.locator(".vote")).toHaveCount(3);
    const first = await box.locator(".vote").first().textContent();
    await box.getByRole("button", { name: /^Ver mais candidatos/ }).click();
    await expect(box.locator(".vote")).toHaveCount(detalhes["3550308"].votos_presidenciais.length);
    expect(await box.locator(".vote").first().textContent()).toBe(first);
    await box.getByRole("button", { name: "Ver menos candidatos" }).click();
    await expect(box.locator(".vote")).toHaveCount(3);
  }
});
