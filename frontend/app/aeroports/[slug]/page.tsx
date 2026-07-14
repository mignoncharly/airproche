import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Icon } from "@/components/icon";
import { ContactCta, EmptyNotice, PageHero, SectionHeading } from "@/components/marketing";
import { StructuredData } from "@/components/structured-data";
import { getAirport, getLocationsAndCoverage } from "@/lib/locations-pricing";
import { getDrivers } from "@/lib/marketplace";
import { getPublicContent } from "@/lib/public-content";
import { airportStructuredData, publicMetadata } from "@/lib/seo";

type PageProps = { params: Promise<{ slug: string }> };

export async function generateStaticParams() {
  const data = await getLocationsAndCoverage();
  return data.airports.map((airport) => ({ slug: airport.slug }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const airport = await getAirport(slug);
  if (!airport) {
    return { title: "Aéroport indisponible", robots: { index: false, follow: false } };
  }
  return publicMetadata(
    airport.seo_title || `Transferts privés — ${airport.name}`,
    airport.seo_description ||
      `Consultez les informations utiles et trouvez un chauffeur indépendant pour ${airport.name}.`,
    `/aeroports/${airport.slug}`,
  );
}

export default async function AirportPage({ params }: PageProps) {
  const { slug } = await params;
  const [airport, allDrivers, { settings }] = await Promise.all([
    getAirport(slug),
    getDrivers(),
    getPublicContent(),
  ]);
  if (!airport) notFound();
  const drivers = allDrivers.filter((driver) =>
    driver.airports.some((servedAirport) => servedAirport.public_id === airport.public_id),
  );

  return (
    <main>
      <StructuredData data={airportStructuredData(airport)} />
      <PageHero
        eyebrow={`${airport.iata_code} · ${airport.city}`}
        title={`Transferts privés pour ${airport.name}`}
        description={airport.description || "Consultez les informations utiles et trouvez un chauffeur indépendant pour cet aéroport."}
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
            <SectionHeading eyebrow="Chauffeurs indépendants" title="Profils desservant cet aéroport" description="Chaque chauffeur confirme directement sa disponibilité, son prix, ses conditions et le point de rencontre." />
            {drivers.length ? (
              <div className="mt-8 grid gap-4 sm:grid-cols-2">
                {drivers.map((driver) => (
                  <article key={driver.public_id} className="surface-card p-6">
                    <p className="text-xs font-bold uppercase tracking-wider text-blue-700">Profil vérifié</p>
                    <h2 className="mt-3 text-xl font-black text-slate-950">{driver.display_name}</h2>
                    <p className="mt-2 text-sm text-slate-600">{driver.business_name || "Chauffeur indépendant"}</p>
                    <Link href={`/chauffeurs/${driver.public_id}`} className="mt-5 inline-flex items-center gap-2 text-sm font-bold text-blue-700 hover:underline">Voir et contacter <Icon name="arrow" className="size-4" /></Link>
                  </article>
                ))}
              </div>
            ) : <EmptyNotice title="Aucun chauffeur publié"><p>Les profils apparaîtront ici après vérification et déclaration de cet aéroport dans leur couverture.</p></EmptyNotice>}
            <Link href="/chauffeurs" className="button button-primary mt-8">Voir tout l’annuaire <Icon name="arrow" className="size-4" /></Link>
          </div>
        </div>
      </section>
      <ContactCta settings={settings} title={`Une prise en charge à ${airport.iata_code} à organiser ?`} />
    </main>
  );
}
