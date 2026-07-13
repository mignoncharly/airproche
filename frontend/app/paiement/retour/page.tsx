import type { Metadata } from "next";

import { PaymentReturn } from "@/features/payments/payment-return";

export const metadata: Metadata = { title: "Statut du paiement", robots: { index: false, follow: false } };

export default async function PaymentReturnPage({ searchParams }: { searchParams: Promise<{ booking?: string; session_id?: string; cancelled?: string }> }) {
  const params = await searchParams;
  return <main><div className="site-container py-16 sm:py-24"><div className="mx-auto max-w-2xl"><PaymentReturn bookingId={params.booking ?? ""} sessionId={params.session_id ?? ""} cancelled={params.cancelled === "1"} /></div></div></main>;
}
