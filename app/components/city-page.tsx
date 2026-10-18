"use client";

import { type BeneficiariosCidade } from "@/lib/bolsa-familia";
import { Feedback } from "@/app/components/ui/feedback";
import { Button, ActionLink } from "@/app/components/ui/button";
import { Card } from "@/app/components/ui/card";
import Link from "next/link";
import { ArrowUpRight, MapPin } from "lucide-react";
import CitySearch from "./city-search";
import CitySections from "./city-sections";
import DinheiroFederal, { SectionHeading } from "./dinheiro-federal";
import SaudeFederal from "./saude-federal";
import BolsaFederal, { type Cobertura } from "./bolsa-federal";
import { useResource } from "../hooks/use-resource";
import type { RespostaSaude } from "@/lib/saude";
import type { RespostaDinheiroFederal, RespostaRegioes } from "@/lib/dinheiro-federal";
import { nomeCandidato as candidato } from "@/lib/eleicoes";
type Municipio = {
    codigo_ibge: string;
    nome: string | null;
    uf: string | null;
    populacao: number | null;
    ano_populacao: number | null;
};
type Bolsa = {
    mes_competencia: string;
    parcelas: number;
    valor_centavos: number;
};
type Voto = {
    candidato: string;
    votos: number;
};
type Detalhe = {
    municipio: Municipio;
    bolsa_familia: Bolsa[];
    votos_presidenciais: Voto[];
    eleitoral_disponivel: boolean;
};
const br = new Intl.NumberFormat("pt-BR");
const percentual = (n: number) => n.toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + "%";
export default function CityPage({ codigo }: {
    codigo: string;
}) {
    const city = useResource<Detalhe>("/api/municipios/" + codigo, "Não foi possível consultar esta cidade. Confira o código ou tente novamente.");
    const federal = useResource<RespostaDinheiroFederal>("/api/dinheiro-federal/" + codigo, "Não foi possível carregar o dinheiro federal da cidade.");
    const regioes = useResource<RespostaRegioes>("/api/dinheiro-federal/regioes", "Não foi possível carregar a comparação entre regiões.");
    const coverage = useResource<Cobertura>("/api/cobertura?municipio=" + codigo, "Não foi possível carregar a cobertura. Tente novamente.");
    const health = useResource<RespostaSaude>("/api/saude/" + codigo, "Não foi possível carregar os indicadores de saúde. Tente novamente.");
    const beneficiaries = useResource<BeneficiariosCidade>("/api/beneficiarios/" + codigo, "Não foi possível consultar as contagens de pessoas e famílias.");
    const detail = city.data;
    const votos = detail?.eleitoral_disponivel ? [...detail.votos_presidenciais].sort((a, b) => b.votos - a.votos || a.candidato.localeCompare(b.candidato)) : [];
    const totalVotos = votos.reduce((s, v) => s + v.votos, 0);
    const lider = votos[0];
    const empate = !!lider && votos.filter(v => v.votos === lider.votos).length > 1;
    const f = federal.data;
    return <main id="conteudo" tabIndex={-1} className="city-page">
    <div className="shell"><div className="city-breadcrumb"><Link href="/">Início</Link><span aria-hidden="true">/</span><span>Minha cidade</span></div>
      {city.error ? <Feedback kind="error"><h1>Não foi possível abrir a cidade</h1><p>{city.error}</p><Button onClick={city.retry}>Tentar novamente</Button><p><Link href="/">Buscar outra cidade →</Link></p></Feedback> : !detail ? <Feedback className="city-loading" kind="loading">Consultando dados do município…</Feedback> : <>
        <header className="city-heading"><div><p className="kicker"><MapPin size={14} aria-hidden="true"/> {f ? `${f.cidade.municipio.uf} · Região de ${f.cidade.regiao_imediata.nome}` : "Sua cidade em perspectiva"}</p><h1>{detail.municipio.nome ?? "Município"} — {detail.municipio.uf ?? "UF"}</h1>
          <p className="population">{detail.municipio.populacao != null ? "População estimada: " + br.format(detail.municipio.populacao) + " habitantes · IBGE " + detail.municipio.ano_populacao : "População IBGE ainda não disponível nesta base"}</p>
          <p className="hint">{lider && totalVotos > 0 && !empate ? `${candidato(lider.candidato)} teve ${percentual(100 * lider.votos / totalVotos)} dos votos no 1º turno de 2026 · ` : ""}Código IBGE {codigo} · Cada indicador tem seu próprio período de referência.</p><ActionLink href={"/comparar?a=" + codigo} className="city-compare-action">Comparar com outra cidade <ArrowUpRight size={17} aria-hidden="true"/></ActionLink></div><CitySearch compact/></header>
        <CitySections />
        {federal.error ? <section id="quanto" aria-labelledby="quanto-title" className="federal-section"><SectionHeading id="quanto-title" kicker="1 · Quanto chega" title="Quanto dinheiro federal chegou à cidade?" />
            <Feedback kind="error" action={<Button onClick={federal.retry}>Tentar novamente</Button>}>{federal.error}</Feedback></section>
          : !f ? <Feedback kind="loading">Calculando o dinheiro federal da cidade…</Feedback>
          : <DinheiroFederal key={codigo} ano={f.ano} pibEstimado={f.pib.estimado} pibAnoFonte={f.pib.ano_fonte} cidade={f.cidade}
              votos={detail.eleitoral_disponivel ? detail.votos_presidenciais : []} regioes={regioes} />}
        <SaudeFederal saude={health} emendas={f?.emendas ?? null} ano={f?.ano ?? 2025} />
        <BolsaFederal meses={detail.bolsa_familia} cobertura={coverage} beneficiarios={beneficiaries} ano={f?.ano ?? 2025} />
        <Card as="section" tone="muted" id="fontes-cidade" className="city-sources" aria-labelledby="fontes-title"><div><p className="kicker">Confira a informação</p><h2 id="fontes-title">Os dados têm origem. E limites.</h2><p>Fontes: TSE (votação), INSS e Ministério da Previdência (benefícios), Tesouro Nacional (FPM), CGU (Bolsa Família e emendas parlamentares), MDS (pessoas e famílias), Câmara dos Deputados e Senado (partidos), IBGE (território, população, PIB e IPCA), Fundo Nacional de Saúde, SIOPS e CNES (saúde). Os períodos e conceitos das fontes são independentes. Estes números mostram dinheiro que chega à cidade; não medem quanto fica na economia local nem permitem atribuir resultados eleitorais às políticas públicas.</p></div><ActionLink href="/fontes">Fontes e metodologia <ArrowUpRight size={18} aria-hidden="true"/></ActionLink></Card>
      </>}
    </div>
  </main>;
}
