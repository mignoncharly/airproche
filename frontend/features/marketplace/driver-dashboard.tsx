"use client";

import { useEffect, useState } from "react";

type Profile = { display_name: string; business_name: string; phone: string; bio: string; verification_status: string; is_published: boolean };

export function DriverDashboard() {
  const [profile, setProfile] = useState<Profile | null | undefined>(undefined);
  const [message, setMessage] = useState("");
  useEffect(() => { fetch("/api/v1/marketplace/me/profile/", { credentials: "same-origin", cache: "no-store" }).then((r) => r.ok ? r.json() : null).then(setProfile); }, []);
  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = Object.fromEntries(new FormData(event.currentTarget));
    const csrf = await fetch("/api/v1/auth/csrf/", { credentials: "same-origin" }).then((r) => r.json());
    const response = await fetch("/api/v1/marketplace/me/profile/", { method: profile ? "PATCH" : "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-CSRFToken": csrf.csrf_token }, body: JSON.stringify({ ...data, max_passengers: Number(data.max_passengers) }) });
    const result = await response.json(); if (response.ok) { setProfile(result); setMessage("Profil enregistre. Toute modification doit etre reverifiee avant publication."); } else setMessage(result.error?.message || result.detail || "Enregistrement impossible.");
  }
  if (profile === undefined) return null;
  return <section className="border-t border-slate-200 pt-8"><h2 className="text-2xl font-black text-slate-950">Espace chauffeur</h2><p className="mt-2 text-sm leading-6 text-slate-600">Creez votre fiche professionnelle. Elle reste invisible jusqu&apos;a verification par Airproche.</p>
    {profile ? <p className="mt-4 rounded-xl bg-slate-100 p-4 text-sm font-semibold">Statut : {profile.verification_status} {profile.is_published ? "- publie" : "- non publie"}</p> : null}
    <form onSubmit={save} className="mt-5 grid gap-4"><input required name="display_name" className="form-input" placeholder="Nom affiche" defaultValue={profile?.display_name} /><input name="business_name" className="form-input" placeholder="Nom commercial" defaultValue={profile?.business_name} /><input required name="phone" className="form-input" placeholder="Telephone professionnel" defaultValue={profile?.phone} /><input required type="number" min="1" max="30" name="max_passengers" className="form-input" defaultValue="4" /><textarea name="bio" className="form-input min-h-28" maxLength={2000} placeholder="Presentation du service" defaultValue={profile?.bio} /><button className="button button-primary" type="submit">{profile ? "Mettre a jour" : "Creer mon profil chauffeur"}</button>{message ? <p role="status" className="text-sm text-slate-700">{message}</p> : null}</form>
  </section>;
}
