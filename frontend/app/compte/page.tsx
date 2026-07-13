import type { Metadata } from "next";

import { AuthShell } from "@/components/auth/auth-shell";
import { AccountPanel } from "@/features/auth/account-panel";

export const metadata: Metadata = { title: "Mon compte", robots: { index: false, follow: false } };

export default function AccountPage() {
  return <AuthShell eyebrow="Mon compte" title="Mes coordonnées" description="Consultez et mettez à jour les coordonnées associées à votre compte."><AccountPanel /></AuthShell>;
}
