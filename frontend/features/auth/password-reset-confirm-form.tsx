"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AuthLink, AuthLinks, FormField, FormStatus } from "@/components/auth/auth-shell";
import { confirmPasswordReset } from "@/lib/auth-api";
import { useSensitiveFragment } from "@/lib/sensitive-fragment";

const schema = z.object({
  password: z.string().min(12, "Utilisez au moins 12 caractères.").max(128),
  confirmation: z.string(),
}).refine((values) => values.password === values.confirmation, { path: ["confirmation"], message: "Les mots de passe ne correspondent pas." });
type Values = z.infer<typeof schema>;

export function PasswordResetConfirmForm() {
  const fragment = useSensitiveFragment();
  const token = fragment?.get("token") ?? "";
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const form = useForm<Values>({ resolver: zodResolver(schema) });
  const submit = form.handleSubmit(async ({ password }) => {
    setError("");
    try { setStatus(await confirmPasswordReset(token, password)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Modification impossible."); }
  });
  if (fragment === null) return <FormStatus type="info">Vérification du lien…</FormStatus>;
  if (!token) return <FormStatus type="error">Ce lien est incomplet. Demandez un nouveau lien de réinitialisation.</FormStatus>;
  if (status) return <div className="grid gap-5"><FormStatus type="success">{status}</FormStatus><AuthLink href="/connexion">Se connecter avec le nouveau mot de passe</AuthLink></div>;
  return <form onSubmit={submit} noValidate className="grid gap-5">{error ? <FormStatus type="error">{error}</FormStatus> : null}<FormField label="Nouveau mot de passe" error={form.formState.errors.password?.message}><input className="form-input" type="password" autoComplete="new-password" aria-invalid={Boolean(form.formState.errors.password)} {...form.register("password")} /></FormField><FormField label="Confirmer le mot de passe" error={form.formState.errors.confirmation?.message}><input className="form-input" type="password" autoComplete="new-password" aria-invalid={Boolean(form.formState.errors.confirmation)} {...form.register("confirmation")} /></FormField><button className="button button-primary w-full" disabled={form.formState.isSubmitting} type="submit">{form.formState.isSubmitting ? "Modification…" : "Modifier le mot de passe"}</button><AuthLinks><AuthLink href="/mot-de-passe-oublie">Demander un autre lien</AuthLink></AuthLinks></form>;
}
