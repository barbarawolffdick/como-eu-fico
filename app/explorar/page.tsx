import type { Metadata } from "next";
import { ActionLink } from "../components/ui/button";
import { Feedback } from "../components/ui/feedback";
import ExploreBrazil from "../components/explore-brazil";
import { lerFiltros } from "@/lib/explorar";

export const metadata: Metadata = { title: "Explorar o Brasil — Como Eu Fico", description: "Explore saúde, Bolsa Família e voto por região, estado e perfil eleitoral, com fontes e períodos explícitos." };

export default async function Explorar({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) if (typeof value === "string") query.set(key, value);
  let filters;
  try { filters = lerFiltros(query); }
  catch { return <main id="conteudo" tabIndex={-1} className="shell explore-page"><Feedback kind="error"><h1>Confira os filtros da exploração</h1><p>Há uma opção inválida ou um estado fora da região escolhida.</p><ActionLink href="/explorar">Começar uma nova exploração →</ActionLink></Feedback></main>; }
  return <ExploreBrazil filters={filters} />;
}
