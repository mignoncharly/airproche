"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { BookingApiError, bookingReceiptUrl, cancelGuestBooking, getCustomerBookings, repeatBooking, type CustomerBooking } from "@/lib/booking-api";
import { PaymentApiError, createStripeCheckout } from "@/lib/payment-api";
import { formatMoney } from "@/lib/locations-pricing";

function defaultRepeatDate(): string {
  const date = new Date(Date.now() + 48 * 60 * 60 * 1000);
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
}

function BookingCard({ booking, onRefresh }: { booking: CustomerBooking; onRefresh: () => void }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  async function cancel() {
    if (!window.confirm("Annuler cette réservation ?")) return;
    setBusy(true); setError(null);
    try { await cancelGuestBooking(booking.public_id, ""); onRefresh(); }
    catch (caught) { setError(caught instanceof BookingApiError ? caught.message : "Annulation impossible."); }
    finally { setBusy(false); }
  }

  async function repeat() {
    setBusy(true); setError(null);
    try {
      const quote = await repeatBooking(booking.public_id, defaultRepeatDate());
      router.push(`/reservation?quote=${quote.public_id}`);
    } catch (caught) { setError(caught instanceof BookingApiError ? caught.message : "Impossible de préparer un nouveau devis."); setBusy(false); }
  }

  async function pay() {
    setBusy(true); setError(null);
    try { const checkout = await createStripeCheckout(booking.public_id, ""); window.location.assign(checkout.checkoutUrl); }
    catch (caught) { setError(caught instanceof PaymentApiError ? caught.message : "Paiement impossible."); setBusy(false); }
  }

  return <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">{booking.reference}</p><h3 className="mt-2 text-lg font-black text-slate-950">{booking.airport.iata_code} · {booking.service_area.name}</h3><p className="mt-1 text-sm text-slate-600">{new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(booking.pickup_at))}</p></div><div className="text-right"><p className="font-black text-slate-950">{formatMoney(booking.total_amount, booking.currency)}</p><p className="mt-1 text-xs font-bold uppercase tracking-wide text-slate-500">{booking.status}</p></div></div><div className="mt-5 flex flex-wrap gap-2 text-xs font-bold"><span className="rounded-full bg-slate-100 px-3 py-1 text-slate-700">Paiement : {booking.payment_status}</span><span className="rounded-full bg-slate-100 px-3 py-1 text-slate-700">{booking.passenger_count} passager(s)</span></div>{error ? <p className="form-status-error mt-4" role="alert">{error}</p> : null}<div className="mt-5 flex flex-wrap gap-3">{booking.payment_status === "pending" || booking.payment_status === "failed" || booking.payment_status === "not_created" ? <button className="button button-primary" onClick={pay} disabled={busy}>Payer</button> : null}{booking.cancellation_eligible ? <button className="button button-secondary" onClick={cancel} disabled={busy}>Annuler</button> : null}<button className="button button-secondary" onClick={repeat} disabled={busy}>Nouveau devis</button><a className="button button-secondary" href={bookingReceiptUrl(booking.public_id)} target="_blank" rel="noreferrer">Reçu</a><button className="text-sm font-bold text-slate-600 underline" onClick={() => setExpanded((value) => !value)}>{expanded ? "Réduire" : "Détails"}</button></div>{expanded ? <div className="mt-5 border-t border-slate-200 pt-5"><p className="text-sm font-bold text-slate-950">Historique</p><ol className="mt-3 grid gap-2 text-sm text-slate-600">{booking.history.map((item) => <li key={`${item.to_status}-${item.created_at}`}><span className="font-bold text-slate-950">{item.to_status}</span> · {new Intl.DateTimeFormat("fr-FR", { dateStyle: "short", timeStyle: "short" }).format(new Date(item.created_at))}{item.note ? ` · ${item.note}` : ""}</li>)}</ol></div> : null}</article>;
}

export function CustomerDashboard() {
  const [bookings, setBookings] = useState<CustomerBooking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const upcoming = useMemo(() => bookings.filter((booking) => booking.is_upcoming), [bookings]);
  const past = useMemo(() => bookings.filter((booking) => !booking.is_upcoming), [bookings]);

  function refresh() {
    setLoading(true); setError(null);
    getCustomerBookings().then(setBookings).catch((caught) => setError(caught instanceof Error ? caught.message : "Réservations indisponibles.")).finally(() => setLoading(false));
  }
  useEffect(() => {
    let active = true;
    getCustomerBookings().then((data) => { if (active) setBookings(data); }).catch((caught) => { if (active) setError(caught instanceof Error ? caught.message : "R?servations indisponibles."); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  if (loading) return <section className="mt-12 border-t border-slate-200 pt-10"><p role="status" className="text-sm text-slate-600">Chargement de vos réservations…</p></section>;
  return <section className="mt-12 border-t border-slate-200 pt-10"><div className="flex flex-wrap items-end justify-between gap-4"><div><p className="eyebrow">Espace client</p><h2 className="mt-2 text-2xl font-black text-slate-950">Mes réservations</h2></div><Link className="button button-secondary" href="/tarifs">Nouveau transfert</Link></div>{error ? <p className="form-status-error mt-5" role="alert">{error}</p> : null}<div className="mt-7 grid gap-8"><div><h3 className="text-sm font-black uppercase tracking-[0.12em] text-slate-500">À venir</h3>{upcoming.length ? <div className="mt-3 grid gap-4">{upcoming.map((booking) => <BookingCard key={booking.public_id} booking={booking} onRefresh={refresh} />)}</div> : <p className="mt-3 rounded-xl bg-slate-50 p-5 text-sm text-slate-600">Aucune réservation à venir.</p>}</div><div><h3 className="text-sm font-black uppercase tracking-[0.12em] text-slate-500">Historique</h3>{past.length ? <div className="mt-3 grid gap-4">{past.map((booking) => <BookingCard key={booking.public_id} booking={booking} onRefresh={refresh} />)}</div> : <p className="mt-3 rounded-xl bg-slate-50 p-5 text-sm text-slate-600">Votre historique apparaîtra ici.</p>}</div></div></section>;
}
