import type { Metadata } from "next";

import { AuthShell } from "@/components/auth/auth-shell";
import { VerifyEmailForm } from "@/features/auth/verify-email-form";

export const metadata: Metadata = { title: "Vérification de l’adresse e-mail", robots: { index: false, follow: false } };

export default async function VerifyEmailPage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const { token = "" } = await searchParams;
  return <AuthShell eyebrow="Vérification" title="Confirmez votre adresse e-mail" description="Cette étape protège votre compte et les futures informations de réservation."><VerifyEmailForm token={token} /></AuthShell>;
}
