import { test, expect } from "./fixtures";
import { readFileSync } from "node:fs";

const snapshot = JSON.parse(readFileSync("data/public/financiamento_saude.json", "utf8"));

test("cidade relaciona total, finalidades, emendas e população sem dupla contagem", async ({ page, request }, testInfo) => {
  const r = await request.get("/api/saude/1504752");
  const body = await r.json();
  expect(body.financiamento).toEqual(snapshot.registros["1504752"]);
  await page.goto("/?municipio=1504752");
  const painel = page.getByTestId("financiamento-saude");
  await expect(painel.getByRole("heading", { name: "Total federal recebido pelo fundo municipal" })).toBeVisible();
  await expect(painel).toContainText("R$ 8.605.457,36");
  await expect(painel).toContainText("R$ 327,14");
  await expect(painel).toContainText("40,67% do total municipal");
  await expect(painel).toContainText("não devem ser somados novamente");
  await painel.getByText("Manutenção e estruturação da rede", { exact: true }).click();
  await expect(painel).toContainText("Manutenção dos serviços");
  await painel.locator(".health-summary").screenshot({ path: `test-results/financiamento-${testInfo.project.name}.png` });
});

test("evolução compara somente anos completos e deixa 2026 parcial separado", async ({ page }) => {
  await page.goto("/?municipio=1504752");
  const card = page.getByTestId("financiamento-saude").getByRole("article").filter({ has: page.getByRole("heading", { name: "O repasse aumentou ou diminuiu?" }) });
  await expect(card).toContainText("2024 · jan–dez");
  await expect(card).toContainText("2025 · jan–dez");
  await expect(card).toContainText("0,51%");
  await expect(card).toContainText("não calculamos variação contra um ano completo");
  await expect(card.getByRole("table")).not.toContainText("2026");
});

test("SIOPS apresenta despesas por fonte com seu próprio exercício", async ({ page }) => {
  await page.goto("/?municipio=1504752");
  const card = page.getByTestId("financiamento-saude").getByRole("article").filter({ has: page.getByRole("heading", { name: "Como a cidade financiou suas despesas de saúde?" }) });
  await expect(card).toContainText("exercício 2025");
  await expect(card).toContainText("49,44%");
  await expect(card).toContainText("Estes totais são despesas, não receitas recebidas");
  await card.getByText("Ver despesas liquidadas por fonte de financiamento", { exact: true }).click();
  await expect(card).toContainText("Transferências federais fundo a fundo");
  await expect(card).toContainText("Impostos e transferências de impostos");
});

test("equipamentos distinguem locais SUS do inventário e preservam ausências", async ({ page }, testInfo) => {
  await page.goto("/?municipio=1504752");
  const card = page.getByTestId("equipamentos-saude");
  const ultrassom = card.locator('[data-equipamento="Ultrassom"]');
  await expect(ultrassom).toContainText("3 locais");
  await expect(ultrassom).toContainText("informado para o SUS");
  await expect(card.locator('[data-equipamento="Mamógrafo"]')).toContainText("Sem informação");
  await expect(card).toContainText("agosto de 2026");
  await expect(card.locator("dl")).not.toBeVisible();
  await card.getByText("Ver o total de equipamentos na rede pública e privada", { exact: true }).click();
  await expect(card.locator("dl")).toContainText("6 aparelhos de ultrassom");
  await expect(card).toContainText("não informa quantos aparelhos são do SUS");
  expect(await card.evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
  await card.screenshot({ style: ".city-sections, .skip-link { visibility: hidden !important; }", path: `test-results/equipamentos-${testInfo.project.name}.png` });
});

test("Brasília separa AgSUS, recurso distrital e valor municipal ausente", async ({ page, request }) => {
  const body = await (await request.get("/api/saude/5300108")).json();
  expect(body.financiamento.fns.at(-1).municipal).toBeNull();
  expect(body.financiamento.centavos_por_habitante).toBeNull();
  expect(body.financiamento.fns.at(-1).outros_destinatarios_sediados_na_cidade.valor_centavos).toBe(930854400);
  await page.goto("/?municipio=5300108");
  const painel = page.getByTestId("financiamento-saude");
  await painel.getByText("Outros destinatários sediados nesta cidade", { exact: true }).click();
  await expect(painel).toContainText("o destinatário identificado não é o fundo municipal");
  await expect(painel).toContainText("R$ 9.308.544,00");
  await expect(painel).toContainText("Recursos distritais relacionados à cidade");
});

test("município sem registro hospitalar não recebe leitos zero", async ({ page }) => {
  await page.goto("/?municipio=1504752");
  const painel = page.getByTestId("financiamento-saude");
  await expect(painel).toContainText("Não há registro hospitalar validado nesta competência para a cidade. Ausência não é zero.");
  await expect(painel).toContainText("10 unidades básicas");
  await painel.getByText("Conhecer algumas unidades da cidade", { exact: true }).click();
  const link = painel.getByRole("link", { name: /UNIDADE BASICA DE SAUDE/ }).first();
  await expect(link).toHaveAttribute("href", /\/ficha\/index\.jsp\?coUnidade=150475\d{7}$/);
});
