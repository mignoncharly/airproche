"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AuthLink, AuthLinks, FormField, FormStatus } from "@/components/auth/auth-shell";
import { requestPasswordReset } from "@/lib/auth-api";

const schema = z.object({ email: z.string().trim().email("Saisissez une adresse e-mail valide.") });
type Values = z.infer<typeof schema>;

export function PasswordResetRequestForm() {
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const form = useForm<Values>({ resolver: zodResolver(schema) });
  const submit = form.handleSubmit(async ({ email }) => {
    setError("");
    try { setStatus(await requestPasswordReset(email)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Demande impossible."); }
  });
  return <form onSubmit={submit} noValidate className="grid gap-5">{status ? <FormStatus type="success">{status}</FormStatus> : null}{error ? <FormStatus type="error">{error}</FormStatus> : null}<FormField label="Adresse e-mail" error={form.formState.errors.email?.message}><input className="form-input" type="email" autoComplete="email" inputMode="email" aria-invalid={Boolean(form.formState.errors.email)} {...form.register("email")} /></FormField><button className="button button-primary w-full" disabled={form.formState.isSubmitting} type="submit">{form.formState.isSubmitting ? "Envoi…" : "Envoyer le lien"}</button><AuthLinks><AuthLink href="/connexion">Retour à la connexion</AuthLink></AuthLinks></form>;
}
