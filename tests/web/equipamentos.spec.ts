import { test, expect } from "./fixtures";

test("São Paulo destaca locais SUS e mantém o inventário em consulta separada", async ({ page }, testInfo) => {
  await page.goto("/?municipio=3550308");
  const section = page.getByTestId("equipamentos-saude");
  await expect(section.getByRole("listitem")).toHaveCount(6);
  await expect(section.locator('[data-equipamento="Mamógrafo"]')).toContainText("88 locais");
  await expect(section.locator('[data-equipamento="Mamógrafo"]')).not.toContainText("434");
  await expect(section).toContainText("não confirma vagas");
  await section.screenshot({ style: ".city-sections, .skip-link { visibility: hidden !important; }", path: `test-results/equipamentos-sp-${testInfo.project.name}.png` });
  const summary = section.locator("summary");
  await summary.focus();
  await page.keyboard.press("Enter");
  await expect(section.locator("dl")).toBeVisible();
  await expect(section.locator("dl")).toContainText("434 mamógrafos");
  await expect(section.locator("dl")).toContainText("4.478 aparelhos de ultrassom");
  await page.keyboard.press("Enter");
  await expect(section.locator("dl")).not.toBeVisible();
  expect(await section.evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
});

test("valores continuam ligados ao tipo e zero explícito difere de ausência", async ({ page }) => {
  await page.route("**/api/saude/1504752", async route => {
    const body = await (await route.fetch()).json();
    const equipamentos = body.financiamento.equipamentos;
    equipamentos.estabelecimentos_com_equipamento_sus.reverse();
    // Estado de contrato: nenhum número simulado é publicado no snapshot.
    equipamentos.estabelecimentos_com_equipamento_sus.find((e: { tipo: string }) => e.tipo === "Raio X").valor = 0;
    await route.fulfill({ json: body });
  });
  await page.goto("/?municipio=1504752");
  const section = page.getByTestId("equipamentos-saude");
  await expect(section.locator('[data-equipamento="Ultrassom"]')).toContainText("3 locais");
  await expect(section.locator('[data-equipamento="Raio X"]')).toContainText("0 locais");
  await expect(section.locator('[data-equipamento="Mamógrafo"]')).toContainText("Sem informação");
  await section.locator("summary").click();
  await expect(section.locator("dl")).toContainText("6 aparelhos de ultrassom");
  await page.setViewportSize({ width: 320, height: 900 });
  expect(await section.evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
});
