"use client";

import { useState } from "react";

import { AuthLink, FormStatus } from "@/components/auth/auth-shell";
import { verifyEmail } from "@/lib/auth-api";
import { useSensitiveFragment } from "@/lib/sensitive-fragment";

export function VerifyEmailForm() {
  const fragment = useSensitiveFragment();
  const token = fragment?.get("token") ?? "";
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  if (fragment === null) return <FormStatus type="info">Vérification du lien…</FormStatus>;
  if (!token) return <FormStatus type="error">Ce lien est incomplet. Connectez-vous pour demander un nouveau lien.</FormStatus>;
  const submit = async () => {
    setLoading(true);
    setError("");
    try { setStatus(await verifyEmail(token)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Vérification impossible."); } finally { setLoading(false); }
  };
  if (status) return <div className="grid gap-5"><FormStatus type="success">{status}</FormStatus><AuthLink href="/connexion">Continuer vers la connexion</AuthLink></div>;
  return <div className="grid gap-5">{error ? <FormStatus type="error">{error}</FormStatus> : null}<button type="button" className="button button-primary w-full" onClick={submit} disabled={loading}>{loading ? "Vérification…" : "Vérifier mon adresse"}</button><p className="text-center text-xs leading-5 text-slate-500">Ce lien est personnel et ne peut être utilisé qu’une fois.</p></div>;
}
