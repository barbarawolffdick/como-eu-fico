"use client";

import { useEffect, useState } from "react";
const sections = [
    { id: "panorama", label: "Panorama" },
    { id: "titulo-saude", label: "Saúde" },
    { id: "dados-bolsa", label: "Bolsa Família" },
    { id: "dados-eleicao", label: "Eleição 2026" },
    { id: "fontes-cidade", label: "Fontes" },
];
export default function CitySections() {
    const [active, setActive] = useState("panorama");
    useEffect(() => {
        let frame = 0;
        function update() {
            if (window.scrollY > 0 && window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) {
                setActive("fontes-cidade");
                return;
            }
            const current = sections.filter(section => {
                const element = document.getElementById(section.id);
                return element && element.getBoundingClientRect().top <= 155;
            }).at(-1);
            setActive(current?.id ?? "panorama");
        }
        function scroll() { cancelAnimationFrame(frame); frame = requestAnimationFrame(update); }
        update();
        window.addEventListener("scroll", scroll, { passive: true });
        return () => { cancelAnimationFrame(frame); window.removeEventListener("scroll", scroll); };
    }, []);
    return <nav className="city-sections" aria-label="Indicadores da cidade">{sections.map(section => <a href={"#" + section.id} key={section.id} aria-current={active === section.id ? "location" : undefined}>{section.label}</a>)}</nav>;
}
