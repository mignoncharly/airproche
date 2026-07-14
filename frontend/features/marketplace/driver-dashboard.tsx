"use client";

import { useEffect, useState } from "react";

const paymentMethods = [{ value: "cash", label: "Especes" }, { value: "card_terminal", label: "Carte sur terminal" }, { value: "bank_transfer", label: "Virement bancaire" }, { value: "private_payment_link", label: "Lien de paiement prive" }] as const;

type Profile = { display_name: string; business_name: string; phone: string; bio: string; accepted_payment_methods: string[]; verification_status: string; is_published: boolean };

export function DriverDashboard() {
  const [profile, setProfile] = useState<Profile | null | undefined>(undefined);
  const [message, setMessage] = useState("");
  useEffect(() => { fetch("/api/v1/marketplace/me/profile/", { credentials: "same-origin", cache: "no-store" }).then((r) => r.ok ? r.json() : null).then(setProfile); }, []);
  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget); const data = Object.fromEntries(form);
    const csrf = await fetch("/api/v1/auth/csrf/", { credentials: "same-origin" }).then((r) => r.json());
    const response = await fetch("/api/v1/marketplace/me/profile/", { method: profile ? "PATCH" : "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-CSRFToken": csrf.csrf_token }, body: JSON.stringify({ ...data, max_passengers: Number(data.max_passengers), accepted_payment_methods: form.getAll("accepted_payment_methods") }) });
    const result = await response.json(); if (response.ok) { setProfile(result); setMessage("Profil enregistre. Toute modification doit etre reverifiee avant publication."); } else setMessage(result.error?.message || result.detail || "Enregistrement impossible.");
  }
  if (profile === undefined) return null;
  return <section className="border-t border-slate-200 pt-8"><h2 className="text-2xl font-black text-slate-950">Espace chauffeur</h2><p className="mt-2 text-sm leading-6 text-slate-600">Creez votre fiche professionnelle. Elle reste invisible jusqu&apos;a verification par Airproche.</p>
    {profile ? <p className="mt-4 rounded-xl bg-slate-100 p-4 text-sm font-semibold">Statut : {profile.verification_status} {profile.is_published ? "- publie" : "- non publie"}</p> : null}
    <form onSubmit={save} className="mt-5 grid gap-4"><input required name="display_name" className="form-input" placeholder="Nom affiche" defaultValue={profile?.display_name} /><input name="business_name" className="form-input" placeholder="Nom commercial" defaultValue={profile?.business_name} /><input required name="phone" className="form-input" placeholder="Telephone professionnel" defaultValue={profile?.phone} /><input required type="number" min="1" max="30" name="max_passengers" className="form-input" defaultValue="4" /><fieldset className="rounded-xl border border-slate-200 p-4"><legend className="px-2 text-sm font-bold text-slate-800">Moyens de paiement acceptes</legend><div className="grid gap-3 sm:grid-cols-2">{paymentMethods.map((method) => <label key={method.value} className="flex items-center gap-3 text-sm text-slate-700"><input type="checkbox" name="accepted_payment_methods" value={method.value} defaultChecked={profile?.accepted_payment_methods.includes(method.value)} className="size-4 accent-blue-700" />{method.label}</label>)}</div><p className="mt-3 text-xs leading-5 text-slate-500">Ne saisissez aucune coordonnee bancaire. Les details sont communiques en prive apres confirmation.</p></fieldset><textarea name="bio" className="form-input min-h-28" maxLength={2000} placeholder="Presentation du service" defaultValue={profile?.bio} /><button className="button button-primary" type="submit">{profile ? "Mettre a jour" : "Creer mon profil chauffeur"}</button>{message ? <p role="status" className="text-sm text-slate-700">{message}</p> : null}</form>
  </section>;
}
