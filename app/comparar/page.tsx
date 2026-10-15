import type { Metadata } from "next";
import { ActionLink } from "../components/ui/button";
import { Feedback } from "../components/ui/feedback";
import CompareCities from "../components/compare-cities";

export const metadata: Metadata = { title: "Compare cidades — Como Eu Fico", description: "Voto, saúde e Bolsa Família de duas cidades, com unidades e períodos explícitos." };

export default async function Comparar({ searchParams }: { searchParams: Promise<{ a?: string; b?: string; modo?: string; bolsa?: string }> }) {
  const params = await searchParams;
  const a = params.a ?? "3550308";
  const b = params.b ?? (a === "3304557" ? "3550308" : "3304557");
  if (!/^\d{7}$/.test(a) || !/^\d{7}$/.test(b)) return <main id="conteudo" tabIndex={-1} className="shell compare-page"><Feedback kind="error"><h1>Confira as cidades do link</h1><p>Escolha cidades por seus nomes na busca para começar a comparação.</p><ActionLink href="/comparar">Abrir a comparação →</ActionLink></Feedback></main>;
  return <CompareCities a={a} b={b} mode={params.modo === "total" ? "total" : "habitante"} bolsaMode={params.bolsa === "total" || params.bolsa === "familia" ? params.bolsa : "pessoa"} example={!params.a && !params.b} />;
}
