"use client";

import { Card } from "@/app/components/ui/card";
import { Feedback } from "@/app/components/ui/feedback";
import { Button } from "@/app/components/ui/button";
import { SectionHeading } from "./dinheiro-federal";
import { LinhaMensal, Pessoas, curto, numero } from "./graficos";
import { mediaPorBeneficiario, type BeneficiariosCidade } from "@/lib/bolsa-familia";
import { AjudaBolsa } from "./alcance-bolsa";

type Mes = { mes_competencia: string; parcelas: number; valor_centavos: number };
export type Cobertura = { periodo: string; fonte: string; disponivel: boolean; municipio: { pessoas: number | null; populacao: number; cobertura_pct: number | null } };
const competencia = (m: string) => m.slice(4, 6) + "/" + m.slice(0, 4);
const moeda = (centavos: number) => (centavos / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

export default function BolsaFederal({ meses, cobertura, beneficiarios, ano }: {
  meses: Mes[];
  cobertura: { data: Cobertura | null; error: string; retry: () => void };
  beneficiarios: { data: BeneficiariosCidade | null; error: string; retry: () => void };
  ano: number;
}) {
  const serie = [...meses].sort((a, b) => a.mes_competencia.localeCompare(b.mes_competencia));
  const ultimo = serie.at(-1);
  const doAno = serie.filter(m => m.mes_competencia.startsWith(String(ano)));
  const anoCompleto = doAno.length === 12;
  const c = cobertura.data;
  const pct = c?.disponivel ? c.municipio.cobertura_pct : null;
  const denominadores = ultimo ? beneficiarios.data?.periodos[ultimo.mes_competencia] : null;
  const mediaPessoa = mediaPorBeneficiario(ultimo?.valor_centavos, denominadores?.pessoas);
  const mediaFamilia = mediaPorBeneficiario(ultimo?.valor_centavos, denominadores?.familias);
  return <section id="bolsa" aria-labelledby="bolsa-title" className="federal-section">
    <SectionHeading id="bolsa-title" kicker="7 · Bolsa Família" title="Quantas pessoas vivem em famílias do Bolsa Família?" />
    <div className="federal-grid">
      <Card className="federal-chart">
        {cobertura.error ? <Feedback kind="error" action={<Button onClick={cobertura.retry}>Tentar novamente</Button>}>{cobertura.error}</Feedback>
          : !c ? <Feedback kind="loading">Carregando cobertura…</Feedback>
          : pct != null ? <>
            <h3>Moradores em famílias que recebem Bolsa Família</h3>
            <p className="federal-sentence"><b>{numero(Math.round(pct))} em cada 100 moradores</b> vivem em famílias que recebem o Bolsa Família.</p>
            <Pessoas n={Math.round(pct)} rotulo={`${numero(pct, 1)}% dos moradores (${numero(c.municipio.pessoas ?? 0)} pessoas) vivem em famílias beneficiárias`} />
            {c.municipio.pessoas != null && <p><b>{numero(c.municipio.pessoas)} moradores</b> em famílias beneficiárias, de uma população estimada de {numero(c.municipio.populacao)} pessoas ({competencia(c.periodo)}).</p>}
            <p className="hint">Cada figura representa 1 em cada 100 moradores. O benefício é da família; o pagamento é feito ao titular. <AjudaBolsa /></p>
          </> : <><h3>Moradores em famílias que recebem Bolsa Família</h3><p>Cobertura populacional ainda não disponível para este município. Ausência não é zero.</p></>}
        <p className="footnote">Fonte: MDS / VIS DATA 3. População: IBGE 2026. É a proporção de moradores que integram famílias beneficiárias, não de titulares que recebem pagamentos. {c?.fonte && <a href={c.fonte} target="_blank" rel="noreferrer">Ver fonte.</a>}</p>
      </Card>
      <Card className="federal-chart" data-testid="media-bolsa-cidade">
        <h3>Quanto chega por pessoa e por família</h3>
        <p className="federal-lead">
          {anoCompleto ? <>Em {ano}, o programa somou <b>{curto(doAno.reduce((s, m) => s + m.valor_centavos, 0))}</b> na cidade.</> : null}
        </p>
        <div className="federal-rows">
          <div className="federal-row"><span>Valor por pessoa da família</span><b>{!beneficiaries(beneficiarios) ? "Carregando…" : mediaPessoa == null ? "Indisponível" : moeda(mediaPessoa)}</b>
            <p className="hint">{ultimo ? competencia(ultimo.mes_competencia) : "Competência indisponível"} · média calculada: valor do mês dividido somente pelos moradores de famílias beneficiárias no mesmo mês.{denominadores?.pessoas != null ? ` Base: ${numero(denominadores.pessoas)} pessoas.` : ""}</p></div>
          {mediaFamilia != null && <div className="federal-row"><span>Valor por família</span><b>{moeda(mediaFamilia)}</b>
            <p className="hint">{numero(denominadores!.familias!)} famílias no mesmo mês{denominadores?.pessoas != null && denominadores.familias ? `, com média de ${numero(denominadores.pessoas / denominadores.familias, 1)} pessoas por família` : ""}.</p></div>}
        </div>
        {mediaPessoa == null && beneficiarios.data && <p className="hint">Sem contagem de pessoas validada para o mês do valor. Não usamos a população inteira nem pessoas de outro mês.</p>}
        {beneficiarios.error && <Feedback kind="error" action={<Button onClick={beneficiarios.retry}>Tentar novamente</Button>}>{beneficiarios.error}</Feedback>}
        <p className="footnote">Fontes: valores CGU e pessoas/famílias MDS, na competência indicada. É uma divisão dos totais municipais; não é um pagamento separado para cada integrante nem o valor exato recebido por cada família. Os registros não comprovam saque.</p>
      </Card>
    </div>
    <Card className="federal-chart benefit-history">
      <h3>Quanto chegou por mês</h3>
      {ultimo ? <>
        <p>Última competência: {competencia(ultimo.mes_competencia)}, <b>{moeda(ultimo.valor_centavos)}</b> em {numero(ultimo.parcelas)} registros de parcelas.{anoCompleto ? ` Em média, ${curto(doAno.reduce((s, m) => s + m.valor_centavos, 0) / 12)} por mês em ${ano}.` : ""}</p>
        <LinhaMensal meses={serie.map(m => ({ mes: m.mes_competencia, valor: m.valor_centavos }))} />
        <details className="federal-details"><summary>Ver tabela</summary>
          <div className="table-scroll"><table className="data-table">
            <caption className="sr-only">Valores mensais do Bolsa Família na cidade</caption>
            <thead><tr><th scope="col">Competência</th><th scope="col">Valor</th><th scope="col">Parcelas</th></tr></thead>
            <tbody>{serie.map(m => <tr key={m.mes_competencia}><th scope="row">{competencia(m.mes_competencia)}</th><td>{moeda(m.valor_centavos)}</td><td>{numero(m.parcelas)}</td></tr>)}</tbody>
          </table></div>
        </details>
        <p className="hint">Acumulado das {serie.length} competências: {moeda(serie.reduce((s, p) => s + p.valor_centavos, 0))}</p>
      </> : <p>Sem registros mensais disponíveis. Ausência não significa zero.</p>}
      <p className="footnote">Fonte: CGU / Portal da Transparência. Valores agregados por competência. Parcelas são registros de parcelas do benefício na base CGU, não famílias únicas. Os registros não comprovam saque.</p>
    </Card>
  </section>;
}

const beneficiaries = (b: { data: BeneficiariosCidade | null; error: string }) => !!b.data || !!b.error;
