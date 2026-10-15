import EquipamentosSaude from "./equipamentos-saude";
import type { FinanciamentoSaude, OrigemSaude } from "@/lib/saude";

const moeda = (v: number | null | undefined) => v == null ? "Indisponível" : (v / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const numero = (v: number | null | undefined) => v == null ? "Indisponível" : v.toLocaleString("pt-BR");
const pct = (v: number | null | undefined) => v == null ? "Indisponível" : `${v.toLocaleString("pt-BR", { maximumFractionDigits: 2 })}%`;
const mes = (v: string) => `${v.slice(4)}/${v.slice(0, 4)}`;
const dia = (v: string) => v.slice(0, 10).split("-").reverse().join("/");
const grupos: Record<string, string> = {
  "ATENÇÃO PRIMÁRIA": "Atenção primária",
  "ATENÇÃO DE MÉDIA E ALTA COMPLEXIDADE AMBULATORIAL E HOSPITALAR": "Hospitais e ambulatórios — média e alta complexidade",
  "ATENÇÃO ESPECIALIZADA": "Atenção especializada",
  "ASSISTÊNCIA FARMACÊUTICA": "Assistência farmacêutica",
  "VIGILÂNCIA EM SAÚDE": "Vigilância em saúde",
  "GESTÃO DO SUS": "Gestão do SUS",
  "REESTRUTURAÇÃO DOS SERVIÇOS EM SAÚDE - FUNDO RIO DOCE": "Reestruturação dos serviços — Fundo Rio Doce",
};

function Valores({ itens, total }: { itens: { nome: string; valor_centavos: number | null }[]; total: number | null }) {
  return <ul className="health-money-list">{itens.map(item => <li key={item.nome}>
    <div><span>{grupos[item.nome] || item.nome}</span><strong>{moeda(item.valor_centavos)}</strong></div>
    {total != null && total > 0 && item.valor_centavos != null && item.valor_centavos >= 0 &&
      <meter min={0} max={total} value={item.valor_centavos} aria-label={`${grupos[item.nome] || item.nome}: ${moeda(item.valor_centavos)}`} />}
  </li>)}</ul>;
}

export default function FinanciamentoSaude({ dados, fontes }: { dados: FinanciamentoSaude; fontes: Record<string, OrigemSaude> }) {
  const atual = dados.fns.at(-1)!;
  const municipal = atual.municipal;
  const liquidado = dados.siops?.fases["Despesas Liquidadas"];
  const pago = dados.siops?.fases["Despesas Pagas"];
  const hospitais = dados.leitos?.unidades.filter(r => r.leitos_sus != null && r.leitos_sus > 0) || [];
  return <div data-testid="financiamento-saude">
    <h3 className="health-subtitle">Quanto a União transferiu ao fundo de saúde da cidade</h3>
    <div className="cards health-summary">
      <article className="card"><h4>Total federal recebido pelo fundo municipal</h4>
        <p className="kicker">De {mes(atual.inicio)} a {mes(atual.fim)}</p>
        <div className="big">{moeda(municipal?.valor_centavos)}</div>
        <p className="sub">Transferências fundo a fundo para todas as áreas da saúde presentes na planilha FNS.</p>
        {!municipal && <p>Não há repasse municipal validado neste recorte. Ausência não é zero.</p>}
        <div className="footnote">Fonte: <a href={fontes.fns_2026.url}>FNS — acumulado até {mes(atual.fim)}</a>. Valores líquidos nominais. O total já inclui atenção primária e emendas identificadas. Não inclui todo gasto federal na cidade, pagamentos diretos ou recursos recebidos pelo estado.</div>
      </article>
      <article className="card"><h4>Quanto isso representa por habitante</h4>
        <p className="kicker">Mesmo acumulado de {mes(atual.inicio)} a {mes(atual.fim)}</p>
        <div className="big">{moeda(dados.centavos_por_habitante)}</div>
        <p className="sub">Total municipal dividido por {numero(dados.municipio.populacao)} habitantes, população IBGE {dados.municipio.ano_populacao}.</p>
        <div className="footnote">Fontes: FNS e população IBGE já publicada no projeto. É uma referência de escala, não um valor pago a cada pessoa nem uma média mensal ou anual.</div>
      </article>
    </div>
    <div className="cards health-related">
      <article className="card"><h4>Para quais áreas veio o dinheiro?</h4>
        <p className="kicker">Fundo municipal · até {mes(atual.fim)}</p>
        {municipal ? <><Valores itens={municipal.grupos} total={municipal.valor_centavos} />
          <details className="health-details"><summary>Manutenção e estruturação da rede</summary><Valores itens={municipal.finalidades} total={municipal.valor_centavos} /></details></> : <p>Finalidades municipais indisponíveis neste recorte.</p>}
        <div className="footnote">Fonte: <a href={fontes.fns_2026.url}>FNS</a>. As áreas são partes do total federal recebido. A finalidade do repasse não comprova a realização de uma compra, obra ou atendimento.</div>
      </article>
      <article className="card"><h4>Quanto foi identificado como emenda?</h4>
        <p className="kicker">Dentro do total municipal · até {mes(atual.fim)}</p>
        <div className="big">{moeda(municipal?.emendas.valor_centavos)}</div>
        <p className="sub">{municipal?.emendas.percentual_do_total != null ? `${pct(municipal.emendas.percentual_do_total)} do total municipal na planilha.` : "Não há valor de emendas identificado e validado neste recorte. Isso não comprova ausência de emendas."}</p>
        <div className="footnote">Fonte: <a href={fontes.fns_2026.url}>FNS</a>. Soma das linhas cuja estratégia começa com “EMENDA -”. Esses valores já estão incluídos no total e nas áreas; não devem ser somados novamente. A planilha não permite atribuir autoria parlamentar ou cobrir todas as modalidades de emenda.</div>
      </article>
      <article className="card"><h4>O repasse aumentou ou diminuiu?</h4>
        <p className="kicker">Comparação entre anos completos</p>
        <table className="health-compact-table"><caption className="sr-only">Transferências municipais em anos completos</caption><thead><tr><th>Ano</th><th>Total municipal</th></tr></thead><tbody>
          {dados.fns.filter(r => r.completo).map(r => <tr key={r.ano}><td>{r.ano} · jan–dez</td><td>{moeda(r.municipal?.valor_centavos)}</td></tr>)}
        </tbody></table>
        <p>Variação nominal de 2024 para 2025: <strong>{pct(dados.variacao_anual_2024_2025_percentual)}</strong>.</p>
        <div className="footnote">Fontes: <a href={fontes.fns_2024.url}>FNS 2024</a> e <a href={fontes.fns_2025.url}>FNS 2025</a>. Valores sem correção pela inflação. O acumulado parcial de 2026 fica separado: não calculamos variação contra um ano completo nem projetamos seu fechamento.</div>
      </article>
      <article className="card"><h4>Como a cidade financiou suas despesas de saúde?</h4>
        <p className="kicker">SIOPS · exercício 2025 · 6º bimestre</p>
        {dados.siops && liquidado ? <><p>Despesas liquidadas: <strong>{moeda(liquidado.total_centavos)}</strong>.<br />Despesas pagas: <strong>{moeda(pago?.total_centavos)}</strong>.</p>
          <p>Parcela das despesas liquidadas declarada na fonte federal fundo a fundo: <strong>{pct(liquidado.percentual_fonte_federal_faf)}</strong>.</p>
          <details className="health-details"><summary>Ver despesas liquidadas por fonte de financiamento</summary><Valores itens={liquidado.fontes} total={liquidado.total_centavos} /></details>
          <p className="hint">Última homologação no arquivo: {dia(dados.siops.homologacao)}.</p></> : <p>Não há despesa municipal homologada validada neste arquivo. Ausência não é zero.</p>}
        <div className="footnote">Fonte: <a href={fontes.siops.url}>SIOPS — despesas por fonte, exercício 2025</a>, declaradas pelos gestores. Liquidação reconhece o direito do fornecedor após a verificação da entrega; pagamento é outra etapa. Estes totais são despesas, não receitas recebidas. O percentual considera somente a fonte federal fundo a fundo; convênios e outras fontes não são atribuídos exclusivamente à União. Não somamos estas despesas aos repasses FNS de 2026.</div>
      </article>
    </div>
    {atual.estadual_sediado_na_cidade && <div className="notice"><details><summary>Recursos {dados.municipio.uf === "DF" ? "distritais" : "estaduais"} relacionados à cidade</summary>
      <p>O fundo {dados.municipio.uf === "DF" ? "distrital" : "estadual"} registrado aqui recebeu <strong>{moeda(atual.estadual_sediado_na_cidade.valor_centavos)}</strong> em transferências FNS nas áreas da planilha, de {mes(atual.inicio)} a {mes(atual.fim)}.</p>
      <p>Destinatário: esfera estadual na fonte. A sede não comprova destinação exclusiva aos moradores desta cidade. O valor fica separado do total municipal.</p>
      <p className="hint">Fonte: <a href={fontes.fns_2026.url}>FNS, até {mes(atual.fim)}</a>.</p>
    </details></div>}
    {atual.outros_destinatarios_sediados_na_cidade && <div className="notice"><details><summary>Outros destinatários sediados nesta cidade</summary>
      <p>{atual.outros_destinatarios_sediados_na_cidade.destinatarios.join(", ")}: <strong>{moeda(atual.outros_destinatarios_sediados_na_cidade.valor_centavos)}</strong>, de {mes(atual.inicio)} a {mes(atual.fim)}.</p>
      <p>A planilha contém classificações municipais e estaduais para esses pagamentos, mas o destinatário identificado não é o fundo municipal ou distrital. A sede da instituição não determina quais moradores foram atendidos. Mantemos esses valores fora dos totais dos fundos e do indicador municipal por habitante.</p>
      <p className="hint">Fonte: <a href={fontes.fns_2026.url}>FNS, até {mes(atual.fim)}</a>.</p>
    </details></div>}
    <h3 className="health-subtitle">Estrutura de saúde localizada na cidade</h3>
    <p className="hint">Cadastros de estrutura ajudam a conhecer a rede. Não vinculamos automaticamente uma unidade, um leito ou um equipamento a um repasse federal.</p>
    <div className="cards health-related">
      <article className="card"><h4>Unidades e atenção básica</h4>
        {dados.cnes ? <><p><strong>{numero(dados.cnes.ubs)} unidades básicas</strong> e <strong>{numero(dados.cnes.postos)} postos de saúde</strong> no recorte de estabelecimentos ativos com atendimento ambulatorial SUS informado.</p>
          <p>Total de estabelecimentos desse recorte: <strong>{numero(dados.cnes.estabelecimentos_sus_ambulatorial)}</strong>.</p>
          <details className="health-details"><summary>Conhecer algumas unidades da cidade</summary><ul>{dados.cnes.unidades_exibidas.map(u => <li key={u.cnes}><a href={`https://cnes.datasus.gov.br/pages/estabelecimentos/ficha/index.jsp?coUnidade=${u.codigo_local_fonte}${u.cnes}`}>{u.nome}</a><small>CNES {u.cnes} · gestão {u.gestao === "M" ? "municipal" : u.gestao === "E" ? "estadual" : u.gestao === "D" ? "dupla" : u.gestao}</small></li>)}</ul>
            {dados.cnes.lista_limitada && <p>Exibindo 10 de {numero(dados.cnes.estabelecimentos_sus_ambulatorial)} estabelecimentos deste recorte.</p>}</details></> : <p>Não há cadastro validado de estabelecimento neste recorte. Isso não comprova ausência de unidade.</p>}
        <div className="footnote">Fonte: <a href={fontes.cnes.url}>CNES — estabelecimentos</a>. Arquivo consultado em {dia(fontes.cnes.data_extracao)}; sem competência mensal declarada no arquivo. Seleção: sem motivo de desativação e atendimento ambulatorial SUS “SIM”. UBS usa o tipo 02; postos, tipo 01. Não mede consultas, funcionamento efetivo ou todos os serviços do SUS.</div>
      </article>
      <article className="card"><h4>Leitos e hospitais</h4>
        <p className="kicker">Cadastro CNES · 08/2026</p>
        {dados.leitos ? <><p>Leitos SUS de internação: <strong>{numero(dados.leitos.leitos_sus)}</strong>.<br />Leitos SUS de UTI: <strong>{numero(dados.leitos.uti_sus)}</strong>.</p>
          <details className="health-details"><summary>Hospitais com leitos SUS registrados</summary>{hospitais.length ? <ul>{hospitais.slice(0, 10).map(u => <li key={u.cnes}>{u.nome}<small>CNES {u.cnes} · {numero(u.leitos_sus)} leitos SUS de internação · {numero(u.uti_sus)} de UTI</small></li>)}</ul> : <p>Nenhum registro com leitos SUS positivos nesta seleção.</p>}{hospitais.length > 10 && <p>Exibindo 10 de {hospitais.length} unidades com leitos SUS positivos.</p>}</details></> : <p>Não há registro hospitalar validado nesta competência para a cidade. Ausência não é zero.</p>}
        <div className="footnote">Fonte: <a href={fontes.leitos.url}>CNES — hospitais e leitos, agosto/2026</a>. Internação e UTI são categorias apresentadas separadamente. São leitos cadastrados, não vagas disponíveis agora. Hospitais podem atender moradores de outras cidades; a base não identifica aqui a residência dos pacientes ou o destino de cada repasse.</div>
      </article>
      <article className="card health-wide"><EquipamentosSaude dados={dados.equipamentos} /></article>
    </div>
    <h3 className="health-subtitle">Equipes e provimento federal</h3>
  </div>;
}
