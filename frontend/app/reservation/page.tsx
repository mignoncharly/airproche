import type { Metadata } from "next";
import Link from "next/link";

import { PageHero } from "@/components/marketing";
import { BookingForm } from "@/features/bookings/booking-form";
import { getBookingQuote } from "@/lib/booking-api";

export const metadata: Metadata = { title: "Réserver un transfert", robots: { index: false, follow: false } };

export default async function ReservationPage({ searchParams }: { searchParams: Promise<{ quote?: string }> }) {
  const { quote: quoteId } = await searchParams;
  const quote = quoteId ? await getBookingQuote(quoteId) : null;
  return <main><PageHero eyebrow="Réservation" title="Organiser votre transfert" description="Complétez les informations nécessaires. Le montant reste celui du devis vérifié par le serveur." /><section className="site-container py-16 sm:py-24">{quote?.status === "valid" ? <BookingForm quote={quote} /> : <div className="surface-card mx-auto max-w-2xl p-8"><h2 className="text-2xl font-black text-slate-950">Devis indisponible</h2><p className="mt-3 text-sm leading-6 text-slate-600">Ce devis est absent ou expiré. Demandez une nouvelle estimation pour commencer une réservation.</p><Link className="button button-primary mt-6" href="/tarifs">Obtenir une estimation</Link></div>}</section></main>;
}
