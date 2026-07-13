import type { Metadata } from "next";

import { PaymentReturnFromFragment } from "@/features/payments/payment-return";

export const metadata: Metadata = { title: "Retour de paiement", robots: { index: false, follow: false } };

export default function PaymentReturnPage() {
  return <main><div className="site-container py-16 sm:py-24"><div className="mx-auto max-w-2xl"><PaymentReturnFromFragment /></div></div></main>;
}
