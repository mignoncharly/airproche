import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Icon } from "@/components/icon";
import { ContactCta, EmptyNotice, PageHero, SectionHeading } from "@/components/marketing";
import { getAirport, getLocationsAndCoverage } from "@/lib/locations-pricing";
import { getPublicContent } from "@/lib/public-content";

type PageProps = { params: Promise<{ slug: string }> };

export async function generateStaticParams() {
  const data = await getLocationsAndCoverage();
  const covered = new Set(data.coverage.routes.map((route) => route.airport_id));
  return data.airports.filter((airport) => covered.has(airport.public_id)).map((airport) => ({ slug: airport.slug }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const airport = await getAirport(slug);
  if (!airport) return { title: "Aéroport indisponible" };
  return {
    title: airport.seo_title || `Transferts privés — ${airport.name}`,
    description:
      airport.seo_description ||
      `Consultez les zones et trajets tarifés actuellement disponibles pour ${airport.name}.`,
  };
}

export default async function AirportPage({ params }: PageProps) {
  const { slug } = await params;
  const [airport, data, { settings }] = await Promise.all([
    getAirport(slug),
    getLocationsAndCoverage(),
    getPublicContent(),
  ]);
  if (!airport) notFound();
  const routes = data.coverage.routes.filter((route) => route.airport_id === airport.public_id);
  if (!routes.length) notFound();
  const areaIds = new Set(routes.map((route) => route.service_area_id));
  const areas = data.serviceAreas.filter((area) => areaIds.has(area.public_id));

  return (
    <main>
      <PageHero
        eyebrow={`${airport.iata_code} · ${airport.city}`}
        title={`Transferts privés pour ${airport.name}`}
        description={airport.description || "Consultez les zones actuellement couvertes et obtenez une estimation calculée par le serveur."}
      />
      <section className="site-container py-16 sm:py-24">
        <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <SectionHeading eyebrow="Informations" title="Préparer le point de rencontre" />
            <dl className="mt-7 grid gap-4 text-sm">
              <div className="rounded-xl border border-slate-200 p-4"><dt className="font-bold text-slate-950">Adresse</dt><dd className="mt-1 text-slate-600">{airport.address}</dd></div>
              <div className="rounded-xl border border-slate-200 p-4"><dt className="font-bold text-slate-950">Fuseau horaire</dt><dd className="mt-1 text-slate-600">{airport.timezone}</dd></div>
            </dl>
            {airport.terminal_guidance ? (
              <div className="mt-5 rounded-xl bg-blue-50 p-5">
                <h2 className="font-extrabold text-slate-950">Consignes publiées</h2>
                <p className="mt-2 whitespace-pre-line text-sm leading-6 text-slate-700">{airport.terminal_guidance}</p>
              </div>
            ) : null}
          </div>
          <div>
            <SectionHeading eyebrow="Trajets actifs" title="Zones disponibles" description="Le sens exact disponible est indiqué pour chaque zone et vérifié de nouveau à la date choisie." />
            {areas.length ? (
              <div className="mt-8 grid gap-4 sm:grid-cols-2">
                {areas.map((area) => {
                  const directions = routes.filter((route) => route.service_area_id === area.public_id).map((route) => route.trip_type);
                  return (
                    <article key={area.public_id} className="surface-card p-6">
                      <Icon name="route" className="size-6 text-blue-700" />
                      <h2 className="mt-4 font-extrabold text-slate-950">{area.name}</h2>
                      <p className="mt-2 text-xs leading-5 text-slate-500">
                        {directions.includes("airport_pickup") ? "Aéroport → zone" : ""}
                        {directions.length === 2 ? " · " : ""}
                        {directions.includes("airport_dropoff") ? "Zone → aéroport" : ""}
                      </p>
                      <Link href={`/zones-desservies/${area.slug}`} className="mt-4 inline-flex items-center gap-2 text-sm font-bold text-blue-700 hover:underline">Détails <Icon name="arrow" className="size-4" /></Link>
                    </article>
                  );
                })}
              </div>
            ) : <EmptyNotice title="Aucune zone publiée"><p>La couverture n’est pas disponible actuellement.</p></EmptyNotice>}
            <Link href="/tarifs" className="button button-primary mt-8">Obtenir une estimation <Icon name="arrow" className="size-4" /></Link>
          </div>
        </div>
      </section>
      <ContactCta settings={settings} title={`Une prise en charge à ${airport.iata_code} à organiser ?`} />
    </main>
  );
}
