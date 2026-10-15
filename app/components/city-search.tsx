"use client";

import { Button } from "@/app/components/ui/button";
import { useEffect, useId, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
export type Cidade = {
    codigo_ibge: string;
    nome: string | null;
    uf: string | null;
};
export default function CitySearch({ compact = false, label, onSelect }: {
    compact?: boolean;
    label?: string;
    onSelect?: (city: Cidade) => void;
}) {
    const router = useRouter();
    const id = useId();
    const [query, setQuery] = useState("");
    const [choices, setChoices] = useState<Cidade[]>([]);
    const [status, setStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");
    const [selected, setSelected] = useState(-1);
    const [open, setOpen] = useState(true);
    const container = useRef<HTMLDivElement>(null);
    useEffect(() => {
        if (!query.trim())
            return;
        const controller = new AbortController();
        const timer = setTimeout(async () => {
            try {
                const response = await fetch("/api/municipios?q=" + encodeURIComponent(query.trim()), { signal: controller.signal });
                if (!response.ok)
                    throw Error("Falha na busca");
                const rows = await response.json() as Cidade[];
                if (!controller.signal.aborted) {
                    setChoices(rows);
                    setStatus("ready");
                }
            }
            catch {
                if (!controller.signal.aborted)
                    setStatus("error");
            }
        }, 200);
        return () => { clearTimeout(timer); controller.abort(); };
    }, [query]);
    function choose(code: string) {
        const city = choices.find(item => item.codigo_ibge === code);
        if (onSelect && city) {
            setOpen(false);
            setQuery("");
            setChoices([]);
            setStatus("idle");
            onSelect(city);
        }
        else
            router.push("/cidade/" + code);
    }
    return <div ref={container} className={compact ? "city-search compact-search" : "city-search"} onBlur={event => {
            if (!event.currentTarget.contains(event.relatedTarget))
                setOpen(false);
        }}>
    <label htmlFor={id} className="inputlabel">{label ?? (compact ? "Trocar de cidade" : "Encontre seu município")}</label>
    <div className="city-search-control"><div className="searchfield"><Search size={20} aria-hidden="true"/>
      <input id={id} role="combobox" aria-autocomplete="list" aria-expanded={open && choices.length > 0} aria-controls={id + "-results"} aria-activedescendant={open && selected >= 0 ? id + "-option-" + selected : undefined} aria-describedby={id + "-hint"} autoComplete="off" placeholder="Digite sua cidade ou código IBGE" value={query} onFocus={() => setOpen(true)} onChange={event => {
            const value = event.target.value;
            setQuery(value);
            setChoices([]);
            setSelected(-1);
            setOpen(true);
            setStatus(value.trim() ? "loading" : "idle");
        }} onKeyDown={event => {
            if (event.key === "Escape") {
                setOpen(false);
                setSelected(-1);
            }
            if (["ArrowDown", "ArrowUp"].includes(event.key) && choices.length) {
                event.preventDefault();
                setOpen(true);
                setSelected(index => event.key === "ArrowDown" ? (index + 1) % choices.length : (index <= 0 ? choices.length - 1 : index - 1));
            }
            if (event.key === "Enter" && open && choices.length && selected >= 0) {
                event.preventDefault();
                choose(choices[selected].codigo_ibge);
            }
        }}/>
    </div>
    <div id={id + "-results"} role="listbox" aria-label="Resultados da busca" className={open && choices.length ? "choices" : undefined}>
      {open && choices.map((city, index) => <Button variant="quiet" id={id + "-option-" + index} type="button" role="option" aria-selected={selected === index} tabIndex={-1} className="choice" key={city.codigo_ibge} onMouseDown={event => event.preventDefault()} onClick={() => choose(city.codigo_ibge)}>
        <span>{city.nome ?? "Município sem nome"} — {city.uf ?? "UF não informada"}</span><small>IBGE {city.codigo_ibge}</small>
      </Button>)}
    </div>
    </div>
    <p id={id + "-hint"} className="hint" role="status" aria-live="polite">
      {status === "loading" ? "Buscando cidades…" : status === "error" ? "Não foi possível buscar. Altere o texto para tentar novamente." :
            status === "ready" && !choices.length ? "Nenhuma cidade encontrada. Confira o nome ou tente o código IBGE." : "Escolha a cidade para conhecer os dados e o resultado eleitoral."}
    </p>
  </div>;
}
