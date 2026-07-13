import type { Metadata } from "next";

import { AuthShell, FormStatus } from "@/components/auth/auth-shell";
import { RegisterForm } from "@/features/auth/register-form";
import { getPublicContent } from "@/lib/public-content";

export const metadata: Metadata = { title: "Créer un compte", robots: { index: false, follow: false } };

export default async function RegistrationPage() {
  const content = await getPublicContent();
  const published = new Set(content.legal_documents.map((document) => document.kind));
  const available = published.has("terms") && published.has("privacy");
  return <AuthShell eyebrow="Inscription" title="Créez votre espace client" description="Votre adresse e-mail devra être vérifiée avant toute modification sensible.">{available ? <RegisterForm /> : <FormStatus type="info">L’inscription n’est pas encore ouverte. Les conditions générales et la politique de confidentialité doivent d’abord être validées et publiées.</FormStatus>}</AuthShell>;
}
