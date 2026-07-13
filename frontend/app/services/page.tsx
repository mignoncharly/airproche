import type { Metadata } from "next";

import { Icon } from "@/components/icon";
import { ContactCta, PageHero, SectionHeading } from "@/components/marketing";
import { serviceHighlights } from "@/lib/marketing-data";
import { getPublicContent } from "@/lib/public-content";

export const metadata: Metadata = { title: "Services", description: "Accueil aéroport, aide aux bagages et transport privé vers la destination prévue." };

const additionalServices = [
  { icon: "hotel" as const, title: "Hôtels et hébergements", description: "Une dépose à l’adresse indiquée, avec les informations utiles préparées avant le départ." },
  { icon: "route" as const, title: "Trajets longue distance", description: "Les demandes hors zone habituelle sont étudiées avant toute confirmation de prix ou de disponibilité." },
  { icon: "car" as const, title: "Départ vers l’aéroport", description: "Une prise en charge depuis le domicile ou l’hébergement pour rejoindre le terminal prévu." },
] as const;

export default async function ServicesPage() {
  const content = await getPublicContent();
  const managed = content.services;
  const services = managed.length ? managed : [...serviceHighlights, ...additionalServices];
  return (
    <main>
      <PageHero eyebrow="Nos services" title="Un transport privé préparé, de la prise en charge à l’arrivée" description="Chaque demande est organisée autour du trajet, du passager et des besoins déclarés à l’avance." />
      <section className="site-container py-16 sm:py-24">
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {services.map((service) => (
            <article key={"slug" in service ? service.slug : service.title} className="surface-card p-7">
              <span className="grid size-12 place-items-center rounded-2xl bg-blue-50 text-blue-700"><Icon name={service.icon} className="size-6" /></span>
              <h2 className="mt-5 text-xl font-extrabold tracking-tight text-slate-950">{service.title}</h2>
              <p className="mt-3 leading-7 text-slate-600">{"summary" in service ? service.summary : service.description}</p>
              {"description" in service && "summary" in service && service.description ? <p className="mt-3 text-sm leading-6 text-slate-500">{service.description}</p> : null}
            </article>
          ))}
        </div>
      </section>
      <section className="border-y border-slate-200 bg-slate-50 py-16 sm:py-24">
        <div className="site-container grid gap-12 lg:grid-cols-2">
          <SectionHeading eyebrow="Avant confirmation" title="Les besoins sont vérifiés, pas supposés" description="Le nombre de voyageurs, les bagages, les sièges enfant et toute demande d’assistance doivent être déclarés. Une option n’est jamais présentée comme disponible sans validation opérationnelle." />
          <ul className="grid gap-4 sm:grid-cols-2">
            {["Nombre de passagers", "Bagages et objets volumineux", "Siège enfant", "Demande d’assistance", "Informations de vol", "Coordonnées du passager"].map((item) => <li key={item} className="flex items-center gap-3 rounded-xl bg-white p-4 text-sm font-bold text-slate-800 shadow-sm"><Icon name="check" className="size-5 shrink-0 text-emerald-600" />{item}</li>)}
          </ul>
        </div>
      </section>
      <ContactCta settings={content.settings} />
    </main>
  );
}
