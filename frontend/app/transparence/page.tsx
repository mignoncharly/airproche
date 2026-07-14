import type { Metadata } from "next";

import { LegalPage } from "@/components/legal-page";

export const metadata: Metadata = { title: "Transparence de la plateforme", robots: { index: true, follow: true } };

export default function TransparencyPage() {
  return <LegalPage kind="transparency" />;
}
