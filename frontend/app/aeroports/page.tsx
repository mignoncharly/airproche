import type { Metadata } from "next";
import Link from "next/link";

import { Icon } from "@/components/icon";
import { ContactCta, EmptyNotice, PageHero } from "@/components/marketing";
import { getLocationsAndCoverage } from "@/lib/locations-pricing";
import { getPublicContent } from "@/lib/public-content";

export const metadata: Metadata = {
  title: "Aéroports desservis",
  description: "Consultez les aéroports disposant actuellement d’au moins un trajet tarifé.",
};

export default async function AirportsPage() {
  const [{ settings }, data] = await Promise.all([getPublicContent(), getLocationsAndCoverage()]);
  const coveredIds = new Set(data.coverage.routes.map((route) => route.airport_id));
  const airports = data.airports.filter((airport) => coveredIds.has(airport.public_id));

  return (
    <main>
      <PageHero
        eyebrow="Accueil aéroport"
        title="Des aéroports publiés depuis la couverture réelle"
        description="Chaque aéroport affiché dispose d’au moins un trajet actif vers ou depuis une zone desservie."
      />
      <section className="site-container py-16 sm:py-24">
        {airports.length ? (
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {airports.map((airport) => (
              <article key={airport.public_id} className="surface-card flex flex-col p-7">
                <div className="flex items-center justify-between gap-4">
                  <span className="grid size-12 place-items-center rounded-2xl bg-blue-50 text-blue-700"><Icon name="plane" className="size-6" /></span>
                  <span className="rounded-lg bg-slate-100 px-3 py-1 text-sm font-black tracking-wider text-slate-700">{airport.iata_code}</span>
                </div>
                <h2 className="mt-6 text-xl font-black tracking-tight text-slate-950">{airport.name}</h2>
                <p className="mt-2 text-sm text-slate-600">{airport.city} · {airport.country_code}</p>
                <Link href={`/aeroports/${airport.slug}`} className="mt-6 inline-flex items-center gap-2 text-sm font-bold text-blue-700 hover:underline">
                  Voir les trajets <Icon name="arrow" className="size-4" />
                </Link>
              </article>
            ))}
          </div>
        ) : (
          <EmptyNotice title="Couverture en cours de configuration">
            <p>Aucun aéroport ne dispose encore d’un trajet tarifé actif. Aucune couverture non vérifiée n’est affichée.</p>
          </EmptyNotice>
        )}
      </section>
      <ContactCta settings={settings} title="Une arrivée particulière à organiser ?" />
    </main>
  );
}
