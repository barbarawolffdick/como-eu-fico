import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { evolucaoMensal } from "../../lib/evolucao";

const carregar = (arquivo: string) => JSON.parse(readFileSync(`data/public/${arquivo}`, "utf8"));
const pessoas = carregar("pessoas_mds.json");
const detalhes = carregar("detalhes_2026.json");
const rankings = carregar("rankings_2026.json");

test.beforeEach(async ({ page }) => {
  const token = process.env.VERCEL_OIDC_TOKEN;
  const base = process.env.PLAYWRIGHT_BASE_URL;
  if (token && base) {
    const origin = new URL(base).origin;
    await page.route(`${origin}/**`, route => route.continue({ headers: {
      ...route.request().headers(), "x-vercel-trusted-oidc-idp-token": token,
    } }));
  }
});

test("busca, detalhe e links funcionam com dados publicados", async ({ page }, testInfo) => {
  const erros: string[] = [];
  page.on("pageerror", erro => erros.push(erro.message));
  await page.goto("/");
  await page.getByRole("textbox", { name: "Encontre seu município" }).fill("3550308");
  await page.getByRole("option", { name: "São Paulo — SP IBGE 3550308" }).click();
  await expect(page.getByRole("heading", { name: "São Paulo — SP" })).toBeVisible();
  const cobertura = page.locator("article").filter({ has: page.getByRole("heading", { name: "Alcance do Bolsa Família" }) });
  await expect(cobertura).toContainText(pessoas.registros["3550308"].pessoas.toLocaleString("pt-BR"));
  await expect(page.getByRole("heading", { name: "Votação presidencial · 2026" })).toBeVisible();
  await page.screenshot({ path: `test-results/consulta-${testInfo.project.name}.png`, fullPage: true });
  await expect(page.getByRole("link", { name: "Explorar o Brasil →" })).toBeVisible();
  await page.getByRole("link", { name: "Explorar o Brasil →" }).click();
  await expect(page.getByRole("heading", { name: "Explore os municípios brasileiros" })).toBeVisible();
  expect(erros).toEqual([]);
});

test("município sem cobertura continua indisponível", async ({ page }) => {
  const codigo = pessoas.municipios_sem_dado[0];
  await page.goto(`/?municipio=${codigo}`);
  await expect(page.getByRole("heading", { name: `${detalhes.registros[codigo].municipio.nome} — ${detalhes.registros[codigo].municipio.uf}` })).toBeVisible();
  await expect(page.getByText("Cobertura populacional ainda não disponível para este município. Ausência não é zero.")).toBeVisible();
});

test("falha na cobertura exibe erro e permite nova tentativa", async ({ page }) => {
  await page.route("**/api/cobertura?*", route => route.abort());
  await page.goto("/?municipio=3550308");
  await expect(page.locator("main").getByRole("alert")).toContainText("Não foi possível carregar a cobertura");
  await expect(page.getByText("Ausência não é zero.", { exact: false })).toHaveCount(0);
  await page.unroute("**/api/cobertura?*");
  await page.getByRole("button", { name: "Tentar novamente", exact: true }).click();
  await expect(page.getByText(pessoas.registros["3550308"].pessoas.toLocaleString("pt-BR"), { exact: false })).toBeVisible();
  await expect(page.locator("main").getByRole("alert")).toHaveCount(0);
});

test("falha na consulta de famílias não fica carregando indefinidamente", async ({ page }) => {
  await page.route("**/api/mudanca-familias?*", route => route.abort());
  await page.goto("/analises");
  await expect(page.locator("main").getByRole("alert")).toContainText("Não foi possível carregar os dados do MDS");
  await expect(page.getByText("Carregando dados municipais do MDS…", { exact: true })).toHaveCount(0);
});

test("rankings respeitam UF, vencedor e métrica", async ({ page }) => {
  await page.goto("/explorar");
  await page.getByRole("combobox", { name: /^UF/ }).selectOption("SP");
  await page.getByLabel("Resultado eleitoral").selectOption("13");
  await page.getByRole("combobox", { name: /^Métrica/ }).selectOption("valor_habitante");
  const tabela = page.locator("table").first();
  await expect(tabela.getByRole("columnheader", { name: "Valor por habitante" })).toBeVisible();
  const codigo = rankings.registros.filter((x: { uf: string; vencedor: string; empatados: number }) => x.uf === "SP" && x.vencedor === "13" && x.empatados === 1)
    .sort((a: { valor_centavos: number; populacao: number }, b: { valor_centavos: number; populacao: number }) => b.valor_centavos / b.populacao - a.valor_centavos / a.populacao)[0].codigo_ibge;
  await expect(tabela.locator("tbody tr").first().getByRole("link")).toHaveAttribute("href", `/?municipio=${codigo}`);
  await expect(tabela.locator("tbody tr")).toHaveCount(10);
  for (const linha of await tabela.locator("tbody tr").all()) {
    await expect(linha).toContainText("— SP");
    await expect(linha).toContainText("Lula (13)");
  }
});

test("análises carregam e mudam o recorte", async ({ page }) => {
  await page.goto("/analises");
  await expect(page.getByRole("heading", { name: "1. Distribuição entre municípios" })).toBeVisible();
  await page.getByLabel("Recorte territorial").selectOption("SP");
  const total = rankings.registros.filter((x: { uf: string; empatados: number }) => x.uf === "SP" && x.empatados === 1).length;
  await expect(page.getByText(`(${total.toLocaleString("pt-BR")} municípios).`, { exact: false })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Aumentaram", exact: true })).toBeVisible();
  await expect(page.locator("main").getByRole("alert")).toHaveCount(0);
});

test("metadados identificam arquivos reais e seis ausências", async ({ request, page }) => {
  const resposta = await request.get("/api/fontes", { headers: process.env.VERCEL_OIDC_TOKEN ? {
    "x-vercel-trusted-oidc-idp-token": process.env.VERCEL_OIDC_TOKEN,
  } : {} });
  expect(resposta.ok()).toBeTruthy();
  const fontes = await resposta.json();
  expect(fontes.pessoas.municipios_sem_dado.map((m: { codigo_ibge: string }) => m.codigo_ibge)).toEqual(pessoas.municipios_sem_dado);
  for (const arquivo of fontes.arquivos) {
    expect(arquivo.sha256).toBe(createHash("sha256").update(readFileSync(`data/public/${arquivo.arquivo}`)).digest("hex"));
  }
  await page.goto("/fontes");
  await expect(page.getByRole("heading", { name: "Fontes e metodologia" })).toBeVisible();
  await expect(page.getByText("SHA-256:", { exact: false })).toHaveCount(4);
  await expect(page.getByRole("link", { name: "Mojuí dos Campos — PA" })).toBeVisible();
});

test("série incompleta e grupo vazio preservam null", () => {
  const reais = rankings.registros;
  const serie = evolucaoMensal(reais, detalhes.registros, ["202608"])[0];
  expect(serie["13"]).toBeGreaterThan(0);
  const cidade = reais.find((x: { vencedor: string }) => x.vencedor === "13");
  const semMes = { ...detalhes.registros, [cidade.codigo_ibge]: { ...detalhes.registros[cidade.codigo_ibge], bolsa_familia: detalhes.registros[cidade.codigo_ibge].bolsa_familia.filter((x: { mes_competencia: string }) => x.mes_competencia !== "202608") } };
  const incompleta = evolucaoMensal(reais, semMes, ["202608"])[0];
  expect(incompleta["13"]).toBeNull();
  expect(incompleta["22"]).toEqual(serie["22"]);
  expect(incompleta.cobertura["13"].municipios_com_dado).toBe(serie.cobertura["13"].municipios - 1);
  const vazio = evolucaoMensal([], detalhes.registros, ["202608"])[0];
  expect(vazio["13"]).toBeNull();
  expect(vazio["22"]).toBeNull();
});
