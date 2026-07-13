import type { Metadata } from "next";

import { AuthShell } from "@/components/auth/auth-shell";
import { PasswordResetConfirmForm } from "@/features/auth/password-reset-confirm-form";

export const metadata: Metadata = { title: "Nouveau mot de passe", robots: { index: false, follow: false } };

export default function ResetPasswordPage() {
  return <AuthShell eyebrow="Sécurité" title="Choisissez un nouveau mot de passe" description="Le lien expire après une heure et ne peut être utilisé qu’une fois."><PasswordResetConfirmForm /></AuthShell>;
}
