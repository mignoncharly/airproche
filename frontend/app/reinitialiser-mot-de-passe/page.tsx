import type { Metadata } from "next";

import { AuthShell } from "@/components/auth/auth-shell";
import { PasswordResetConfirmForm } from "@/features/auth/password-reset-confirm-form";

export const metadata: Metadata = { title: "Nouveau mot de passe", robots: { index: false, follow: false } };

export default async function ResetPasswordPage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const { token = "" } = await searchParams;
  return <AuthShell eyebrow="Sécurité" title="Choisissez un nouveau mot de passe" description="Le lien expire après une heure et ne peut être utilisé qu’une fois."><PasswordResetConfirmForm token={token} /></AuthShell>;
}
