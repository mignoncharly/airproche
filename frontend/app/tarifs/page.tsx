import type { Metadata } from "next";

import { QuoteEstimator } from "@/components/quote-estimator";
import { ContactCta, EmptyNotice, PageHero, SectionHeading } from "@/components/marketing";
import { getLocationsAndCoverage } from "@/lib/locations-pricing";
import { getPublicContent } from "@/lib/public-content";
import { publicMetadata } from "@/lib/seo";

export const metadata: Metadata = publicMetadata(
  "Tarifs et estimation",
  "Obtenez une estimation serveur pour un transfert privé entre un aéroport et une zone active.",
  "/tarifs",
);

export default async function PricingPage() {
  const [{ settings }, locationData] = await Promise.all([
    getPublicContent(),
    getLocationsAndCoverage(),
  ]);
  const canEstimate = locationData.coverage.routes.length > 0;

  return (
    <main>
      <PageHero
        eyebrow="Tarification"
        title="Un prix clair avant vos coordonnées"
        description="Le serveur sélectionne le tarif actif entre l’aéroport et la zone, puis détaille chaque option applicable."
      />
      <section className="site-container py-16 sm:py-24">
        {canEstimate ? (
          <QuoteEstimator
            airports={locationData.airports}
            serviceAreas={locationData.serviceAreas}
            routes={locationData.coverage.routes}
            minimumLeadHours={settings.minimum_lead_hours}
            maximumBookingDays={settings.maximum_booking_days}
          />
        ) : (
          <EmptyNotice title="Estimations en ligne non ouvertes">
            <p>Aucun trajet complet n’est actuellement publié. Une estimation apparaîtra ici dès qu’un aéroport, une zone et leur tarif auront été activés.</p>
          </EmptyNotice>
        )}

        <div className="mt-16 grid gap-12 lg:grid-cols-[0.9fr_1.1fr]">
          <SectionHeading
            eyebrow="Calcul"
            title="Une règle fixe et reproductible"
            description="Le navigateur transmet uniquement le trajet, la date, les capacités et les options. Il ne peut jamais fixer le montant."
          />
          <div className="grid gap-4 sm:grid-cols-2">
            {[
              ["Trajet couvert", "Un tarif fixe relie un aéroport et une zone active."],
              ["Capacité vérifiée", "Passagers et bagages restent dans les limites configurées."],
              ["Options explicites", "Chaque supplément apparaît sur une ligne séparée."],
              ["Durée limitée", "L’estimation expire et sera revérifiée avant réservation."],
            ].map(([title, text]) => (
              <article key={title} className="rounded-xl border border-slate-200 bg-white p-5">
                <h2 className="text-sm font-extrabold text-slate-950">{title}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">{text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
      <ContactCta settings={settings} title="Votre trajet demande une vérification particulière ?" />
    </main>
  );
}
