import { leituraCobertura } from "@/lib/bolsa-familia";
import TermHelp from "./ui/term-help";

export function AjudaBolsa() {
  return <TermHelp term="Quem entra na conta do Bolsa Família?" presentation="dialog">
    <p><strong>Família beneficiária:</strong> a família para a qual o programa concede o benefício.</p>
    <p><strong>Titular:</strong> a pessoa responsável por receber o pagamento para a família. A contagem de pessoas beneficiadas inclui também os demais integrantes, como crianças.</p>
    <p><strong>Percentual da cidade:</strong> número de pessoas que vivem nessas famílias dividido pelo total estimado de moradores da cidade. Não é uma porcentagem dentro de cada família.</p>
    <p><strong>Valor por pessoa da família:</strong> valor registrado no município dividido pelas pessoas em famílias beneficiárias no mesmo mês. É uma média calculada; não significa que cada integrante recebe um pagamento separado.</p>
    <p><strong>Valor por família:</strong> valor registrado dividido pelas famílias beneficiárias do mesmo mês. O valor de cada família pode ser diferente dessa média.</p>
    <p>Não usamos o número de parcelas como se fosse uma contagem de famílias ou de titulares únicos. <a href="https://www.gov.br/mds/pt-br/acoes-e-programas/bolsa-familia/conheca-as-regras">Regras e informações oficiais do MDS</a>.</p>
  </TermHelp>;
}

export default function AlcanceBolsa({ pessoas, populacao, percentual, compact = false }: { pessoas: number; populacao: number; percentual: number; compact?: boolean }) {
  return <><p className="sub coverage-reading">{leituraCobertura(percentual)}</p>
    <p className="sub"><strong>{pessoas.toLocaleString("pt-BR")} moradores</strong> em famílias beneficiárias{!compact && <>, de uma população estimada de <strong>{populacao.toLocaleString("pt-BR")} pessoas</strong></>}.</p>
    <p className="hint">O benefício é da família. O pagamento é feito ao titular. <AjudaBolsa /></p>
  </>;
}
