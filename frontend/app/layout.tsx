import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { AnalyticsConsentBanner } from "@/components/analytics-consent";
import { PwaManager } from "@/components/pwa-manager";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { getPublicContent } from "@/lib/public-content";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "AirProche — Chauffeurs indépendants pour transferts aéroport",
    template: "%s | AirProche",
  },
  description: "Trouvez et contactez des chauffeurs indépendants vérifiés pour vos transferts depuis et vers les aéroports.",
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
        <div className="pointer-events-none fixed inset-x-3 bottom-3 z-[80] flex flex-col items-end gap-3 sm:left-auto sm:right-5 sm:w-[min(36rem,calc(100vw-2.5rem))]">
          <AnalyticsConsentBanner />
          <PwaManager />
        </div>
      </body>
    </html>
  );
}
