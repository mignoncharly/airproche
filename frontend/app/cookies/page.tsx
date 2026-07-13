import type { Metadata } from "next";

import { LegalPage } from "@/components/legal-page";

export const metadata: Metadata = { title: "Politique relative aux cookies", robots: { index: false, follow: true } };

export default function CookiesPage() {
  return <LegalPage kind="cookies" />;
}
