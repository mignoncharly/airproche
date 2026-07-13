"use client";

import { useState } from "react";

import {
  BookingApiError,
  type Booking,
  accessGuestBooking,
  cancelGuestBooking,
} from "@/lib/booking-api";
import { formatMoney } from "@/lib/locations-pricing";
import { useSensitiveFragment } from "@/lib/sensitive-fragment";

export function ManageBooking() {
  const fragment = useSensitiveFragment();
  const [reference, setReference] = useState("");
  const [token, setToken] = useState("");
  const [booking, setBooking] = useState<Booking | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const effectiveReference = reference || fragment?.get("reference") || "";
  const effectiveToken = token || fragment?.get("token") || "";

  async function open(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      setBooking(await accessGuestBooking(effectiveReference, effectiveToken));
    } catch (caught) {
      setError(caught instanceof BookingApiError ? caught.message : "Impossible d’ouvrir cette réservation.");
    } finally {
      setLoading(false);
    }
  }

  async function cancel() {
    if (!booking || !window.confirm("Annuler cette réservation ?")) return;
    setLoading(true);
    setError(null);
    try {
      setBooking(await cancelGuestBooking(booking.public_id, effectiveToken));
    } catch (caught) {
      setError(caught instanceof BookingApiError ? caught.message : "Impossible d’annuler cette réservation.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="site-container py-16 sm:py-24">
      <div className="mx-auto max-w-2xl">
        {booking ? (
          <div className="surface-card p-6 sm:p-8">
            <p className="eyebrow">Réservation {booking.reference}</p>
            <h1 className="mt-3 text-3xl font-black text-slate-950">{booking.airport.iata_code} · {booking.service_area.name}</h1>
            <p className="mt-3 text-sm text-slate-600">Statut : <strong>{booking.status}</strong></p>
            <p className="mt-2 text-sm text-slate-600">{new Intl.DateTimeFormat("fr-FR", { dateStyle: "full", timeStyle: "short" }).format(new Date(booking.pickup_at))}</p>
            <p className="mt-7 text-2xl font-black text-slate-950">{formatMoney(booking.total_amount, booking.currency)}</p>
            {booking.cancellation_eligible ? <button className="button button-secondary mt-7" onClick={cancel} disabled={loading}>Annuler la réservation</button> : <p className="mt-7 text-sm text-slate-600">Cette réservation n’est plus dans sa fenêtre d’annulation.</p>}
            {error ? <p className="form-status-error mt-5" role="alert">{error}</p> : null}
          </div>
        ) : (
          <form className="surface-card grid gap-5 p-6 sm:p-8" onSubmit={open}>
            <p className="eyebrow">Gestion sécurisée</p>
            <h1 className="text-3xl font-black text-slate-950">Retrouver ma réservation</h1>
            <p className="text-sm leading-6 text-slate-600">Utilisez la référence et le lien personnel reçus après votre demande.</p>
            <label><span className="form-label">Référence</span><input className="form-input" value={effectiveReference} onChange={(event) => setReference(event.target.value.toUpperCase())} required /></label>
            <label><span className="form-label">Jeton de gestion</span><input className="form-input" type="password" value={effectiveToken} onChange={(event) => setToken(event.target.value)} required /></label>
            {error ? <p className="form-status-error" role="alert">{error}</p> : null}
            <button className="button button-primary" disabled={loading}>{loading ? "Vérification…" : "Ouvrir ma réservation"}</button>
          </form>
        )}
      </div>
    </section>
  );
}
