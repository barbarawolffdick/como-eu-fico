import type { FinanciamentoSaude } from "@/lib/saude";
import styles from "./equipamentos-saude.module.css";

type Equipamentos = FinanciamentoSaude["equipamentos"];
const descricoes: Record<string, { titulo: string; equipamento: string; plural: string }> = {
  "Mamógrafo": { titulo: "Mamografia", equipamento: "mamógrafo", plural: "mamógrafos" },
  "Raio X": { titulo: "Raio X", equipamento: "aparelho de raio X", plural: "aparelhos de raio X" },
  "Tomógrafo Computadorizado": { titulo: "Tomografia", equipamento: "tomógrafo", plural: "tomógrafos" },
  "Ressonância Magnética": { titulo: "Ressonância magnética", equipamento: "aparelho de ressonância", plural: "aparelhos de ressonância" },
  "Ultrassom": { titulo: "Ultrassom", equipamento: "aparelho de ultrassom", plural: "aparelhos de ultrassom" },
  "Equipo Odontológico Completo": { titulo: "Atendimento odontológico", equipamento: "conjunto odontológico completo", plural: "conjuntos odontológicos completos" },
};
const numero = (n: number) => n.toLocaleString("pt-BR");
function referencia(competencia: string) {
  const ano = Number(competencia.slice(0, 4));
  const mes = Number(competencia.slice(4)) - 1;
  return new Intl.DateTimeFormat("pt-BR", { month: "long", year: "numeric", timeZone: "UTC" })
    .format(new Date(Date.UTC(ano, mes, 1)));
}

export default function EquipamentosSaude({ dados }: { dados: Equipamentos }) {
  const locais = new Map((dados.estabelecimentos_com_equipamento_sus ?? []).map(e => [e.tipo, e.valor]));
  const aparelhos = new Map((dados.equipamentos_em_uso ?? []).map(e => [e.tipo, e.valor]));
  const tipos = [...new Set([...locais.keys(), ...aparelhos.keys()])];
  return <div className={styles.section} data-testid="equipamentos-saude">
    <header className={styles.header}>
      <h4>Equipamentos na cidade</h4>
      <p className={styles.date}>Dados de {referencia(dados.competencia)}</p>
    </header>
    <p className={styles.intro}>Quantos locais informam ter equipamentos para atender pelo SUS?</p>
    <p className={styles.explanation}>Cada número abaixo conta <strong>locais de atendimento</strong>. Um hospital ou clínica pode ter vários aparelhos do mesmo tipo.</p>
    {tipos.length ? <ul className={styles.grid} aria-label="Locais com equipamentos para atendimento pelo SUS">
      {tipos.map(tipo => {
        const descricao = descricoes[tipo] ?? { titulo: tipo, equipamento: tipo, plural: tipo };
        const valor = locais.get(tipo);
        return <li key={tipo} className={`${styles.item} ${valor == null ? styles.itemMissing : ""}`} data-equipamento={tipo}>
          <h5>{descricao.titulo}</h5>
          <p className={styles.count}>
            {valor == null ? <span className={styles.missing}>Sem informação</span> : <><strong>{numero(valor)}</strong> <span>{valor === 1 ? "local" : "locais"}</span></>}
          </p>
          <p className={styles.description}>{valor == null
            ? "A fonte não informa uma contagem neste recorte."
            : valor === 0 ? "Zero locais informado pela fonte para este equipamento."
            : `Com ${descricao.equipamento} informado para o SUS.`}</p>
        </li>;
      })}
    </ul> : <p className={styles.explanation}>Não há dados de equipamentos disponíveis neste recorte. Ausência não é zero.</p>}
    <p className={styles.availability}>O cadastro não confirma vagas para exames ou agendamento disponível.</p>
    {tipos.length > 0 && <details className={styles.details}>
      <summary>Ver o total de equipamentos na rede pública e privada</summary>
      <p>Esta outra medida conta <strong>aparelhos em uso</strong>, incluindo os que não atendem pelo SUS. Ela não informa quantos aparelhos são do SUS.</p>
      <dl className={styles.inventory}>
        {tipos.map(tipo => {
          const descricao = descricoes[tipo] ?? { titulo: tipo, equipamento: tipo, plural: tipo };
          const valor = aparelhos.get(tipo);
          return <div key={tipo}><dt>{tipo}</dt><dd>{valor == null ? "Sem informação" : `${numero(valor)} ${valor === 1 ? descricao.equipamento : descricao.plural}`}</dd></div>;
        })}
      </dl>
      <p>Um local pode ter mais de um aparelho. Por isso, essa quantidade não deve ser somada nem subtraída da contagem de locais acima.</p>
    </details>}
    <div className="footnote">Fonte: <a href="https://tabnet.datasus.gov.br/cgi/deftohtm.exe?cnes/cnv/equipobr.def">DATASUS / Cadastro Nacional de Estabelecimentos de Saúde (CNES)</a>, {referencia(dados.competencia)}. Tipos selecionados no cadastro. “Sem informação” preserva dados ausentes da fonte; não significa zero. Os registros não informam quem pagou pela compra dos equipamentos.</div>
  </div>;
}
