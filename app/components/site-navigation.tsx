"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
const links = [
    { href: "/", label: "Minha cidade" },
    { href: "/explorar", label: "Explorar o Brasil" },
    { href: "/comparar", label: "Comparar cidades" },
    { href: "/analises", label: "Análises" },
    { href: "/fontes", label: "Sobre os dados" },
];
export default function SiteNavigation() {
    const pathname = usePathname();
    return <>
    <a className="skip-link" href="#conteudo">Pular para o conteúdo</a>
    <div className="global-header"><div className="shell global-header-inner">
      <Link href="/" className="brand" aria-label="Como Eu Fico — início">Como Eu Fico<span className="brand-dot">.</span></Link>
      <nav aria-label="Navegação principal">{links.map(link => {
            const active = link.href === "/" ? pathname === "/" || pathname.startsWith("/cidade/") : pathname === link.href;
            return <Link key={link.href} href={link.href} aria-current={active ? "page" : undefined}>{link.label}</Link>;
        })}</nav>
    </div></div>
  </>;
}
