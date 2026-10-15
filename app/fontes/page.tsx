import Link from "next/link";
import { fontesPublicadas } from "@/lib/fontes";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const periodo = (mes: string) => `${mes.slice(4)}/${mes.slice(0, 4)}`;

export default async function Fontes() {
  const dados = await fontesPublicadas().catch(() => null);
  return <>
    <header className="masthead"><div className="shell"><div className="topbar"><Link className="brand" href="/">Como Eu Fico</Link><Link href="/explorar">Explorar o Brasil →</Link></div><div className="hero"><h1>Fontes e metodologia</h1><p>Períodos, unidades e limites dos dados disponíveis para consulta.</p></div></div></header>
    <main className="shell main"><section className="searchpanel">
      {!dados ? <p role="alert">Não foi possível consultar as fontes publicadas. Tente novamente mais tarde.</p> : <>
        <h2>O que os indicadores medem</h2>
        <p>{dados.limites}</p>
        <ul>{dados.fontes.map(fonte => <li key={fonte.url}><a href={fonte.url} target="_blank" rel="noreferrer">{fonte.nome}</a></li>)}</ul>
        <p>Base territorial: {dados.municipios.toLocaleString("pt-BR")} municípios. População IBGE 2026 {dados.populacao_completa ? "disponível em todos os municípios" : "com cobertura incompleta"}.</p>
        <p>CGU: série de {periodo(dados.periodo_serie_cgu[0])} a {periodo(dados.periodo_serie_cgu.at(-1)!)}. Nem todos os municípios têm todas as competências históricas. Rankings financeiros: acumulado de {periodo(dados.periodo_ranking.inicio)} a {periodo(dados.periodo_ranking.fim)}.</p>
        <p>Famílias MDS: comparação entre {dados.familias.periodos.map(periodo).join(" e ")}. Coleta: {dados.familias.coleta_utc}.</p>
        <p>Pessoas em famílias beneficiárias: fotografia de {periodo(dados.pessoas.periodo)}, dividida pela estimativa anual de população IBGE 2026. Não representa média anual. Extração: {dados.pessoas.data_extracao}.</p>
        <h2>Municípios sem cobertura populacional validada</h2>
        <p>{dados.pessoas.municipios_com_dado.toLocaleString("pt-BR")} municípios com dado. Os demais não entram nos rankings de cobertura:</p>
        <ul>{dados.pessoas.municipios_sem_dado.map(m => <li key={m.codigo_ibge}><Link href={`/?municipio=${m.codigo_ibge}`}>{m.nome} — {m.uf}</Link> (IBGE {m.codigo_ibge})</li>)}</ul>
        <p>Os totais municipais disponíveis não devem ser apresentados como cobertura nacional completa. Os seis casos exigem uma fonte oficial validada antes de qualquer preenchimento.</p>
        <h2>Arquivos e versões</h2>
        <p>Saúde: consulta em {dados.saude.municipios_referencia.toLocaleString("pt-BR")} municípios. Os valores são observados, sem projeção. Repasses FNS acumulados de janeiro a julho de 2026; equipes e Mais Médicos têm suas próprias datas indicadas na página de cada cidade. O consolidado do Mais Médicos mede vagas ocupadas no provimento federal, incluindo instituições vinculadas; não é uma contagem deduplicada de todos os médicos do SUS. Repasses a fundos estaduais registrados na cidade ficam separados dos repasses municipais. Financiamento, estrutura e atendimento são medidas distintas.</p>
        <p>Cobertura por indicador: FNS com repasse municipal validado em {dados.saude.cobertura.fns.com_dado.toLocaleString("pt-BR")} municípios; equipes APS em {dados.saude.cobertura.aps.com_dado.toLocaleString("pt-BR")}; vagas ocupadas no Mais Médicos em {dados.saude.cobertura.mais_medicos.com_dado.toLocaleString("pt-BR")}. Zeros explícitos da fonte são preservados; ausência de registro permanece indisponível.</p>
        {dados.saude.cobertura.fns.sem_dado.length > 0 && <p>Sem repasse municipal FNS validado neste recorte: {dados.saude.cobertura.fns.sem_dado.map((codigo, i) => <span key={codigo}>{i > 0 ? ", " : ""}<Link href={`/?municipio=${codigo}`}>IBGE {codigo}</Link></span>)}. Isso não significa ausência de financiamento da saúde.</p>}
        <p>{dados.commit ? `Commit desta versão: ${dados.commit}.` : "Commit do deploy não informado neste ambiente; os hashes abaixo identificam os arquivos em uso."}</p>
        <ul className="snapshot-list">{dados.arquivos.map(arquivo => <li key={arquivo.arquivo}><a href={arquivo.url} target="_blank" rel="noreferrer">{arquivo.arquivo}</a><br /><code>SHA-256: {arquivo.sha256}</code></li>)}</ul>
        <p>Os snapshots MDS preservam URLs e hashes das respostas oficiais. O ranking registra as origens TSE, CGU e IBGE; os arquivos brutos e o SQLite pertencem ao pipeline de dados, separado da aplicação web.</p>
        <p><a href="/api/fontes">Consultar metadados em JSON</a></p>
      </>}
    </section></main>
  </>;
}
