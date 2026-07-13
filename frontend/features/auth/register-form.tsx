"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AuthLink, AuthLinks, FormField, FormStatus } from "@/components/auth/auth-shell";
import { registerAccount } from "@/lib/auth-api";

const schema = z.object({
  first_name: z.string().trim().min(1, "Saisissez votre prénom.").max(150),
  last_name: z.string().trim().min(1, "Saisissez votre nom.").max(150),
  email: z.string().trim().email("Saisissez une adresse e-mail valide."),
  phone: z.string().trim().max(32, "Le numéro est trop long."),
  password: z.string().min(12, "Utilisez au moins 12 caractères.").max(128),
  confirm_password: z.string(),
  accept_terms: z.boolean().refine(Boolean, "Vous devez accepter les conditions générales."),
  accept_privacy: z.boolean().refine(Boolean, "Vous devez reconnaître la politique de confidentialité."),
}).refine((values) => values.password === values.confirm_password, { path: ["confirm_password"], message: "Les mots de passe ne correspondent pas." });
type Values = z.infer<typeof schema>;

export function RegisterForm() {
  const [serverError, setServerError] = useState("");
  const [success, setSuccess] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { phone: "", accept_terms: false, accept_privacy: false },
  });

  const submit = handleSubmit(async (values) => {
    setServerError("");
    setSuccess("");
    try {
      const result = await registerAccount({
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        phone: values.phone,
        password: values.password,
        accept_terms: values.accept_terms,
        accept_privacy: values.accept_privacy,
      });
      setSuccess(result.verification_email_sent ? result.message : `${result.message} L’e-mail n’a pas pu être envoyé ; vous pourrez demander un nouveau lien après connexion.`);
    } catch (error) {
      setServerError(error instanceof Error ? error.message : "Inscription impossible.");
    }
  });

  if (success) return <div className="grid gap-5"><FormStatus type="success">{success}</FormStatus><AuthLink href="/connexion">Continuer vers la connexion</AuthLink></div>;

  return (
    <form onSubmit={submit} noValidate className="grid gap-5">
      {serverError ? <FormStatus type="error">{serverError}</FormStatus> : null}
      <div className="grid gap-5 sm:grid-cols-2">
        <FormField label="Prénom" error={errors.first_name?.message}><input className="form-input" autoComplete="given-name" aria-invalid={Boolean(errors.first_name)} {...register("first_name")} /></FormField>
        <FormField label="Nom" error={errors.last_name?.message}><input className="form-input" autoComplete="family-name" aria-invalid={Boolean(errors.last_name)} {...register("last_name")} /></FormField>
      </div>
      <FormField label="Adresse e-mail" error={errors.email?.message}><input className="form-input" type="email" autoComplete="email" inputMode="email" aria-invalid={Boolean(errors.email)} {...register("email")} /></FormField>
      <FormField label="Téléphone (facultatif)" error={errors.phone?.message}><input className="form-input" type="tel" autoComplete="tel" inputMode="tel" aria-invalid={Boolean(errors.phone)} {...register("phone")} /></FormField>
      <FormField label="Mot de passe" error={errors.password?.message} hint="Au moins 12 caractères ; évitez un mot de passe déjà utilisé ailleurs."><input className="form-input" type="password" autoComplete="new-password" aria-invalid={Boolean(errors.password)} {...register("password")} /></FormField>
      <FormField label="Confirmer le mot de passe" error={errors.confirm_password?.message}><input className="form-input" type="password" autoComplete="new-password" aria-invalid={Boolean(errors.confirm_password)} {...register("confirm_password")} /></FormField>
      <label className="flex items-start gap-3 text-sm leading-6 text-slate-700"><input type="checkbox" className="mt-1 size-4 accent-blue-700" {...register("accept_terms")} /><span>J’accepte les <AuthLink href="/conditions-generales">conditions générales</AuthLink>.</span></label>{errors.accept_terms ? <p className="form-error -mt-4">{errors.accept_terms.message}</p> : null}
      <label className="flex items-start gap-3 text-sm leading-6 text-slate-700"><input type="checkbox" className="mt-1 size-4 accent-blue-700" {...register("accept_privacy")} /><span>J’ai lu la <AuthLink href="/confidentialite">politique de confidentialité</AuthLink>.</span></label>{errors.accept_privacy ? <p className="form-error -mt-4">{errors.accept_privacy.message}</p> : null}
      <button className="button button-primary w-full" type="submit" disabled={isSubmitting}>{isSubmitting ? "Création…" : "Créer mon compte"}</button>
      <AuthLinks><span>Déjà inscrit ? <AuthLink href="/connexion">Se connecter</AuthLink></span></AuthLinks>
    </form>
  );
}
