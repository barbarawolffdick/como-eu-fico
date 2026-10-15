import { test, expect } from "./fixtures";

const screens = ["/", "/cidade/3550308", "/explorar", "/comparar", "/analises", "/fontes"];

for (const path of screens) {
  test(`base acessível e responsiva em ${path}`, async ({ page }, testInfo) => {
    await page.goto(path);
    await expect(page.locator("main")).toBeVisible();
    // Wait for real content in pages with client-side data.
    await expect(page.locator(".feedback--loading")).toHaveCount(0);
    await expect(page.getByRole("navigation", { name: "Navegação principal" })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const contrastIssues = await page.evaluate(() => {
      const rgb = (color: string) => (color.match(/[\d.]+/g) || []).map(Number);
      const luminance = (color: number[]) => color.slice(0, 3).map(n => {
        const c = n / 255;
        return c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4;
      }).reduce((sum, c, i) => sum + c * [.2126, .7152, .0722][i], 0);
      const issues = new Set<string>();
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        const node = walker.currentNode;
        const el = node.parentElement!;
        if (!node.textContent?.trim() || el.closest("script, style, .sr-only, [aria-hidden=true], :disabled")) continue;
        const rect = el.getBoundingClientRect();
        const style = getComputedStyle(el);
        if (rect.width <= 1 || rect.height <= 1 || style.visibility !== "visible") continue;
        let bg = [0, 0, 0], remaining = 1;
        for (let ancestor: Element | null = el; ancestor && remaining > .001; ancestor = ancestor.parentElement) {
          const value = rgb(getComputedStyle(ancestor).backgroundColor);
          const alpha = value[3] ?? 1;
          bg = bg.map((c, i) => c + value[i] * alpha * remaining);
          remaining *= 1 - alpha;
        }
        bg = bg.map(c => c + 255 * remaining);
        const text = rgb(style.color);
        const alpha = text[3] ?? 1;
        const foreground = text.map((c, i) => c * alpha + bg[i] * (1 - alpha));
        const [light, dark] = [luminance(foreground), luminance(bg)].sort((a, b) => b - a);
        const ratio = (light + .05) / (dark + .05);
        const size = parseFloat(style.fontSize);
        const large = size >= 24 || (size >= 18.66 && parseInt(style.fontWeight) >= 700);
        if (ratio + .01 < (large ? 3 : 4.5)) issues.add(`${node.textContent.trim().slice(0, 55)}: ${ratio.toFixed(2)} (${el.tagName}.${el.className})`);
      }
      return [...issues];
    });
    expect(contrastIssues, "Texto precisa de contraste AA no fundo efetivamente renderizado").toEqual([]);
    await page.screenshot({ path: `test-results/design-${path === "/" ? "inicio" : path.split("/")[1]}-${testInfo.project.name}.png` });
    await page.keyboard.press("Tab");
    const skip = page.getByRole("link", { name: "Pular para o conteúdo" });
    await expect(skip).toBeFocused();
    await expect(skip).toBeInViewport();
    await page.keyboard.press("Enter");
    await expect(page.locator("main")).toBeFocused();
  });
}

test("movimento reduzido e foco visível continuam funcionais", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/explorar");
  expect(await page.evaluate(() => getComputedStyle(document.documentElement).scrollBehavior)).toBe("auto");
  const select = page.getByLabel("Estado (UF)");
  await select.focus();
  await expect(select).toBeFocused();
  expect(await select.evaluate(el => parseFloat(getComputedStyle(el).outlineWidth))).toBeGreaterThanOrEqual(3);
  expect(await select.evaluate(el => el.getBoundingClientRect().height)).toBeGreaterThanOrEqual(44);
});

test("links com opções inválidas anunciam erro e oferecem recuperação", async ({ page }) => {
  for (const path of ["/explorar?regiao=invalida", "/comparar?a=invalida"]) {
    await page.goto(path);
    const error = page.locator("main").getByRole("alert");
    await expect(error).toBeVisible();
    const recovery = error.getByRole("link");
    await expect(recovery).toBeVisible();
    await recovery.click();
    await expect(page.locator("main").getByRole("alert")).toHaveCount(0);
  }
});
