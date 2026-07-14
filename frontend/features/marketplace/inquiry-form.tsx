"use client";

import { useState } from "react";

export function InquiryForm({ driverId, airports }: { driverId: string; airports: Array<{ public_id: string; name: string }> }) {
  const [status, setStatus] = useState("");
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setStatus("Envoi...");
    const form = new FormData(event.currentTarget);
    const csrf = await fetch("/api/v1/auth/csrf/", { credentials: "same-origin" }).then((r) => r.json());
    const response = await fetch("/api/v1/marketplace/inquiries/", {
      method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-CSRFToken": csrf.csrf_token },
      body: JSON.stringify({ driver_id: driverId, airport_id: form.get("airport_id") || null, customer_name: form.get("customer_name"), customer_email: form.get("customer_email"), customer_phone: form.get("customer_phone"), destination: form.get("destination"), pickup_at: form.get("pickup_at") || null, passenger_count: Number(form.get("passenger_count")), message: form.get("message") }),
    });
    const body = await response.json().catch(() => ({}));
    setStatus(response.ok ? body.message : body.error?.message || "La demande n'a pas pu etre envoyee.");
    if (response.ok) event.currentTarget.reset();
  }
  return <form onSubmit={submit} className="surface-card grid gap-4 p-6">
    <h2 className="text-2xl font-black text-slate-950">Demander au chauffeur</h2>
    <p className="text-sm leading-6 text-slate-600">Demande non contraignante. Le chauffeur confirme directement le prix, la disponibilite et le trajet. Le paiement se fait directement au chauffeur.</p>
    <input required name="customer_name" className="form-input" placeholder="Votre nom" />
    <div className="grid gap-4 sm:grid-cols-2"><input required type="email" name="customer_email" className="form-input" placeholder="E-mail" /><input required name="customer_phone" className="form-input" placeholder="Telephone" /></div>
    <select name="airport_id" className="form-input" defaultValue=""><option value="">Choisir un aeroport</option>{airports.map((a) => <option key={a.public_id} value={a.public_id}>{a.name}</option>)}</select>
    <input required name="destination" className="form-input" placeholder="Destination" />
    <div className="grid gap-4 sm:grid-cols-2"><input type="datetime-local" name="pickup_at" className="form-input" /><input required type="number" min="1" max="30" name="passenger_count" defaultValue="1" className="form-input" /></div>
    <textarea name="message" className="form-input min-h-28" placeholder="Bagages, vol et besoins particuliers" maxLength={2000} />
    <button className="button button-primary" type="submit">Envoyer la demande</button>
    {status ? <p role="status" className="text-sm font-semibold text-slate-700">{status}</p> : null}
  </form>;
}
