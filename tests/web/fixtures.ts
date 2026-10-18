import { test as base, expect } from "@playwright/test";

export const test = base.extend({
  page: async ({ page, baseURL }, use) => {
    const token = process.env.VERCEL_OIDC_TOKEN;
    if (token && baseURL && process.env.PLAYWRIGHT_BASE_URL) {
      await page.route(`${new URL(baseURL).origin}/**`, route => route.continue({ headers: {
        ...route.request().headers(), "x-vercel-trusted-oidc-idp-token": token,
      } }));
    }
    await use(page);
  },
  request: async ({ playwright, baseURL }, use) => {
    const token = process.env.VERCEL_OIDC_TOKEN;
    const context = await playwright.request.newContext({ baseURL,
      extraHTTPHeaders: token && process.env.PLAYWRIGHT_BASE_URL ? { "x-vercel-trusted-oidc-idp-token": token } : {},
    });
    try { await use(context); } finally { await context.dispose(); }
  },
});
export { expect };

/** Abre o detalhe de saúde, que fica recolhido abaixo dos gráficos da seção 6 da página da cidade. */
export async function abrirDetalheSaude(page: import("@playwright/test").Page) {
  const detalhe = page.getByTestId("saude-detalhe");
  if (!(await detalhe.evaluate(el => (el as HTMLDetailsElement).open))) await detalhe.locator("> summary").click();
}
