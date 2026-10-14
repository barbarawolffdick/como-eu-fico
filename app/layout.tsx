import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Como Eu Fico — seu município em dados",
  description: "Dados públicos municipais: Bolsa Família, votação presidencial e população IBGE.",
};

export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}
