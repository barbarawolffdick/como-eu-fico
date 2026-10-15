"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { RespostaSaude } from "@/lib/saude";

const numero = (valor: number | null) => valor == null ? "Indisponível" : valor.toLocaleString("pt-BR");
const moeda = (valor: number | null) => valor == null ? "Indisponível" : (valor / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const periodo = (mes: string) => `${mes.slice(4)}/${mes.slice(0, 4)}`;
const data = (dia: string) => dia.slice(0, 10).split("-").reverse().join("/");

export default function SaudeMunicipal({ codigo }: { codigo: string }) {
  const [resposta, setResposta] = useState<RespostaSaude | null>(null);
  const [erro, setErro] = useState("");
  const [tentativa, setTentativa] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setResposta(null); setErro("");
    fetch(`/api/saude/${codigo}`, { signal: controller.signal, cache: "no-store" })
      .then(async r => { if (!r.ok) throw Error("Falha na consulta"); return await r.json() as RespostaSaude; })
      .then(r => { if (!controller.signal.aborted) setResposta(r); })
      .catch(() => { if (!controller.signal.aborted) setErro("Não foi possível carregar os indicadores de saúde. Tente novamente."); });
    return () => controller.abort();
  }, [codigo, tentativa]);
  const dados = resposta?.dados;
  return <section className="ranking-section" aria-labelledby="titulo-saude" data-testid="saude-municipal">
    <h2 id="titulo-saude">Saúde na sua cidade</h2>
    <p className="hint">Consulta disponível para todos os municípios. Recursos, equipes e vagas médicas têm fontes e datas próprias; dados ausentes são indicados em cada cartão.</p>
    {erro ? <div className="notice" role="alert"><p>{erro}</p><button onClick={() => setTentativa(x => x + 1)}>Tentar novamente</button></div>
      : !resposta ? <p role="status">Carregando indicadores de saúde…</p>
      : !dados ? <div className="card"><p>{resposta.motivo || "Não há indicadores de saúde disponíveis para esta cidade."}</p></div>
      : <>
        <div className="cards">
          <article className="card"><h3>Repasses federais para atenção primária</h3>
            <span className="kicker">Acumulado de {periodo(dados.fns.periodo_inicio)} a {periodo(dados.fns.periodo_fim)}</span>
            <div className="big" style={{ marginTop: 12 }}>{moeda(dados.fns.municipal?.valor_liquido_centavos ?? null)}</div>
            <p className="sub">Valor líquido registrado para o fundo municipal de saúde, no grupo Atenção Primária.</p>
            {!dados.fns.municipal && <p>Não há repasse municipal validado neste recorte. Ausência não é zero.</p>}
            <details className="health-details"><summary>Ver finalidades dos repasses</summary>
              {dados.fns.municipal ? <ul>{dados.fns.municipal.componentes.map((c, i) => <li key={i}><strong>{c.estrategia}</strong><br />{moeda(c.valor_liquido_centavos)}<small>{c.bloco}</small></li>)}</ul> : <p>Não há repasse municipal validado neste recorte. Ausência não é zero.</p>}
            </details>
            {dados.fns.estadual_sediado_na_cidade && <details className="health-details"><summary>{dados.municipio.uf === "DF" ? "Repasses ao fundo distrital registrado nesta cidade" : "Repasses ao fundo estadual registrado nesta cidade"}</summary><p>{moeda(dados.fns.estadual_sediado_na_cidade.valor_liquido_centavos)} no grupo Atenção Primária. A fonte classifica este repasse na esfera estadual. A sede do fundo não permite atribuir todo o valor aos moradores da cidade. Não somamos esse montante ao repasse municipal nem o atribuímos aos moradores.</p></details>}
            <div className="footnote">Fonte: <a href={dados.proveniencia.fns.url}>Fundo Nacional de Saúde</a>. Dados até {periodo(dados.fns.periodo_fim)}; arquivo acumulado, sem série mensal reconstruída. Valores nominais. Repasse não comprova despesa executada ou atendimento realizado. Saldos bancários não integram o total.</div>
          </article>
          <article className="card"><h3>Equipes com financiamento federal</h3>
            {dados.aps ? <><p className="kicker">Parcela {periodo(dados.aps.parcela)} · Cadastro CNES {periodo(dados.aps.competencia_cnes)}</p>
              <div className="ranking-scroll health-table"><table className="ranking-table"><thead><tr><th>Equipe</th><th>Homologadas</th><th>Financiadas</th></tr></thead><tbody>{dados.aps.equipes.map(e => <tr key={e.tipo}><td>{e.tipo}</td><td>{numero(e.homologadas)}</td><td>{numero(e.financiadas)}</td></tr>)}</tbody></table></div>
            </> : <p>Não há observação de equipes validada para esta parcela. Ausência não é zero.</p>}
            <div className="footnote">Fonte: <a href="https://relatorioaps.saude.gov.br/">Relatórios públicos da APS</a>. Relatório de {dados.aps?.data_relatorio || data(dados.proveniencia.aps.data_extracao)}. Homologação e financiamento são estados diferentes. As quantidades financiadas podem incluir financiamento parcial e não medem consultas ou equipes únicas ao longo do ano. A parcela mais recente pode receber atualizações.</div>
          </article>
          <article className="card"><h3>Mais Médicos na cidade</h3>
            {dados.mais_medicos.ultimo ? <><span className="kicker">Referência: {data(dados.mais_medicos.ultimo.data_referencia)}</span><div className="big" style={{ marginTop: 12 }}>{numero(dados.mais_medicos.ultimo.vagas_ocupadas)}</div><p className="sub">Vagas ocupadas no provimento federal, conforme o registro municipal.</p>{dados.mais_medicos.ultimo.vagas_ocupadas === 0 && <p>Zero informado explicitamente no consolidado oficial para esta referência.</p>}</> : <p>{dados.mais_medicos.motivo}</p>}
            <div className="footnote">Fonte: <a href="https://dadosabertos.saude.gov.br/dataset/provimento-federal-programa-mais-medicos">Ministério da Saúde — Mais Médicos, consolidado</a>. Inclui PMMB e vagas de instituições vinculadas, conforme o <a href="https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/MaisMedicos/Dicionario_de_dados_PPF_Mais_Medicos.pdf">dicionário oficial</a>. Conta vagas ocupadas, sem deduplicação de profissionais entre vínculos; não representa todos os médicos do SUS nem quantidade de atendimentos. Registros estaduais e de distritos indígenas não são atribuídos à cidade. Extração: {data(dados.proveniencia.mais_medicos.data_extracao)}.</div>
          </article>
        </div>
        <p className="sources">A cidade é o ponto de consulta. Serviços localizados aqui podem atender moradores de outras cidades; atendimento regional exige evidência própria. Estes dados observados não são projeções e não permitem atribuir efeitos sobre os resultados eleitorais. <Link href="/fontes">Fontes e metodologia</Link>.</p>
      </>}
  </section>;
}
