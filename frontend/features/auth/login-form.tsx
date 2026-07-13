"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AuthLink, AuthLinks, FormField, FormStatus } from "@/components/auth/auth-shell";
import { loginAccount } from "@/lib/auth-api";

const schema = z.object({
  email: z.string().trim().email("Saisissez une adresse e-mail valide."),
  password: z.string().min(1, "Saisissez votre mot de passe."),
});
type Values = z.infer<typeof schema>;

export function LoginForm() {
  const router = useRouter();
  const [serverError, setServerError] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Values>({ resolver: zodResolver(schema) });

  const submit = handleSubmit(async (values) => {
    setServerError("");
    try {
      await loginAccount(values.email, values.password);
      router.push("/compte");
      router.refresh();
    } catch (error) {
      setServerError(error instanceof Error ? error.message : "Connexion impossible.");
    }
  });

  return (
    <form onSubmit={submit} noValidate className="grid gap-5">
      {serverError ? <FormStatus type="error">{serverError}</FormStatus> : null}
      <FormField label="Adresse e-mail" error={errors.email?.message}><input className="form-input" type="email" autoComplete="email" inputMode="email" aria-invalid={Boolean(errors.email)} {...register("email")} /></FormField>
      <FormField label="Mot de passe" error={errors.password?.message}><input className="form-input" type="password" autoComplete="current-password" aria-invalid={Boolean(errors.password)} {...register("password")} /></FormField>
      <button className="button button-primary w-full" type="submit" disabled={isSubmitting}>{isSubmitting ? "Connexion…" : "Se connecter"}</button>
      <AuthLinks><AuthLink href="/mot-de-passe-oublie">Mot de passe oublié ?</AuthLink><span>Pas encore de compte ? <AuthLink href="/inscription">Créer un compte</AuthLink></span></AuthLinks>
    </form>
  );
}
