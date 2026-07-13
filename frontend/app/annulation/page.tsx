import type { Metadata } from "next";

import { LegalPage } from "@/components/legal-page";

export const metadata: Metadata = { title: "Politique d’annulation", robots: { index: false, follow: true } };

export default function CancellationPage() {
  return <LegalPage kind="cancellation" />;
}
