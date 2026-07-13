"use client";

import Link from "next/link";
import { useState } from "react";

import { trackConversion } from "@/lib/analytics";
import { BookingApiError, type Booking, type BookingQuote, createBooking } from "@/lib/booking-api";
import { formatMoney } from "@/lib/locations-pricing";
import { CheckoutAction } from "@/features/payments/checkout-action";

const steps = ["Trajet", "Voyageurs", "Contact", "Revue"];

export function BookingForm({ quote }: { quote: BookingQuote }) {
  const [step, setStep] = useState(0);
  const [samePassenger, setSamePassenger] = useState(true);
  const [values, setValues] = useState<Record<string, string | boolean>>({
    pickup_address: "", destination_address: "", flight_number: "", terminal: "",
    booker_first_name: "", booker_last_name: "", booker_email: "", booker_phone: "",
    passenger_first_name: "", passenger_last_name: "", passenger_phone: "",
    adult_count: String(quote.passenger_count), child_count: "0", oversized_luggage_count: "0",
    accept_terms: false, accept_privacy: false,
  });
  const [booking, setBooking] = useState<Booking | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function set(name: string, value: string | boolean) { setValues((current) => ({ ...current, [name]: value })); }
  function next() { setError(null); setStep((current) => Math.min(3, current + 1)); }
  function previous() { setError(null); setStep((current) => Math.max(0, current - 1)); }

  async function submit() {
    setSubmitting(true); setError(null);
    try {
      trackConversion("booking_started", { trip_type: quote.trip_type, currency: quote.currency });
      const adultCount = Number(values.adult_count);
      const childCount = Number(values.child_count);
      const result = await createBooking({
        quote_id: quote.public_id, booking_type: quote.trip_type,
        pickup_address: values.pickup_address, destination_address: values.destination_address,
        flight_number: values.flight_number, terminal: values.terminal,
        adult_count: adultCount, child_count: childCount, oversized_luggage_count: Number(values.oversized_luggage_count),
        passenger_same_as_booker: samePassenger,
        booker_first_name: values.booker_first_name, booker_last_name: values.booker_last_name,
        booker_email: values.booker_email, booker_phone: values.booker_phone,
        passenger_first_name: samePassenger ? values.booker_first_name : values.passenger_first_name,
        passenger_last_name: samePassenger ? values.booker_last_name : values.passenger_last_name,
        passenger_phone: samePassenger ? values.booker_phone : values.passenger_phone,
        accept_terms: values.accept_terms, accept_privacy: values.accept_privacy,
      });
      setBooking(result);
      trackConversion("booking_created", { trip_type: quote.trip_type, currency: result.currency });
    } catch (caught) {
      setError(caught instanceof BookingApiError ? caught.message : "Le service de réservation est momentanément indisponible.");
    } finally { setSubmitting(false); }
  }

  if (booking) {
    const manageUrl = `/reservation/gerer?reference=${encodeURIComponent(booking.reference)}#token=${encodeURIComponent(booking.management_token ?? "")}`;
    return <section className="surface-card p-6 sm:p-8" aria-live="polite"><p className="eyebrow">Demande enregistrée</p><h2 className="mt-3 text-3xl font-black text-slate-950">Référence {booking.reference}</h2><p className="mt-4 text-sm leading-6 text-slate-600">Votre réservation est enregistrée et attend la confirmation du paiement. Conservez le lien de gestion sécurisé ci-dessous.</p><CheckoutAction booking={booking} /><Link className="button button-primary mt-7" href={manageUrl}>Gérer ma réservation</Link><p className="mt-4 text-xs text-slate-500">Le lien de gestion est personnel. Ne le partagez pas.</p></section>;
  }

  const field = (name: string, label: string, type = "text") => <label><span className="form-label">{label}</span><input className="form-input" type={type} value={String(values[name] ?? "")} onChange={(event) => set(name, event.target.value)} /></label>;
  return <div className="grid gap-7 lg:grid-cols-[1.1fr_0.9fr]"><div className="surface-card p-6 sm:p-8"><ol className="grid grid-cols-4 gap-2" aria-label="Étapes de réservation">{steps.map((label, index) => <li key={label} className={`rounded-lg px-2 py-3 text-center text-xs font-bold ${index === step ? "bg-blue-700 text-white" : "bg-slate-100 text-slate-500"}`}><span className="sr-only">Étape {index + 1} : </span>{label}</li>)}</ol>
    {error ? <p className="form-status-error mt-5" role="alert">{error}</p> : null}
    <div className="mt-8 grid gap-5">
      {step === 0 ? <><h2 className="text-xl font-black text-slate-950">Votre trajet</h2>{field("pickup_address", "Adresse de prise en charge")}{field("destination_address", "Adresse de destination")}{field("flight_number", "Numéro de vol (facultatif)")}{field("terminal", "Terminal (facultatif)")}</> : null}
      {step === 1 ? <><h2 className="text-xl font-black text-slate-950">Voyageurs et bagages</h2><p className="text-sm text-slate-600">Le devis couvre {quote.passenger_count} passager(s) et {quote.luggage_count} bagage(s).</p><div className="grid gap-5 sm:grid-cols-2">{field("adult_count", "Adultes", "number")}{field("child_count", "Enfants", "number")}{field("oversized_luggage_count", "Bagages hors format", "number")}</div></> : null}
      {step === 2 ? <><h2 className="text-xl font-black text-slate-950">Coordonnées</h2><div className="grid gap-5 sm:grid-cols-2">{field("booker_first_name", "Prénom")}{field("booker_last_name", "Nom")}</div>{field("booker_email", "Adresse e-mail", "email")}{field("booker_phone", "Téléphone", "tel")}<label className="flex items-center gap-3 text-sm font-semibold text-slate-700"><input type="checkbox" checked={samePassenger} onChange={(event) => setSamePassenger(event.target.checked)} />Le passager est la personne qui réserve</label>{!samePassenger ? <div className="grid gap-5 sm:grid-cols-2">{field("passenger_first_name", "Prénom du passager")}{field("passenger_last_name", "Nom du passager")}{field("passenger_phone", "Téléphone du passager", "tel")}</div> : null}</> : null}
      {step === 3 ? <><h2 className="text-xl font-black text-slate-950">Vérifier et envoyer</h2><dl className="grid gap-3 rounded-xl bg-slate-50 p-4 text-sm"><div className="flex justify-between gap-4"><dt className="text-slate-600">Trajet</dt><dd className="font-bold text-slate-950">{quote.airport_iata_code} · {quote.service_area_name}</dd></div><div className="flex justify-between gap-4"><dt className="text-slate-600">Prise en charge</dt><dd className="font-bold text-slate-950">{new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(quote.pickup_at))}</dd></div><div className="flex justify-between gap-4"><dt className="text-slate-600">Total</dt><dd className="font-black text-slate-950">{formatMoney(quote.total_amount, quote.currency)}</dd></div></dl><label className="flex items-start gap-3 text-sm leading-6 text-slate-700"><input className="mt-1" type="checkbox" checked={Boolean(values.accept_terms)} onChange={(event) => set("accept_terms", event.target.checked)} />J’accepte les conditions de réservation.</label><label className="flex items-start gap-3 text-sm leading-6 text-slate-700"><input className="mt-1" type="checkbox" checked={Boolean(values.accept_privacy)} onChange={(event) => set("accept_privacy", event.target.checked)} />J’accepte la politique de confidentialité.</label></> : null}
    </div><div className="mt-8 flex flex-wrap gap-3">{step > 0 ? <button type="button" className="button button-secondary" onClick={previous}>Retour</button> : null}{step < 3 ? <button type="button" className="button button-primary" onClick={next}>Continuer</button> : <button type="button" className="button button-primary" onClick={submit} disabled={submitting}>{submitting ? "Enregistrement…" : "Enregistrer la réservation"}</button>}</div>
  </div><aside className="surface-card h-fit p-6 sm:p-8"><p className="eyebrow">Devis serveur</p><p className="mt-4 text-3xl font-black text-slate-950">{formatMoney(quote.total_amount, quote.currency)}</p><p className="mt-2 text-sm text-slate-600">{quote.airport_iata_code} · {quote.service_area_name}</p><ul className="mt-6 grid gap-3 border-y border-slate-200 py-5 text-sm">{quote.lines.map((line) => <li key={line.code} className="flex justify-between gap-4"><span className="text-slate-600">{line.label}</span><strong>{formatMoney(line.total_amount, quote.currency)}</strong></li>)}</ul><p className="mt-5 text-xs leading-5 text-slate-500">Le montant est repris depuis le devis et recalculé côté serveur lors de l’enregistrement.</p></aside></div>;
}
