"use client";

import { useId, useState } from "react";
import { Button } from "./ui/button";
import { DataBar } from "./ui/data-bar";
import { nomeCandidato } from "@/lib/eleicoes";

export default function VotosMunicipais({ votos, compact = false }: { votos: { candidato: string; votos: number }[]; compact?: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const id = useId();
  const ordenados = [...votos].sort((a, b) => b.votos - a.votos || a.candidato.localeCompare(b.candidato));
  const total = ordenados.reduce((sum, item) => sum + item.votos, 0);
  if (!ordenados.length || total <= 0) return <p>Dados eleitorais indisponíveis. Ausência não significa zero.</p>;
  return <div className={compact ? "votes-summary" : ""}>
    <div className="vote-list" id={id}>{ordenados.slice(0, expanded ? undefined : 3).map(v => {
      const p = 100 * v.votos / total;
      return <div className="vote" key={v.candidato}><div className="voterow"><span>{nomeCandidato(v.candidato)} ({v.candidato})</span><strong>{p.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%</strong></div>
        {!compact && <DataBar value={p} />}<p className="sub">{v.votos.toLocaleString("pt-BR")} votos</p>
      </div>;
    })}</div>
    {ordenados.length > 3 && <Button variant="quiet" className="votes-expand" aria-expanded={expanded} aria-controls={id} onClick={() => setExpanded(value => !value)}>{expanded ? "Ver menos candidatos" : `Ver mais candidatos (${ordenados.length - 3})`}</Button>}
  </div>;
}
