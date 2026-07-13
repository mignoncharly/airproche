import type { Metadata } from "next";
import Link from "next/link";

import { Icon } from "@/components/icon";
import { ContactCta, EmptyNotice, PageHero } from "@/components/marketing";
import { getLocationsAndCoverage } from "@/lib/locations-pricing";
import { getPublicContent } from "@/lib/public-content";

export const metadata: Metadata = {
  title: "Zones desservies",
  description: "Consultez les zones disposant actuellement d’au moins un trajet aéroport tarifé.",
};

const areaLabels = {
  city: "Ville",
  region: "Région",
  postal_zone: "Zone postale",
  custom: "Zone définie",
};

export default async function ServiceAreasPage() {
  const [{ settings }, data] = await Promise.all([getPublicContent(), getLocationsAndCoverage()]);
  const coveredIds = new Set(data.coverage.routes.map((route) => route.service_area_id));
  const areas = data.serviceAreas.filter((area) => coveredIds.has(area.public_id));

  return (
    <main>
      <PageHero
        eyebrow="Couverture"
        title="Des zones confirmées par un trajet actif"
        description="La liste est alimentée par les zones et tarifs publiés dans le système opérationnel."
      />
      <section className="site-container py-16 sm:py-24">
        {areas.length ? (
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {areas.map((area) => (
              <article key={area.public_id} className="surface-card flex flex-col p-7">
                <span className="grid size-12 place-items-center rounded-2xl bg-blue-50 text-blue-700"><Icon name="route" className="size-6" /></span>
                <p className="mt-6 text-xs font-extrabold uppercase tracking-[0.14em] text-blue-700">{areaLabels[area.area_type]}</p>
                <h2 className="mt-2 text-xl font-black tracking-tight text-slate-950">{area.name}</h2>
                {area.description ? <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-600">{area.description}</p> : null}
                <Link href={`/zones-desservies/${area.slug}`} className="mt-6 inline-flex items-center gap-2 text-sm font-bold text-blue-700 hover:underline">
                  Voir la zone <Icon name="arrow" className="size-4" />
                </Link>
              </article>
            ))}
          </div>
        ) : (
          <EmptyNotice title="Zones en cours de configuration">
            <p>Aucune zone ne dispose encore d’un trajet tarifé actif. Les demandes hors couverture peuvent être vérifiées manuellement.</p>
          </EmptyNotice>
        )}
      </section>
      <ContactCta settings={settings} title="Vous souhaitez vérifier une autre destination ?" />
    </main>
  );
}
