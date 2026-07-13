import type { Metadata } from "next";
import Link from "next/link";

import { Icon } from "@/components/icon";

export const metadata: Metadata = {
  title: "Hors connexion",
  robots: { index: false, follow: false },
};

export default function OfflinePage() {
  return (
    <main className="site-container grid min-h-[65vh] place-items-center py-16">
      <section className="max-w-xl text-center" aria-labelledby="offline-title">
        <span className="mx-auto grid size-14 place-items-center rounded-lg bg-blue-50 text-blue-700" aria-hidden="true">
          <Icon name="plane" className="size-7" />
        </span>
        <p className="eyebrow mt-6">Hors connexion</p>
        <h1 id="offline-title" className="mt-3 text-3xl font-black text-slate-950">
          Cette page n’est pas disponible sans réseau
        </h1>
        <p className="mt-4 leading-7 text-slate-600">
          Reconnectez-vous pour consulter les informations à jour ou accéder à une réservation.
        </p>
        <Link className="button button-primary mt-7" href="/">
          Réessayer <Icon name="refresh" className="size-4" />
        </Link>
      </section>
    </main>
  );
}
