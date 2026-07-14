import type { Metadata } from "next";
import Link from "next/link";

import { Icon } from "@/components/icon";
import { ContactCta, EmptyNotice, PageHero } from "@/components/marketing";
import { getLocationsAndCoverage } from "@/lib/locations-pricing";
import { getPublicContent } from "@/lib/public-content";
import { publicMetadata } from "@/lib/seo";

export const metadata: Metadata = publicMetadata(
  "Aéroports desservis",
  "Consultez les aéroports proposés dans l’annuaire Airproche.",
  "/aeroports",
);

export default async function AirportsPage() {
  const [{ settings }, data] = await Promise.all([getPublicContent(), getLocationsAndCoverage()]);
  const airports = data.airports;

  return (
    <main>
      <PageHero
        eyebrow="Accueil aéroport"
        title="Les principaux aéroports de la région parisienne"
        description="Consultez les informations utiles puis trouvez un chauffeur indépendant qui dessert votre aéroport."
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
                  Voir l’aéroport <Icon name="arrow" className="size-4" />
                </Link>
              </article>
            ))}
          </div>
        ) : (
          <EmptyNotice title="Aéroports en cours de publication">
            <p>Aucun aéroport actif n’est publié actuellement.</p>
          </EmptyNotice>
        )}
      </section>
      <ContactCta settings={settings} title="Une arrivée particulière à organiser ?" />
    </main>
  );
}
