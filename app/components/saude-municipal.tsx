"use client";

import { Feedback } from "@/app/components/ui/feedback";
import { Button } from "@/app/components/ui/button";
import { Card } from "@/app/components/ui/card";
import Link from "next/link";
import type { RespostaSaude } from "@/lib/saude";
import FinanciamentoSaude from "./financiamento-saude";
import TermHelp from "@/app/components/ui/term-help";
import { explicacoesEquipes } from "@/lib/health-copy";
const numero = (valor: number | null) => valor == null ? "Indisponível" : valor.toLocaleString("pt-BR");
const moeda = (valor: number | null) => valor == null ? "Indisponível" : (valor / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const periodo = (mes: string) => `${mes.slice(4)}/${mes.slice(0, 4)}`;
const data = (dia: string) => dia.slice(0, 10).split("-").reverse().join("/");
export default function SaudeMunicipal({ resposta, erro, retry }: {
    resposta: RespostaSaude | null;
    erro: string;
    retry: () => void;
}) {
    const dados = resposta?.dados;
    return <section className="ranking-section" aria-labelledby="titulo-saude" data-testid="saude-municipal">
    <div className="section-heading"><div><p className="kicker">Recursos e serviços públicos</p><h2 id="titulo-saude">Saúde na sua cidade</h2>
    <p className="hint">Veja os recursos recebidos e a estrutura de saúde. Cada indicador informa sua fonte e período.</p></div></div>
    {erro ? <Feedback kind="error"><p>{erro}</p><Button onClick={retry}>Tentar novamente</Button></Feedback>
            : !resposta ? <Feedback kind="loading">Carregando indicadores de saúde…</Feedback>
                : !dados ? <Card as="div"><p>{resposta.motivo || "Não há indicadores de saúde disponíveis para esta cidade."}</p></Card>
                    : <>
        {resposta.financiamento && <FinanciamentoSaude dados={resposta.financiamento} fontes={resposta.fontes_financiamento}/>}
        <div className="cards">
          <Card><h3>Dinheiro federal para os cuidados básicos de saúde</h3>
            <span className="kicker">Acumulado de {periodo(dados.fns.periodo_inicio)} a {periodo(dados.fns.periodo_fim)}</span>
            <div className="big money-value">{moeda(dados.fns.municipal?.valor_liquido_centavos ?? null)}</div>
            <p className="sub">Dinheiro enviado pelo governo federal ao fundo de saúde da cidade para a <strong>atenção primária</strong>: cuidados do dia a dia, como o acompanhamento nas UBS.<TermHelp term="atenção primária">É a porta de entrada para muitos cuidados do SUS. O valor mostra recursos destinados a essa área, não o número de consultas realizadas. Esse dinheiro já está incluído no total federal mostrado acima.</TermHelp></p>
            {!dados.fns.municipal && <p>Não há repasse municipal validado neste recorte. Ausência não é zero.</p>}
            <details className="health-details"><summary>Ver finalidades dos repasses</summary>
              {dados.fns.municipal ? <ul>{dados.fns.municipal.componentes.map((c, i) => <li key={i}><strong>{c.estrategia}</strong><br />{moeda(c.valor_liquido_centavos)}<small>{c.bloco}</small></li>)}</ul> : <p>Não há repasse municipal validado neste recorte. Ausência não é zero.</p>}
            </details>
            {dados.fns.estadual_sediado_na_cidade && <details className="health-details"><summary>{dados.municipio.uf === "DF" ? "Repasses ao fundo distrital registrado nesta cidade" : "Repasses ao fundo estadual registrado nesta cidade"}</summary><p>{moeda(dados.fns.estadual_sediado_na_cidade.valor_liquido_centavos)} no grupo Atenção Primária. A fonte classifica este repasse na esfera estadual. A sede do fundo não permite atribuir todo o valor aos moradores da cidade. Não somamos esse montante ao repasse municipal nem o atribuímos aos moradores.</p></details>}
            <div className="footnote">Fonte: <a href={dados.proveniencia.fns.url}>Fundo Nacional de Saúde</a>. Dados até {periodo(dados.fns.periodo_fim)}; arquivo acumulado, sem série mensal reconstruída. Valores nominais. Repasse não comprova despesa executada ou atendimento realizado. Saldos bancários não integram o total.</div>
          </Card>
          <Card><h3>Equipes com financiamento federal</h3>
            <p className="sub">Grupos de profissionais que cuidam da população. O governo federal ajuda a financiar essas equipes; isso não significa que pague todos os custos.<TermHelp term="financiamento das equipes">A tabela conta equipes com apoio financeiro federal na parcela indicada. Pode haver financiamento parcial. Uma equipe reúne profissionais; o número de equipes não é o número de médicos, de consultas ou de equipes únicas ao longo do ano.</TermHelp></p>
            {dados.aps ? <><p className="kicker">Parcela {periodo(dados.aps.parcela)} · Cadastro CNES {periodo(dados.aps.competencia_cnes)}</p>
              <div className="table-scroll health-table"><table className="data-table data-table--wide"><caption className="sr-only">Quantidade de equipes reconhecidas oficialmente e com financiamento na parcela indicada</caption><thead><tr><th>Tipo de equipe</th><th>Com registro oficial<TermHelp term="equipes homologadas">O termo oficial é homologadas: equipes com identificação reconhecida formalmente pelo Ministério da Saúde. Esse registro é diferente de receber financiamento na parcela consultada.</TermHelp></th><th>Com apoio financeiro<TermHelp term="equipes financiadas">Equipes com financiamento federal registrado nesta parcela, inclusive parcial. Não subtraia essas contagens para estimar equipes em funcionamento ou consultas disponíveis.</TermHelp></th></tr></thead><tbody>{dados.aps.equipes.map(e => <tr key={e.tipo}><td>{e.tipo}{explicacoesEquipes[e.tipo.split(" —")[0]] && <TermHelp term={e.tipo}>{explicacoesEquipes[e.tipo.split(" —")[0]]}</TermHelp>}</td><td>{numero(e.homologadas)}</td><td>{numero(e.financiadas)}</td></tr>)}</tbody></table></div>
              <p className="hint">Na fonte: “homologadas” e “financiadas”. As colunas representam situações diferentes; não some seus valores.</p>
            </> : <p>Não há observação de equipes validada para esta parcela. Ausência não é zero.</p>}
            <div className="footnote">Fonte: <a href="https://relatorioaps.saude.gov.br/">Relatórios públicos da APS</a>. Relatório de {dados.aps?.data_relatorio || data(dados.proveniencia.aps.data_extracao)}. Homologação e financiamento são estados diferentes. As quantidades financiadas podem incluir financiamento parcial e não medem consultas ou equipes únicas ao longo do ano. A parcela mais recente pode receber atualizações.</div>
          </Card>
          <Card className="health-wide"><h3>Mais Médicos na cidade</h3>
            {dados.mais_medicos.ultimo ? <><span className="kicker">Referência: {data(dados.mais_medicos.ultimo.data_referencia)}</span><div className="big">{numero(dados.mais_medicos.ultimo.vagas_ocupadas)}</div><p className="sub">Vagas ocupadas no provimento federal, conforme o registro municipal.</p>{dados.mais_medicos.ultimo.vagas_ocupadas === 0 && <p>Zero informado explicitamente no consolidado oficial para esta referência.</p>}</> : <p>{dados.mais_medicos.motivo}</p>}
            <div className="footnote">Fonte: <a href="https://dadosabertos.saude.gov.br/dataset/provimento-federal-programa-mais-medicos">Ministério da Saúde — Mais Médicos, consolidado</a>. Inclui PMMB e vagas de instituições vinculadas, conforme o <a href="https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/MaisMedicos/Dicionario_de_dados_PPF_Mais_Medicos.pdf">dicionário oficial</a>. Conta vagas ocupadas, sem deduplicação de profissionais entre vínculos; não representa todos os médicos do SUS nem quantidade de atendimentos. Registros estaduais e de distritos indígenas não são atribuídos à cidade. Extração: {data(dados.proveniencia.mais_medicos.data_extracao)}.</div>
          </Card>
        </div>
        <p className="sources">A cidade é o ponto de consulta. Serviços localizados aqui podem atender moradores de outras cidades; atendimento regional exige evidência própria. Estes dados observados não são projeções e não permitem atribuir efeitos sobre os resultados eleitorais. <Link href="/fontes">Fontes e metodologia</Link>.</p>
      </>}
  </section>;
}
