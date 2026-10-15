import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { createHash } from "node:crypto";
import { NextResponse } from "next/server";
import { pessoasTabulares, type BeneficiariosCidade } from "@/lib/bolsa-familia";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const digest = (s: string) => createHash("sha256").update(s).digest("hex");

export async function GET(_request: Request, { params }: { params: Promise<{ codigo_ibge: string }> }) {
  const { codigo_ibge } = await params;
  if (!/^\d{7}$/.test(codigo_ibge)) return NextResponse.json({ detail: "Código IBGE inválido" }, { status: 400 });
  try {
    const [territorio, familiasRaw, publicado, mensal] = await Promise.all([
      readFile(join(process.cwd(), "data/public/rankings_2026.json"), "utf8").then(JSON.parse),
      readFile(join(process.cwd(), "data/public/familias_mds.json"), "utf8"),
      readFile(join(process.cwd(), "data/public/pessoas_mds.json"), "utf8").then(JSON.parse),
      readFile(join(process.cwd(), "data/public/pessoas_mds_mensal.json"), "utf8").then(JSON.parse),
    ]);
    const cidade = territorio.registros.find((r: { codigo_ibge: string }) => r.codigo_ibge === codigo_ibge);
    if (!cidade) return NextResponse.json({ detail: "Município não encontrado" }, { status: 404 });
    const familias = JSON.parse(familiasRaw);
    if (familias.unidade !== "familias_beneficiarias" || mensal.esquema !== 1 || mensal.unidade !== "pessoas_em_familias_beneficiarias") throw Error("Unidade incompatível");
    let pessoas: Record<string, number> = mensal.registros[codigo_ibge]?.periodos ?? {};
    let origem = mensal.registros[codigo_ibge]?.proveniencia ?? null;
    let aviso: string | null = null;
    if (!origem) {
      try {
        const url = new URL(publicado.pagina_fonte);
        if (url.origin !== "https://aplicacoes.cidadania.gov.br" || url.pathname !== "/vis/data3/v.php") throw Error("Fonte inesperada");
        url.searchParams.set("ag", "m"); url.searchParams.set("codigo", codigo_ibge);
        const response = await fetch(url, { headers: { "User-Agent": "ComoEuFico/1.0", Accept: "text/html" }, next: { revalidate: 86400 }, signal: AbortSignal.timeout(15000) });
        if (!response.ok || new URL(response.url).origin !== url.origin) throw Error("Fonte indisponível");
        const raw = await response.text();
        const aliases = (publicado.correspondencias_explicitas ?? []).filter((a: { codigo_ibge: string }) => a.codigo_ibge === codigo_ibge)
          .map((a: { nome_mds_normalizado: string }) => a.nome_mds_normalizado);
        pessoas = pessoasTabulares(raw, { ...cidade, aliases });
        if (pessoas[publicado.periodo] !== publicado.registros[codigo_ibge]?.pessoas) throw Error("Revisão da fonte exige reconciliação");
        origem = { url: url.href, sha256: digest(raw), data_extracao: new Date().toISOString() };
      } catch {
        pessoas = {}; origem = null;
        aviso = "Não foi possível validar a série de pessoas desta cidade. A média por família continua disponível nos meses com contagem de famílias.";
      }
    }
    const meses = [...new Set([...Object.keys(pessoas), ...familias.periodos])].sort();
    const periodos = Object.fromEntries(meses.map(mes => {
      const f = familias.registros[mes]?.[codigo_ibge];
      return [mes, { pessoas: pessoas[mes] ?? null, familias: Number.isSafeInteger(f) && f >= 0 ? f : null }];
    }));
    const result: BeneficiariosCidade = { codigo_ibge, periodos, pessoas_disponiveis: !!origem, aviso,
      fontes: { pessoas: origem, familias: { arquivo: "familias_mds.json", sha256: digest(familiasRaw) } } };
    return NextResponse.json(result);
  } catch {
    return NextResponse.json({ detail: "Não foi possível carregar as contagens de beneficiários." }, { status: 503 });
  }
}
