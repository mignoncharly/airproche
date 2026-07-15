"use client";

import Link from "next/link";
import { useState } from "react";

type Result = { message: string; reference: string; notification_state: "pending" | "sent" };

export function InquiryForm({ driverId, driverName, airports, privacyVersion }: { driverId: string; driverName: string; airports: Array<{ public_id: string; name: string }>; privacyVersion: string }) {
  const [startedAt, setStartedAt] = useState(() => Date.now());
  const [idempotencyKey, setIdempotencyKey] = useState(() => crypto.randomUUID());
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [globalError, setGlobalError] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const form = event.currentTarget;
    if (!form.reportValidity()) return;
    setBusy(true); setGlobalError(""); setErrors({});
    try {
      const data = new FormData(form);
      const csrfResponse = await fetch("/api/v1/auth/csrf/", { credentials: "same-origin", cache: "no-store" });
      if (!csrfResponse.ok) throw new Error("La protection du formulaire est indisponible.");
      const csrf = await csrfResponse.json();
      const preferred = String(data.get("preferred_contact_method"));
      const response = await fetch("/api/v1/marketplace/inquiries/", {
        method: "POST", credentials: "same-origin", cache: "no-store",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf.csrf_token, "Idempotency-Key": idempotencyKey },
        body: JSON.stringify({
          driver_id: driverId, airport_id: data.get("airport_id"), direction: data.get("direction"), destination: data.get("destination"), pickup_at: data.get("pickup_at") || null,
          customer_name: data.get("customer_name"), customer_email: data.get("customer_email"), customer_phone: data.get("customer_phone"), customer_whatsapp: data.get("customer_whatsapp") || "",
          preferred_contact_method: preferred, whatsapp_consent: data.get("whatsapp_consent") === "on", allowed_contact_channels: [preferred], passenger_count: Number(data.get("passenger_count")), luggage_count: Number(data.get("luggage_count")), message: data.get("message"),
          privacy_consent: data.get("privacy_consent") === "on", privacy_policy_version: privacyVersion, consent_text_version: "marketplace-inquiry-v1", website: data.get("website"), form_started_at: startedAt,
        }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        const fields = body.error?.fields ?? {};
        setErrors(Object.fromEntries(Object.entries(fields).map(([key, value]) => [key, Array.isArray(value) ? String(value[0]) : String(value)])));
        throw new Error(body.error?.message || "La demande n’a pas pu être enregistrée.");
      }
      setResult(body);
      form.reset();
      setIdempotencyKey(crypto.randomUUID());
      setStartedAt(Date.now());
    } catch (error) { setGlobalError(error instanceof Error ? error.message : "Envoi impossible."); }
    finally { setBusy(false); }
  }

  if (result) return <section className="rounded-[2rem] border border-emerald-200 bg-emerald-50 p-6 sm:p-8" aria-live="polite"><p className="text-sm font-black uppercase tracking-wider text-emerald-800">Demande reçue par AirProche</p><h2 className="mt-3 text-2xl font-black text-slate-950">Demande {result.reference}</h2><p className="mt-4 leading-7 text-slate-700">{result.message}</p><p className="mt-4 text-sm font-semibold text-slate-700">{result.notification_state === "sent" ? "Le chauffeur a été informé par e-mail." : "L’envoi de l’e-mail au chauffeur est en cours. La demande est déjà visible dans son espace."}</p></section>;

  const error = (name: string) => errors[name] ? <span id={`${name}-error`} className="form-error">{errors[name]}</span> : null;
  return <form onSubmit={submit} className="surface-card grid gap-5 p-6 sm:p-8" noValidate>
    <div><p className="eyebrow">Contact direct</p><h2 className="mt-2 text-2xl font-black text-slate-950">Envoyer une demande à {driverName}</h2><p className="mt-3 text-sm leading-6 text-slate-600">Le trajet n’est pas confirmé à ce stade. Le chauffeur confirme directement sa disponibilité, son tarif et ses conditions.</p></div>
    <div className="sr-only" aria-hidden="true"><label>Site web<input name="website" tabIndex={-1} autoComplete="off" /></label></div>
    <label><span className="form-label">Votre nom <span aria-hidden="true">*</span></span><input required name="customer_name" autoComplete="name" className="form-input" aria-describedby={errors.customer_name ? "customer_name-error" : undefined} />{error("customer_name")}</label>
    <div className="grid gap-5 sm:grid-cols-2"><label><span className="form-label">E-mail <span aria-hidden="true">*</span></span><input required type="email" name="customer_email" autoComplete="email" className="form-input" />{error("customer_email")}</label><label><span className="form-label">Téléphone <span aria-hidden="true">*</span></span><input required type="tel" name="customer_phone" autoComplete="tel" className="form-input" />{error("customer_phone")}</label></div>
    <div className="grid gap-5 sm:grid-cols-2"><label><span className="form-label">Aéroport <span aria-hidden="true">*</span></span><select required name="airport_id" className="form-input" defaultValue=""><option value="" disabled>Choisir un aéroport</option>{airports.map((airport) => <option key={airport.public_id} value={airport.public_id}>{airport.name}</option>)}</select>{error("airport_id")}</label><label><span className="form-label">Sens du trajet <span aria-hidden="true">*</span></span><select required name="direction" className="form-input"><option value="airport_to_destination">Aéroport vers destination</option><option value="destination_to_airport">Destination vers aéroport</option></select>{error("direction")}</label></div>
    <label><span className="form-label">Adresse, hôtel, gare ou entreprise hors aéroport <span aria-hidden="true">*</span></span><input required minLength={3} name="destination" className="form-input" />{error("destination")}</label>
    <div className="grid gap-5 sm:grid-cols-3"><label><span className="form-label">Date et heure</span><input type="datetime-local" name="pickup_at" className="form-input" /></label><label><span className="form-label">Passagers <span aria-hidden="true">*</span></span><input required type="number" min="1" max="30" name="passenger_count" defaultValue="1" className="form-input" /></label><label><span className="form-label">Bagages</span><input type="number" min="0" max="60" name="luggage_count" defaultValue="0" className="form-input" /></label></div>
    <label><span className="form-label">Moyen de contact préféré</span><select name="preferred_contact_method" className="form-input"><option value="email">E-mail</option><option value="phone">Téléphone</option><option value="whatsapp">WhatsApp</option></select></label>
    <label><span className="form-label">Numéro WhatsApp, si différent</span><input type="tel" name="customer_whatsapp" className="form-input" /></label>
    <label className="flex items-start gap-3 text-sm leading-6 text-slate-700"><input type="checkbox" name="whatsapp_consent" className="mt-1 size-4" />J’autorise ce chauffeur à me contacter sur WhatsApp au sujet de cette demande.</label>
    <label><span className="form-label">Informations utiles</span><textarea name="message" className="form-input min-h-28" maxLength={2000} placeholder="Vol, bagages particuliers, accessibilité ou point de rencontre" />{error("message")}</label>
    <label className="flex items-start gap-3 rounded-xl bg-slate-50 p-4 text-sm leading-6 text-slate-700"><input required type="checkbox" name="privacy_consent" className="mt-1 size-4" /><span>J’accepte que mes coordonnées et les informations du trajet soient transmises à ce chauffeur pour traiter ma demande. <Link className="font-bold text-blue-700 underline" href="/confidentialite" target="_blank">Lire la politique de confidentialité</Link>.</span></label>{error("privacy_consent")}
    <p className="text-xs leading-5 text-slate-500">AirProche agit comme intermédiaire. Le contrat de transport, le tarif, le paiement et les conditions sont convenus directement avec le chauffeur.</p>
    {globalError ? <p className="form-status-error" role="alert">{globalError}</p> : null}
    <button className="button button-primary" type="submit" disabled={busy}>{busy ? "Envoi sécurisé…" : "Envoyer la demande"}</button>
  </form>;
}
