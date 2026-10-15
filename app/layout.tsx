import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Como Eu Fico — seu município em dados",
  description: "Dados públicos municipais: Bolsa Família, votação presidencial e população IBGE.",
};

export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {
  return <html lang="pt-BR"><body>{children}<nav className="shell site-nav" aria-label="Navegação principal"><Link href="/">Consultar município</Link><Link href="/explorar">Explorar o Brasil</Link><Link href="/analises">Análises</Link><Link href="/fontes">Fontes e metodologia</Link></nav></body></html>;
}
