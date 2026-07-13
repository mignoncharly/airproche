import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { PwaManager } from "@/components/pwa-manager";
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
  applicationName: "Airproche",
  manifest: "/manifest.webmanifest",
  icons: {
    icon: [
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [{ url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" }],
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Airproche",
  },
};

export const viewport: Viewport = {
  themeColor: "#175cd3",
  width: "device-width",
  initialScale: 1,
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
        <PwaManager />
      </body>
    </html>
  );
}
