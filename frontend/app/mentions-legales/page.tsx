import type { Metadata } from "next";

import { LegalPage } from "@/components/legal-page";

export const metadata: Metadata = { title: "Mentions légales", robots: { index: false, follow: true } };

export default function LegalNoticePage() {
  return <LegalPage kind="legal_notice" />;
}
