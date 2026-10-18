import { test, expect } from "./fixtures";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { evolucaoMensal } from "../../lib/evolucao";

const carregar = (arquivo: string) => JSON.parse(readFileSync(`data/public/${arquivo}`, "utf8"));
const pessoas = carregar("pessoas_mds.json");
const detalhes = carregar("detalhes_2026.json");
const rankings = carregar("rankings_2026.json");


test("busca, detalhe e links funcionam com dados publicados", async ({ page }, testInfo) => {
  const erros: string[] = [];
  page.on("pageerror", erro => erros.push(erro.message));
  await page.goto("/");
  await page.getByRole("combobox", { name: "Encontre seu município" }).fill("3550308");
  await page.getByRole("option", { name: "São Paulo — SP IBGE 3550308" }).click();
  await expect(page.getByRole("heading", { name: "São Paulo — SP" })).toBeVisible();
  const cobertura = page.locator("article").filter({ has: page.getByRole("heading", { name: "Moradores em famílias que recebem Bolsa Família" }) });
  await expect(cobertura).toContainText(pessoas.registros["3550308"].pessoas.toLocaleString("pt-BR"));
  await expect(page.getByRole("heading", { name: "Votação presidencial · 2026" })).toBeVisible();
  await page.screenshot({ path: `test-results/consulta-${testInfo.project.name}.png`, fullPage: true });
  await expect(page).toHaveURL(/\/cidade\/3550308$/);
  await page.getByRole("navigation", { name: "Navegação principal" }).getByRole("link", { name: "Explorar o Brasil", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Explore os municípios brasileiros" })).toBeVisible();
  expect(erros).toEqual([]);
});

for (const codigo of ["1504752", "4212650", "4220000", "4314548", "5006275", "5101837"]) {
  test(`cobertura tabular validada chega à cidade ${codigo}`, async ({ page, request }) => {
    const response = await request.get(`/api/cobertura?municipio=${codigo}`);
    const body = await response.json();
    expect(body.disponivel).toBe(true);
    expect(body.periodo).toBe("202609");
    expect(body.municipio.pessoas).toBe(pessoas.registros[codigo].pessoas);
    await page.goto(`/?municipio=${codigo}`);
    const card = page.locator("article").filter({ has: page.getByRole("heading", { name: "Moradores em famílias que recebem Bolsa Família" }) });
    await expect(card).toContainText("09/2026");
    await expect(card).toContainText(`${pessoas.registros[codigo].pessoas.toLocaleString("pt-BR")} moradores`);
    await expect(card.getByRole("link", { name: "Ver fonte." })).toHaveAttribute("href", body.fonte);
  });
}

test("ausência na fonte continua indisponível, sem virar zero", async ({ page }) => {
  await page.route("**/api/cobertura?*", async route => {
    const original = await route.fetch();
    const body = await original.json();
    await route.fulfill({ json: { ...body, disponivel: false, municipio: { ...body.municipio, pessoas: null, cobertura_pct: null } } });
  });
  await page.goto("/?municipio=1504752");
  await expect(page.getByText("Cobertura populacional ainda não disponível para este município. Ausência não é zero.")).toBeVisible();
});

test("falha na cobertura exibe erro e permite nova tentativa", async ({ page }) => {
  await page.route("**/api/cobertura?*", route => route.abort());
  await page.goto("/?municipio=3550308");
  await expect(page.locator("main").getByRole("alert")).toContainText("Não foi possível carregar a cobertura");
  await expect(page.getByText("Ausência não é zero.", { exact: false })).toHaveCount(0);
  await page.unroute("**/api/cobertura?*");
  await page.getByRole("button", { name: "Tentar novamente", exact: true }).click();
  await expect(page.locator("#bolsa").getByText(pessoas.registros["3550308"].pessoas.toLocaleString("pt-BR"), { exact: false })).toBeVisible();
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
  await page.getByRole("combobox", { name: /^Estado/ }).selectOption("SP");
  await page.getByLabel("Resultado eleitoral").selectOption("13");
  await page.getByRole("combobox", { name: "Indicador", exact: true }).selectOption("valor_habitante");
  const lista = page.locator(".explore-results");
  const codigo = rankings.registros.filter((x: { uf: string; vencedor: string; empatados: number }) => x.uf === "SP" && x.vencedor === "13" && x.empatados === 1)
    .sort((a: { valor_centavos: number; populacao: number }, b: { valor_centavos: number; populacao: number }) => b.valor_centavos / b.populacao - a.valor_centavos / a.populacao)[0].codigo_ibge;
  await expect(lista.locator("li").first().getByRole("link")).toHaveAttribute("href", `/cidade/${codigo}`);
  await expect(lista.locator("li")).toHaveCount(10);
  for (const linha of await lista.locator("li").all()) {
    await expect(linha).toContainText("— SP");
    await expect(linha).toContainText("Lula");
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

test("metadados identificam arquivos reais e cobertura completa validada", async ({ request, page }) => {
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
  await expect(page.getByText("SHA-256:", { exact: false })).toHaveCount(fontes.arquivos.length);
  await expect(page.getByText("Todos os municípios do cadastro possuem cobertura validada", { exact: false })).toBeVisible();
  await expect(page.getByText("49.645.630 pessoas", { exact: false })).toBeVisible();
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
