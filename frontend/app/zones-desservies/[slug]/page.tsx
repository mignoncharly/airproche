import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Icon } from "@/components/icon";
import { ContactCta, PageHero, SectionHeading } from "@/components/marketing";
import { getLocationsAndCoverage, getServiceArea } from "@/lib/locations-pricing";
import { getPublicContent } from "@/lib/public-content";

type PageProps = { params: Promise<{ slug: string }> };

export async function generateStaticParams() {
  const data = await getLocationsAndCoverage();
  const covered = new Set(data.coverage.routes.map((route) => route.service_area_id));
  return data.serviceAreas.filter((area) => covered.has(area.public_id)).map((area) => ({ slug: area.slug }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const area = await getServiceArea(slug);
  if (!area) return { title: "Zone indisponible" };
  return {
    title: `Transferts aéroport — ${area.name}`,
    description: area.description || `Consultez les trajets aéroport actuellement tarifés pour ${area.name}.`,
  };
}

export default async function ServiceAreaPage({ params }: PageProps) {
  const { slug } = await params;
  const [area, data, { settings }] = await Promise.all([
    getServiceArea(slug),
    getLocationsAndCoverage(),
    getPublicContent(),
  ]);
  if (!area) notFound();
  const routes = data.coverage.routes.filter((route) => route.service_area_id === area.public_id);
  if (!routes.length) notFound();
  const airportIds = new Set(routes.map((route) => route.airport_id));
  const airports = data.airports.filter((airport) => airportIds.has(airport.public_id));

  return (
    <main>
      <PageHero
        eyebrow="Zone desservie"
        title={`Transferts aéroport pour ${area.name}`}
        description={area.description || "Cette zone dispose d’au moins un trajet aéroport actif et tarifé."}
      />
      <section className="site-container py-16 sm:py-24">
        <div className="grid gap-12 lg:grid-cols-[0.75fr_1.25fr]">
          <div>
            <SectionHeading eyebrow="Périmètre" title="Une zone configurée précisément" />
            <dl className="mt-7 grid gap-4 text-sm">
              {area.city ? <div className="rounded-xl border border-slate-200 p-4"><dt className="font-bold text-slate-950">Ville</dt><dd className="mt-1 text-slate-600">{area.city}</dd></div> : null}
              {area.region ? <div className="rounded-xl border border-slate-200 p-4"><dt className="font-bold text-slate-950">Région</dt><dd className="mt-1 text-slate-600">{area.region}</dd></div> : null}
              {area.postal_codes.length ? <div className="rounded-xl border border-slate-200 p-4"><dt className="font-bold text-slate-950">Codes postaux publiés</dt><dd className="mt-1 text-slate-600">{area.postal_codes.join(", ")}</dd></div> : null}
            </dl>
          </div>
          <div>
            <SectionHeading eyebrow="Liaisons" title="Aéroports actuellement reliés" description="L’affichage dépend des tarifs actifs, sans liste d’aéroports intégrée au code." />
            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              {airports.map((airport) => {
                const directions = routes.filter((route) => route.airport_id === airport.public_id).map((route) => route.trip_type);
                return (
                  <article key={airport.public_id} className="surface-card p-6">
                    <div className="flex items-center justify-between gap-4"><Icon name="plane" className="size-6 text-blue-700" /><span className="text-sm font-black tracking-wider text-slate-500">{airport.iata_code}</span></div>
                    <h2 className="mt-4 font-extrabold text-slate-950">{airport.name}</h2>
                    <p className="mt-2 text-xs leading-5 text-slate-500">
                      {directions.includes("airport_pickup") ? "Aéroport → zone" : ""}
                      {directions.length === 2 ? " · " : ""}
                      {directions.includes("airport_dropoff") ? "Zone → aéroport" : ""}
                    </p>
                    <Link href={`/aeroports/${airport.slug}`} className="mt-4 inline-flex items-center gap-2 text-sm font-bold text-blue-700 hover:underline">Voir l’aéroport <Icon name="arrow" className="size-4" /></Link>
                  </article>
                );
              })}
            </div>
            <Link href="/tarifs" className="button button-primary mt-8">Estimer ce trajet <Icon name="arrow" className="size-4" /></Link>
          </div>
        </div>
      </section>
      <ContactCta settings={settings} title={`Un trajet vers ${area.name} à vérifier ?`} />
    </main>
  );
}
