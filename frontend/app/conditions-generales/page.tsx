import type { Metadata } from "next";

import { LegalPage } from "@/components/legal-page";

export const metadata: Metadata = { title: "Conditions générales", robots: { index: false, follow: true } };

export default function TermsPage() {
  return <LegalPage kind="terms" />;
}
