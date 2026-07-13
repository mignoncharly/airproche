"use client";

import { useState } from "react";

import { BookingApiError, type Booking, accessGuestBooking, cancelGuestBooking } from "@/lib/booking-api";
import { formatMoney } from "@/lib/locations-pricing";

export function ManageBooking({ initialReference = "" }: { initialReference?: string }) {
  const [reference, setReference] = useState(initialReference);
  const [token, setToken] = useState("");
  const [booking, setBooking] = useState<Booking | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function open(event: React.FormEvent) { event.preventDefault(); setLoading(true); setError(null); try { setBooking(await accessGuestBooking(reference, token || (window.location.hash.startsWith("#token=") ? decodeURIComponent(window.location.hash.slice(7)) : ""))); } catch (caught) { setError(caught instanceof BookingApiError ? caught.message : "Impossible dâ€™ouvrir cette rÃ©servation."); } finally { setLoading(false); } }
  async function cancel() { if (!booking || !window.confirm("Annuler cette rÃ©servation ?")) return; setLoading(true); setError(null); try { setBooking(await cancelGuestBooking(booking.public_id, token || (window.location.hash.startsWith("#token=") ? decodeURIComponent(window.location.hash.slice(7)) : ""))); } catch (caught) { setError(caught instanceof BookingApiError ? caught.message : "Impossible dâ€™annuler cette rÃ©servation."); } finally { setLoading(false); } }

  return <section className="site-container py-16 sm:py-24"><div className="mx-auto max-w-2xl">{booking ? <div className="surface-card p-6 sm:p-8"><p className="eyebrow">RÃ©servation {booking.reference}</p><h1 className="mt-3 text-3xl font-black text-slate-950">{booking.airport.iata_code} Â· {booking.service_area.name}</h1><p className="mt-3 text-sm text-slate-600">Statut : <strong>{booking.status}</strong></p><p className="mt-2 text-sm text-slate-600">{new Intl.DateTimeFormat("fr-FR", { dateStyle: "full", timeStyle: "short" }).format(new Date(booking.pickup_at))}</p><p className="mt-7 text-2xl font-black text-slate-950">{formatMoney(booking.total_amount, booking.currency)}</p>{booking.cancellation_eligible ? <button className="button button-secondary mt-7" onClick={cancel} disabled={loading}>Annuler la rÃ©servation</button> : <p className="mt-7 text-sm text-slate-600">Cette rÃ©servation nâ€™est plus dans sa fenÃªtre dâ€™annulation.</p>}{error ? <p className="form-status-error mt-5" role="alert">{error}</p> : null}</div> : <form className="surface-card grid gap-5 p-6 sm:p-8" onSubmit={open}><p className="eyebrow">Gestion sÃ©curisÃ©e</p><h1 className="text-3xl font-black text-slate-950">Retrouver ma rÃ©servation</h1><p className="text-sm leading-6 text-slate-600">Utilisez la rÃ©fÃ©rence et le lien personnel reÃ§us aprÃ¨s votre demande.</p><label><span className="form-label">RÃ©fÃ©rence</span><input className="form-input" value={reference} onChange={(event) => setReference(event.target.value.toUpperCase())} required /></label><label><span className="form-label">Jeton de gestion</span><input className="form-input" type="password" value={token} onChange={(event) => setToken(event.target.value)} required /></label>{error ? <p className="form-status-error" role="alert">{error}</p> : null}<button className="button button-primary" disabled={loading}>{loading ? "VÃ©rificationâ€¦" : "Ouvrir ma rÃ©servation"}</button></form>}</div></section>;
}
