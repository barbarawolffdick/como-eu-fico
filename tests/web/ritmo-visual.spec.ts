import { test, expect } from "./fixtures";

test("panorama mantém linhas comuns e valores monetários cabem em telas estreitas", async ({ page }, testInfo) => {
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/cidade/3550308");
    await expect(page.locator(".overview-number").last()).toContainText("%");
    await expect(page.locator(".health-summary .money-value").first()).toContainText("R$");
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const moneyLines = await page.locator(".health-summary .money-value").first().evaluate(el => {
      const range = document.createRange(); range.selectNodeContents(el);
      return range.getClientRects().length;
    });
    expect(moneyLines, `Valor completo deve caber em uma linha a ${width}px`).toBe(1);
    if (width === 1440) {
      const measure = () => page.locator(".city-overview").evaluate(el => {
        const y = (selector: string) => [...el.querySelectorAll(selector)].map(item => item.getBoundingClientRect().top);
        const widths = [...el.children].map(item => item.getBoundingClientRect().width);
        return { numbers: y(".overview-number"), actions: y(".overview-footer .action-link"), widths };
      });
      for (const expanded of [false, true]) {
        if (expanded) await page.locator(".electoral-overview").getByRole("button", { name: /^Ver mais candidatos/ }).click();
        const bounds = await measure();
        for (const line of [bounds.numbers, bounds.actions, bounds.widths]) expect(Math.max(...line) - Math.min(...line)).toBeLessThan(2);
      }
      await page.locator(".electoral-overview").getByRole("button", { name: "Ver menos candidatos" }).click();
      await page.locator("#panorama").screenshot({ path: `test-results/panorama-alinhado-${testInfo.project.name}.png` });
    }
    if (width === 390) await page.locator(".health-summary").screenshot({ path: `test-results/saude-alinhada-${testInfo.project.name}.png` });
  }
  await page.setViewportSize({ width: 390, height: 844 });
  const nav = page.getByRole("navigation", { name: "Indicadores da cidade" });
  await nav.getByRole("link", { name: "Saúde", exact: true }).click();
  await expect(nav.getByRole("link", { name: "Saúde", exact: true })).toHaveAttribute("aria-current", "location");
  await expect(page.locator("#titulo-saude")).toBeInViewport();
});
