import { test, expect } from "./fixtures";

test("valores principais e monetários cabem em telas estreitas", async ({ page }, testInfo) => {
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/cidade/3550308");
    await expect(page.locator(".federal-big")).toContainText("R$");
    await expect(page.locator("#saude svg.viz").first()).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    // Gráficos desenhados na largura do contêiner: nenhum SVG ultrapassa o cartão.
    const excedentes = await page.locator("svg.viz").evaluateAll(svgs => svgs.filter(s => s.getBoundingClientRect().width > (s.closest(".card")?.getBoundingClientRect().width ?? innerWidth) + 1).length);
    expect(excedentes, `Gráficos cabem no cartão a ${width}px`).toBe(0);
    const bigLines = await page.locator(".federal-big").evaluate(el => {
      const range = document.createRange(); range.selectNodeContents(el);
      return range.getClientRects().length;
    });
    expect(bigLines, `Total federal deve caber em uma linha a ${width}px`).toBe(1);
    if (width === 1440) await page.locator("#quanto").screenshot({ path: `test-results/quanto-chega-alinhado-${testInfo.project.name}.png` });
    if (width === 390) await page.locator("#saude").screenshot({ path: `test-results/saude-alinhada-${testInfo.project.name}.png` });
  }
  await page.setViewportSize({ width: 390, height: 844 });
  const nav = page.getByRole("navigation", { name: "Indicadores da cidade" });
  await nav.getByRole("link", { name: "Saúde", exact: true }).click();
  await expect(nav.getByRole("link", { name: "Saúde", exact: true })).toHaveAttribute("aria-current", "location");
  await expect(page.locator("#saude-title")).toBeInViewport();
});
