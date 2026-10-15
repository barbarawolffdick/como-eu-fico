import { Card } from "@/app/components/ui/card";
import { Feedback } from "@/app/components/ui/feedback";
import Link from "next/link";
import { fontesPublicadas } from "@/lib/fontes";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const periodo = (mes: string) => `${mes.slice(4)}/${mes.slice(0, 4)}`;
export default async function Fontes() {
    const dados = await fontesPublicadas().catch(() => null);
    return <>
    <header className="masthead"><div className="shell"><div className="hero"><h1>Fontes e metodologia</h1><p>Períodos, unidades e limites dos dados disponíveis para consulta.</p></div></div></header>
    <main id="conteudo" tabIndex={-1} className="shell main"><Card className="searchpanel" as="section">
      {!dados ? <Feedback kind="error">Não foi possível consultar as fontes publicadas. Tente novamente mais tarde.</Feedback> : <>
        <h2>O que os indicadores medem</h2>
        <p>{dados.limites}</p>
        <ul>{dados.fontes.map(fonte => <li key={fonte.url}><a href={fonte.url} target="_blank" rel="noreferrer">{fonte.nome}</a></li>)}</ul>
        <p>Base territorial: {dados.municipios.toLocaleString("pt-BR")} municípios. População IBGE 2026 {dados.populacao_completa ? "disponível em todos os municípios" : "com cobertura incompleta"}.</p>
        <p>CGU: série de {periodo(dados.periodo_serie_cgu[0])} a {periodo(dados.periodo_serie_cgu.at(-1)!)}. Nem todos os municípios têm todas as competências históricas. Rankings financeiros: acumulado de {periodo(dados.periodo_ranking.inicio)} a {periodo(dados.periodo_ranking.fim)}.</p>
        <p>Famílias MDS: comparação entre {dados.familias.periodos.map(periodo).join(" e ")}. Coleta: {dados.familias.coleta_utc}.</p>
        <p>Pessoas em famílias beneficiárias: fotografia de {periodo(dados.pessoas.periodo)}, dividida pela estimativa anual de população IBGE 2026. Não representa média anual. Extração: {dados.pessoas.data_extracao}.</p>
        <h2>Cobertura territorial do Bolsa Família</h2>
        <p>{dados.pessoas.municipios_com_dado.toLocaleString("pt-BR")} municípios com dado de pessoas em famílias beneficiárias.</p>
        {dados.pessoas.municipios_sem_dado.length > 0 ? <>
          <p>Os seguintes municípios continuam indisponíveis e não entram nos rankings de cobertura:</p>
          <ul>{dados.pessoas.municipios_sem_dado.map(m => <li key={m.codigo_ibge}><Link href={`/cidade/${m.codigo_ibge}`}>{m.nome} — {m.uf}</Link> (IBGE {m.codigo_ibge})</li>)}</ul>
        </> : <p>Todos os municípios do cadastro possuem cobertura validada para esta competência. As seis cidades ausentes no mapa do MDS foram completadas pela consulta tabular oficial por código IBGE, sem estimativas.</p>}
        {dados.pessoas.complemento_tabular && <p>Conferência tabular: {dados.pessoas.complemento_tabular.validacao.total_pessoas.toLocaleString("pt-BR")} pessoas; a soma municipal e cada uma das três faixas de renda fecham com o total Brasil de {periodo(dados.pessoas.complemento_tabular.periodo)}. O período antes exibido como agosto foi corrigido para setembro/2026 após essa conferência. Validação: {dados.pessoas.data_validacao_tabular}.</p>}
        <h2>Médias do Bolsa Família para quem faz parte do programa</h2>
        <p>O valor por pessoa da família divide os valores registrados na CGU somente pelas pessoas em famílias beneficiárias do mesmo mês. A média por família usa a contagem de famílias MDS da mesma competência. Não dividimos esses indicadores pela população inteira, pelo número de parcelas ou por pessoas de outro mês.</p>
        <p>O histórico tabular de pessoas possui {dados.pessoas_mensais.municipios_com_dado} cidades previamente verificadas, nas competências {dados.pessoas_mensais.periodos.map(periodo).join(" e ")}; seu recorte histórico é parcial, separado da cobertura nacional de setembro. Outras cidades são consultadas individualmente no MDS, com validação territorial, mensal e das três faixas. Uma falha ou lacuna impede a média por pessoa; não vira zero. A resposta de cada cidade informa fonte e hash em <code>/api/beneficiarios/IBGE7</code>.</p>
        <p>As médias são divisões de totais municipais: não informam o valor exato de cada família, não significam pagamentos separados para cada integrante e não comprovam saque.</p>
        <h2>Arquivos e versões</h2>
        <p>Saúde: consulta em {dados.saude.municipios_referencia.toLocaleString("pt-BR")} municípios. Os valores são observados, sem projeção. Repasses FNS acumulados de janeiro a julho de 2026; equipes e Mais Médicos têm suas próprias datas indicadas na página de cada cidade. O consolidado do Mais Médicos mede vagas ocupadas no provimento federal, incluindo instituições vinculadas; não é uma contagem deduplicada de todos os médicos do SUS. Repasses a fundos estaduais registrados na cidade ficam separados dos repasses municipais. Financiamento, estrutura e atendimento são medidas distintas.</p>
        <p>Cobertura por indicador: FNS com repasse municipal validado em {dados.saude.cobertura.fns.com_dado.toLocaleString("pt-BR")} municípios; equipes APS em {dados.saude.cobertura.aps.com_dado.toLocaleString("pt-BR")}; vagas ocupadas no Mais Médicos em {dados.saude.cobertura.mais_medicos.com_dado.toLocaleString("pt-BR")}. Zeros explícitos da fonte são preservados; ausência de registro permanece indisponível.</p>
        {dados.saude.cobertura.fns.sem_dado.length > 0 && <p>Sem repasse municipal FNS validado neste recorte: {dados.saude.cobertura.fns.sem_dado.map((codigo, i) => <span key={codigo}>{i > 0 ? ", " : ""}<Link href={`/cidade/${codigo}`}>IBGE {codigo}</Link></span>)}. Isso não significa ausência de financiamento da saúde.</p>}
        <h2>Financiamento e estrutura de saúde</h2>
        <p>Transferências federais fundo a fundo de todas as áreas, com finalidades e emendas identificadas na planilha. O acumulado de 2026 vai até julho. Valor por habitante usa a população IBGE 2026; não é pagamento individual. A evolução compara 2024 e 2025 completos, em valores nominais, sem comparar o parcial de 2026 com um ano inteiro. Emendas já integram o total.</p>
        <p>SIOPS: despesas liquidadas e pagas do exercício 2025, 6º bimestre, por fonte de financiamento. Não são receitas recebidas nem devem ser somadas ao FNS. CNES: cadastro de estabelecimentos consultado nesta coleta, sem competência mensal informada no arquivo; leitos e equipamentos com referência agosto/2026. Localização do serviço não identifica residência dos atendidos nem comprova financiamento por um repasse específico.</p>
        <p>Cobertura dos recortes publicados: FNS 2026 em {dados.financiamento_saude.cobertura.fns_2026.toLocaleString("pt-BR")} municípios; despesas municipais SIOPS em {dados.financiamento_saude.cobertura.siops.toLocaleString("pt-BR")}; estabelecimentos ativos com atendimento ambulatorial SUS informado em {dados.financiamento_saude.cobertura.cnes.toLocaleString("pt-BR")}; registros hospitalares em {dados.financiamento_saude.cobertura.leitos.toLocaleString("pt-BR")}. Ausência de registro não significa ausência de serviço. Traços do Tabnet permanecem indisponíveis. A proveniência JSON preserva os parâmetros das duas consultas de equipamentos.</p>
        <p>{dados.commit ? `Commit desta versão: ${dados.commit}.` : "Commit do deploy não informado neste ambiente; os hashes abaixo identificam os arquivos em uso."}</p>
        <ul className="snapshot-list">{dados.arquivos.map(arquivo => <li key={arquivo.arquivo}><a href={arquivo.url} target="_blank" rel="noreferrer">{arquivo.arquivo}</a><br /><code>SHA-256: {arquivo.sha256}</code></li>)}</ul>
        <p>Os snapshots MDS preservam URLs e hashes das respostas oficiais. O ranking registra as origens TSE, CGU e IBGE; os arquivos brutos e o SQLite pertencem ao pipeline de dados, separado da aplicação web.</p>
        <p><a href="/api/fontes">Consultar metadados em JSON</a></p>
      </>}
    </Card></main>
  </>;
}
