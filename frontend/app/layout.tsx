import type { Metadata } from "next";
import type { ReactNode } from "react";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { getPublicContent } from "@/lib/public-content";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Transfert aéroport privé",
    template: "%s | Transfert aéroport privé",
  },
  description: "Accueil et transport privé depuis et vers les aéroports, organisé avec soin.",
  metadataBase: new URL(process.env.APP_BASE_URL ?? "http://localhost:3000"),
};

export default async function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  const { settings } = await getPublicContent();
  return (
    <html lang="fr">
      <body>
        <a href="#contenu" className="skip-link">Aller au contenu</a>
        <SiteHeader settings={settings} />
        <div id="contenu">{children}</div>
        <SiteFooter settings={settings} />
      </body>
    </html>
  );
}
