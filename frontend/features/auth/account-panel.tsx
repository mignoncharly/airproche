"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FormField, FormStatus } from "@/components/auth/auth-shell";
import { type AccountUser, currentAccount, logoutAccount, resendVerification, updateProfile } from "@/lib/auth-api";
import { CustomerDashboard } from "@/features/bookings/customer-dashboard";

const schema = z.object({
  first_name: z.string().trim().min(1, "Saisissez votre prénom.").max(150),
  last_name: z.string().trim().min(1, "Saisissez votre nom.").max(150),
  phone: z.string().trim().max(32, "Le numéro est trop long."),
});
type Values = z.infer<typeof schema>;

export function AccountPanel() {
  const router = useRouter();
  const [user, setUser] = useState<AccountUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const form = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { first_name: "", last_name: "", phone: "" } });

  useEffect(() => {
    currentAccount().then((account) => {
      if (!account) { router.replace("/connexion"); return; }
      setUser(account);
      form.reset({ first_name: account.first_name, last_name: account.last_name, phone: account.phone });
    }).catch((reason) => setError(reason instanceof Error ? reason.message : "Compte indisponible.")).finally(() => setLoading(false));
  }, [form, router]);

  const save = form.handleSubmit(async (values) => {
    setError(""); setMessage("");
    try { const updated = await updateProfile(values); setUser(updated); setMessage("Vos coordonnées ont été mises à jour."); } catch (reason) { setError(reason instanceof Error ? reason.message : "Modification impossible."); }
  });
  const resend = async () => { setError(""); try { setMessage(await resendVerification()); } catch (reason) { setError(reason instanceof Error ? reason.message : "Envoi impossible."); } };
  const signOut = async () => { setError(""); try { await logoutAccount(); router.push("/"); router.refresh(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Déconnexion impossible."); } };

  if (loading) return <p role="status" className="text-sm text-slate-600">Chargement du compte…</p>;
  if (!user) return error ? <FormStatus type="error">{error}</FormStatus> : null;
  return (
    <div className="grid gap-8">
      {message ? <FormStatus type="success">{message}</FormStatus> : null}
      {error ? <FormStatus type="error">{error}</FormStatus> : null}
      {!user.email_verified ? <FormStatus type="info"><span className="block font-bold">Adresse e-mail non vérifiée</span><span className="mt-1 block">Vérifiez votre adresse avant de modifier le profil.</span><button type="button" className="mt-3 font-bold text-blue-700 underline" onClick={resend}>Renvoyer le lien</button></FormStatus> : null}
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5"><p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">Adresse du compte</p><p className="mt-2 font-bold text-slate-950">{user.email}</p></div>
      <form onSubmit={save} noValidate className="grid gap-5">
        <div className="grid gap-5 sm:grid-cols-2"><FormField label="Prénom" error={form.formState.errors.first_name?.message}><input className="form-input" autoComplete="given-name" disabled={!user.email_verified} aria-invalid={Boolean(form.formState.errors.first_name)} {...form.register("first_name")} /></FormField><FormField label="Nom" error={form.formState.errors.last_name?.message}><input className="form-input" autoComplete="family-name" disabled={!user.email_verified} aria-invalid={Boolean(form.formState.errors.last_name)} {...form.register("last_name")} /></FormField></div>
        <FormField label="Téléphone" error={form.formState.errors.phone?.message}><input className="form-input" type="tel" autoComplete="tel" disabled={!user.email_verified} aria-invalid={Boolean(form.formState.errors.phone)} {...form.register("phone")} /></FormField>
        <button className="button button-primary" type="submit" disabled={form.formState.isSubmitting || !user.email_verified}>{form.formState.isSubmitting ? "Enregistrement…" : "Enregistrer les modifications"}</button>
      </form>
      <div className="border-t border-slate-200 pt-6"><button type="button" className="text-sm font-bold text-slate-600 hover:text-red-700" onClick={signOut}>Se déconnecter</button></div>
      <CustomerDashboard />
    </div>
  );
}
