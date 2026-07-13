import type { Metadata } from "next";

import { LegalPage } from "@/components/legal-page";

export const metadata: Metadata = { title: "Politique de confidentialité", robots: { index: false, follow: true } };

export default function PrivacyPage() {
  return <LegalPage kind="privacy" />;
}
