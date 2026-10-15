import { test, expect } from "./fixtures";
import { readFileSync } from "node:fs";
import { ultimoMesComum, porHabitante, placar } from "../../lib/comparacao";

const details = JSON.parse(readFileSync("data/public/detalhes_2026.json", "utf8")).registros;
const health = JSON.parse(readFileSync("data/public/financiamento_saude.json", "utf8")).registros;
const people = JSON.parse(readFileSync("data/public/pessoas_mds.json", "utf8")).registros;
const money = (centavos: number) => (centavos / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

test("regras não confundem zero, ausência, empate ou meses diferentes", () => {
  const a = details["3550308"];
  const b = details["3304557"];
  expect(ultimoMesComum(a, { ...b, bolsa_familia: [] })).toBeNull();
  expect(porHabitante(0, a)).toBe(0);
  expect(porHabitante(null, a)).toBeNull();
  expect(porHabitante(100, { ...a, municipio: { ...a.municipio, populacao: 0 } })).toBeNull();
  expect(placar({ ...a, eleitoral_disponivel: false })).toBeNull();
  expect(placar({ ...a, votos_presidenciais: [{ candidato: "13", votos: 100 }, { candidato: "22", votos: 100 }] })?.empate).toBe(true);
});

test("comparação inicial mostra fontes reais e layout sem rolagem lateral", async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/comparar");
  await expect(page.getByRole("heading", { name: "O que muda de uma cidade para outra?" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Por habitante", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("navigation", { name: "Navegação principal" }).getByRole("link", { name: "Comparar cidades" })).toHaveAttribute("aria-current", "page");
  const row = page.getByTestId("compare-health-money");
  const value = health["3550308"].fns.at(-1).municipal.valor_centavos;
  await expect(row.locator(".comparison-value").first()).toContainText(money(value / details["3550308"].municipio.populacao));
  await expect(page.getByTestId("compare-benefit-coverage")).toContainText(people["3550308"].cobertura_pct.toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + "%");
  const barWidth = await page.getByTestId("compare-benefit-coverage").locator(".comparison-bar span").first().evaluate(element => parseFloat((element as HTMLElement).style.width));
  expect(barWidth).toBeCloseTo(people["3550308"].cobertura_pct, 3);
  await expect(page.getByTestId("compare-benefit-money")).toContainText("08/2026 · último mês comum");
  await expect(page.getByTestId("compare-doctors")).not.toContainText("Carregando…");
  await expect(page.locator(".compare-error")).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: `test-results/comparacao-${testInfo.project.name}.png`, fullPage: true });
  await page.getByText("Ver a distribuição de votos por candidato", { exact: true }).click();
  await expect(page.locator(".compare-votes-table")).toContainText("Flávio Bolsonaro (22)");
  expect(errors).toEqual([]);
});

test("total, inversão, link e histórico preservam as escolhas", async ({ page }) => {
  await page.goto("/comparar?a=1504752&b=3550308");
  await page.getByRole("button", { name: "Valor total", exact: true }).click();
  await expect(page).toHaveURL(/modo=total/);
  await expect(page.getByTestId("compare-health-money").locator(".comparison-value").first()).toContainText("R$ 8.605.457,36");
  await page.getByRole("button", { name: "Inverter as cidades" }).click();
  await expect(page).toHaveURL(/a=3550308&b=1504752&modo=total/);
  await page.reload();
  await expect(page.getByRole("button", { name: "Valor total", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("region", { name: "Cidade A", exact: true })).toContainText("São Paulo — SP");
  await page.getByRole("button", { name: "Copiar link" }).click();
  await expect(page.getByRole("status").filter({ hasText: /Link copiado|copie o endereço/ })).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(/a=1504752&b=3550308&modo=total/);
});

test("busca troca apenas uma cidade e evita seleção duplicada", async ({ page }) => {
  await page.goto("/comparar");
  const a = page.getByRole("region", { name: "Cidade A", exact: true });
  const search = a.getByRole("combobox");
  await search.fill("3304557");
  await a.getByRole("option").click();
  await expect(page.locator("main").getByRole("alert")).toContainText("já está na comparação");
  await search.fill("1504752");
  await expect(a.getByRole("option")).toHaveCount(1);
  await search.press("ArrowDown"); await search.press("Enter");
  await expect(page).toHaveURL(/a=1504752&b=3304557/);
  await expect(a.getByRole("heading")).toHaveText("Mojuí dos Campos — PA");
  await expect(page.getByRole("region", { name: "Cidade B", exact: true }).getByRole("heading")).toHaveText("Rio de Janeiro — RJ");
});

test("Bolsa Família usa o último mês comum e distingue pontos percentuais", async ({ page }) => {
  await page.route("**/api/municipios/3304557", async route => {
    const body = await (await route.fetch()).json();
    body.bolsa_familia = body.bolsa_familia.filter((row: { mes_competencia: string }) => row.mes_competencia !== "202608");
    await route.fulfill({ json: body });
  });
  await page.goto("/comparar?modo=total&bolsa=total");
  const row = page.getByTestId("compare-benefit-money");
  await expect(row).toContainText("07/2026 · último mês comum");
  await expect(row.locator(".comparison-value").first()).toContainText(money(details["3550308"].bolsa_familia.find((r: { mes_competencia: string }) => r.mes_competencia === "202607").valor_centavos));
  await expect(page.getByTestId("compare-benefit-coverage").locator(".comparison-reading")).toContainText("pontos percentuais");
});

test("períodos de saúde diferentes não geram diferença nem barras de comparação", async ({ page }) => {
  await page.route("**/api/saude/3304557", async route => {
    const body = await (await route.fetch()).json();
    body.financiamento.fns.at(-1).fim = "202606";
    await route.fulfill({ json: body });
  });
  await page.goto("/comparar");
  const row = page.getByTestId("compare-health-money");
  await expect(row).toContainText("Períodos diferentes");
  await expect(row.locator(".comparison-bar")).toHaveCount(0);
  await expect(row).toContainText("06/2026");
});

test("saúde ausente e zero explícito continuam diferentes", async ({ page }) => {
  await page.goto("/comparar?a=5300108&b=5101837");
  await expect(page.getByTestId("compare-health-money").locator(".comparison-value").first()).toContainText("Indisponível");
  await expect(page.getByTestId("compare-health-money").locator(".comparison-reading")).not.toContainText("Diferença:");
  await expect(page.getByTestId("compare-doctors").locator(".comparison-value").nth(1).locator("strong")).toHaveText("0");
});

test("falha em uma fonte permite recuperar sem perder a outra cidade", async ({ page }) => {
  await page.route("**/api/saude/3304557", route => route.abort());
  await page.goto("/comparar");
  const healthSection = page.getByRole("region", { name: "Dinheiro enviado e presença de profissionais" });
  await expect(healthSection.getByRole("alert")).toContainText("Rio de Janeiro — RJ");
  await expect(page.getByTestId("compare-health-money").locator(".comparison-value").nth(1)).toContainText("Falha na consulta");
  await expect(page.getByTestId("compare-benefit-money")).toContainText("08/2026");
  await page.unroute("**/api/saude/3304557");
  await healthSection.getByRole("button", { name: "Tentar novamente — Rio de Janeiro — RJ" }).click();
  await expect(healthSection.getByRole("alert")).toHaveCount(0);
  await expect(page.getByTestId("compare-health-money").locator(".comparison-value").nth(1)).not.toContainText("Carregando…");
});

test("cidade atual abre comparação e links inválidos têm saída", async ({ page }) => {
  await page.goto("/cidade/1504752");
  await page.getByRole("link", { name: "Comparar com outra cidade" }).click();
  await expect(page).toHaveURL(/\/comparar\?a=1504752$/);
  await expect(page.getByRole("region", { name: "Cidade A", exact: true }).getByRole("heading")).toHaveText("Mojuí dos Campos — PA");
  await page.goto("/comparar?a=invalido");
  await expect(page.getByRole("heading", { name: "Confira as cidades do link" })).toBeVisible();
  await page.getByRole("link", { name: "Abrir a comparação" }).click();
  await expect(page.getByRole("heading", { name: "O que muda de uma cidade para outra?" })).toBeVisible();
});
