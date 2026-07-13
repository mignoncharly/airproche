import type { Metadata } from "next";

import { AuthShell } from "@/components/auth/auth-shell";
import { PasswordResetRequestForm } from "@/features/auth/password-reset-request-form";

export const metadata: Metadata = { title: "Mot de passe oublié", robots: { index: false, follow: false } };

export default function ForgotPasswordPage() {
  return <AuthShell eyebrow="Accès au compte" title="Réinitialisez votre mot de passe" description="La réponse reste identique pour toutes les adresses afin de protéger l’existence des comptes."><PasswordResetRequestForm /></AuthShell>;
}
