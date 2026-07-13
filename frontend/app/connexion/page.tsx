import type { Metadata } from "next";

import { AuthShell } from "@/components/auth/auth-shell";
import { LoginForm } from "@/features/auth/login-form";

export const metadata: Metadata = { title: "Connexion", robots: { index: false, follow: false } };

export default function LoginPage() {
  return <AuthShell eyebrow="Connexion" title="Retrouvez votre espace client" description="Connectez-vous avec l’adresse e-mail utilisée lors de la création du compte."><LoginForm /></AuthShell>;
}
