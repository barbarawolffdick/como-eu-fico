import { test, expect } from "./fixtures";

test("explicações funcionam com mouse, toque e teclado sem sair da tela", async ({ page, isMobile }, testInfo) => {
  await page.goto("/cidade/3550308");
  const card = page.getByRole("article").filter({ has: page.getByRole("heading", { name: "Para quais áreas veio o dinheiro?" }) });
  await expect(card).toContainText("Cuidados do dia a dia, como os oferecidos nas UBS.");
  const help = card.getByRole("button", { name: "Entender: Atenção primária", exact: true });
  if (isMobile) await help.tap(); else await help.click();
  const tooltip = page.getByRole("dialog");
  await expect(tooltip).toContainText("porta de entrada");
  const box = await tooltip.boundingBox();
  expect(box!.x).toBeGreaterThanOrEqual(0);
  expect(box!.x + box!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  await page.locator(':focus').evaluateAll(elements => elements.forEach(element => (element as HTMLElement).blur()));
  await card.screenshot({ style: ".city-sections, .skip-link { visibility: hidden !important; }", path: `test-results/areas-explicadas-${testInfo.project.name}.png` });
  await page.keyboard.press("Escape");
  await expect(tooltip).toHaveCount(0);
  await help.blur();
  const paid = page.getByRole("button", { name: "Entender: despesas pagas", exact: true });
  await paid.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog")).toContainText("não some os dois valores");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("equipes explicam siglas e distinguem reconhecimento de apoio financeiro", async ({ page }, testInfo) => {
  await page.goto("/cidade/3550308");
  const card = page.getByRole("article").filter({ has: page.getByRole("heading", { name: "Equipes com financiamento federal" }) });
  await expect(card).toContainText("não significa que pague todos os custos");
  await expect(card.getByRole("columnheader", { name: /Com registro oficial/ })).toBeVisible();
  await card.getByRole("button", { name: "Entender: eMulti — Equipes multiprofissionais", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("não informa quantos profissionais");
  await page.keyboard.press("Escape");
  await page.locator(':focus').evaluateAll(elements => elements.forEach(element => (element as HTMLElement).blur()));
  await card.screenshot({ style: ".city-sections, .skip-link { visibility: hidden !important; }", path: `test-results/equipes-explicadas-${testInfo.project.name}.png` });
});

test("variação diferencia aumento, redução, estabilidade e ausência", async ({ page }) => {
  let value: number | null = 5.5;
  await page.route("**/api/saude/1504752", async route => {
    const original = await (await route.fetch()).json();
    original.financiamento.variacao_anual_2024_2025_percentual = value;
    await route.fulfill({ json: original });
  });
  for (const [number, css, text] of [[5.5, "change-up", "Aumentou 5,5%"], [-2, "change-down", "Diminuiu 2%"], [0, "change-flat", "Mesmo valor nos dois anos"], [null, "change-unavailable", "Comparação indisponível"]] as const) {
    value = number;
    await page.goto("/cidade/1504752");
    await expect(page.getByTestId("variacao-saude").locator("." + css)).toContainText(text);
  }
});

test("equipamentos alinham aparelhos e estabelecimentos pelo tipo, sem depender da ordem", async ({ page }) => {
  await page.route("**/api/saude/1504752", async route => {
    const original = await (await route.fetch()).json();
    original.financiamento.equipamentos.estabelecimentos_com_equipamento_sus.reverse();
    await route.fulfill({ json: original });
  });
  await page.goto("/cidade/1504752");
  const card = page.getByTestId("equipamentos-saude");
  await expect(card.locator('[data-equipamento="Ultrassom"]')).toContainText("3 locais");
  await card.locator("summary").click();
  await expect(card.locator("dl")).toContainText("6 aparelhos de ultrassom");
});
