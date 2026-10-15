import type { Metadata } from "next";
import "./globals.css";
import SiteNavigation from "./components/site-navigation";

export const metadata: Metadata = {
  title: "Como Eu Fico — seu município em dados",
  description: "Entenda como sua cidade vota e o que muda na vida de quem mora nela. Políticas públicas, recursos e serviços em dados.",
};

export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {
  return <html lang="pt-BR"><body><SiteNavigation />{children}<footer className="footer"><div className="shell footer-inner"><strong>Como Eu Fico</strong><span>Dados públicos para entender sua cidade e formar sua própria opinião.</span><a href="/fontes">Fontes e metodologia →</a></div></footer></body></html>;
}
