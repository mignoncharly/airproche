import Image from "next/image";
import Link from "next/link";

import { Icon } from "@/components/icon";
import { ContactCta, Eyebrow, SectionHeading } from "@/components/marketing";
import { StructuredData } from "@/components/structured-data";
import { processSteps, serviceHighlights, trustPoints } from "@/lib/marketing-data";
import { getLocationsAndCoverage } from "@/lib/locations-pricing";
import { getPublicContent } from "@/lib/public-content";
import { businessStructuredData, publicMetadata } from "@/lib/seo";

export const metadata = publicMetadata(
  "Transport privé depuis les aéroports",
  "Préparez l’accueil et le transport privé d’un proche ou de votre groupe avec des étapes claires.",
  "/",
);

export default async function HomePage() {
  const [content, locationData] = await Promise.all([
    getPublicContent(),
    getLocationsAndCoverage(),
  ]);
  const estimationAvailable = locationData.coverage.routes.length > 0;
  const services = content.services.length ? content.services : serviceHighlights;
  const structuredData = businessStructuredData(content.settings, content.services);

  return (
    <main>
      <StructuredData data={structuredData} />
      <section className="relative overflow-hidden bg-[#f7faff]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(147,197,253,0.34),transparent_30rem)]" aria-hidden="true" />
        <div className="site-container relative grid items-center gap-12 py-16 sm:py-24 lg:grid-cols-[1.03fr_0.97fr] lg:py-28">
          <div className="max-w-2xl">
            <Eyebrow>Accueil aéroport · Transport privé</Eyebrow>
            <h1 className="mt-6 text-balance text-5xl font-black leading-[1.02] tracking-[-0.055em] text-slate-950 sm:text-6xl lg:text-7xl">Le trajet commence par un accueil rassurant.</h1>
            <p className="mt-6 max-w-xl text-pretty text-lg leading-8 text-slate-600">Organisez le transport d’un proche, d’un ami ou de votre groupe depuis l’aéroport jusqu’à sa destination, avec des informations claires à chaque étape.</p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Link href={estimationAvailable ? "/tarifs" : "/services"} className="button button-primary px-5">{estimationAvailable ? "Obtenir une estimation" : "Découvrir les services"} <Icon name="arrow" className="size-4" /></Link>
              <Link href="/fonctionnement" className="button button-secondary px-5">Comment ça marche</Link>
            </div>
            <p className="mt-6 flex items-start gap-2 text-sm leading-6 text-slate-600"><Icon name="check" className="mt-0.5 size-5 shrink-0 text-blue-700" />{estimationAvailable ? "Le prix est calculé par le serveur avant toute collecte de coordonnées." : "Les réservations en ligne seront affichées uniquement lorsqu’elles seront réellement ouvertes."}</p>
          </div>
          <div className="relative mx-auto w-full max-w-[34rem]">
            <div className="relative aspect-[4/3] overflow-hidden rounded-[2rem] bg-[#10213f] shadow-2xl">
              <Image src="/images/airport-transfer-hero.png" alt="Un chauffeur range les bagages d’une passagère dans un véhicule privé devant un aéroport" fill priority sizes="(min-width: 1024px) 46vw, 90vw" className="object-cover object-center" />
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/90 via-slate-950/45 to-transparent p-7 pt-24 text-white sm:p-9 sm:pt-28">
                <p className="text-sm font-semibold text-blue-200">Aéroport → destination</p>
                <p className="mt-2 max-w-md text-2xl font-bold tracking-tight">Un point de rencontre clair, un trajet préparé.</p>
              </div>
              <span className="absolute left-6 top-6 rounded-full border border-white/20 bg-slate-950/60 px-3 py-1.5 text-xs font-bold uppercase tracking-[0.13em] text-white backdrop-blur">Prise en charge privée</span>
            </div>
            <div className="absolute -bottom-5 -left-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-xl sm:-left-8">
              <div className="flex items-center gap-3"><span className="grid size-10 place-items-center rounded-xl bg-blue-50 text-blue-700"><Icon name="message" className="size-5" /></span><div><p className="text-xs font-semibold text-slate-500">Avant l’arrivée</p><p className="text-sm font-bold text-slate-950">Consignes confirmées</p></div></div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-slate-200 bg-white">
        <div className="site-container grid grid-cols-2 gap-px py-3 md:grid-cols-4">
          {trustPoints.map((point) => <div key={point.title} className="flex items-center gap-3 px-3 py-4 sm:px-5"><Icon name={point.icon} className="size-5 shrink-0 text-blue-700" /><span className="text-sm font-bold text-slate-800">{point.title}</span></div>)}
        </div>
      </section>

      <section className="site-container py-20 sm:py-28">
        <SectionHeading eyebrow="Services" title="Une prise en charge pensée autour du passager" description="De l’arrivée à la destination finale, chaque information utile est préparée en amont." />
        <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          {services.slice(0, 4).map((service) => (
            <article key={"slug" in service ? service.slug : service.title} className="surface-card p-6 transition-transform hover:-translate-y-1">
              <span className="grid size-12 place-items-center rounded-2xl bg-blue-50 text-blue-700"><Icon name={service.icon} className="size-6" /></span>
              <h3 className="mt-5 text-lg font-extrabold tracking-tight text-slate-950">{service.title}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{"summary" in service ? service.summary : service.description}</p>
            </article>
          ))}
        </div>
        <Link href="/services" className="mt-8 inline-flex items-center gap-2 text-sm font-bold text-blue-700 hover:underline">Voir tous les services <Icon name="arrow" className="size-4" /></Link>
      </section>

      <section className="bg-slate-950 py-20 text-white sm:py-28">
        <div className="site-container">
          <SectionHeading centered inverted eyebrow="Fonctionnement" title="Quatre étapes, sans zone d’ombre" description="Le parcours est conçu pour rassurer la personne qui réserve comme celle qui voyage." />
          <ol className="mt-14 grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            {processSteps.map((step) => <li key={step.number} className="border-t border-white/20 pt-6"><span className="text-sm font-black text-blue-300">{step.number}</span><h3 className="mt-4 text-xl font-extrabold">{step.title}</h3><p className="mt-3 text-sm leading-6 text-slate-400">{step.description}</p></li>)}
          </ol>
        </div>
      </section>

      <section className="site-container py-20 sm:py-28">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <div className="rounded-[2rem] bg-blue-50 p-8 sm:p-10">
            <Icon name="users" className="size-10 text-blue-700" />
            <p className="mt-8 text-2xl font-black tracking-tight text-slate-950 sm:text-3xl">Vous organisez le trajet pour quelqu’un d’autre ?</p>
            <p className="mt-4 leading-7 text-slate-600">Le parcours de réservation distinguera les coordonnées de la personne qui organise et celles du passager. Chacun recevra uniquement les informations qui le concernent.</p>
          </div>
          <div>
            <SectionHeading eyebrow="Pour vos proches" title="Moins d’incertitude, même à distance" description="Vous savez ce qui est prévu, le passager sait où se rendre, et les besoins particuliers sont signalés avant le trajet." />
            <ul className="mt-7 grid gap-4">
              {["Coordonnées séparées pour l’organisateur et le passager", "Informations de vol et terminal enregistrées", "Bagages et demandes d’assistance déclarés", "Consignes de rencontre communiquées avant l’arrivée"].map((item) => <li key={item} className="flex gap-3 text-sm font-semibold text-slate-700"><span className="grid size-6 shrink-0 place-items-center rounded-full bg-emerald-100 text-emerald-700"><Icon name="check" className="size-4" /></span>{item}</li>)}
            </ul>
          </div>
        </div>
      </section>

      {content.testimonials.length ? (
        <section className="border-y border-slate-200 bg-slate-50 py-20 sm:py-24">
          <div className="site-container"><SectionHeading eyebrow="Avis vérifiés" title="Ce que disent nos passagers" /><div className="mt-10 grid gap-5 md:grid-cols-3">{content.testimonials.slice(0, 3).map((item) => <figure key={item.public_id} className="surface-card p-6"><div className="text-sm tracking-wider text-amber-500" aria-label={`${item.rating} étoiles sur 5`}>{"★".repeat(item.rating)}</div><blockquote className="mt-4 leading-7 text-slate-700">“{item.quote}”</blockquote><figcaption className="mt-5 text-sm font-bold text-slate-950">{item.author_name}{item.author_context ? <span className="block font-normal text-slate-500">{item.author_context}</span> : null}</figcaption></figure>)}</div></div>
        </section>
      ) : null}

      {content.faqs.length ? (
        <section className="site-container py-20 sm:py-28"><SectionHeading eyebrow="Questions fréquentes" title="Des réponses avant de partir" /><div className="mt-10 max-w-3xl divide-y divide-slate-200 border-y border-slate-200">{content.faqs.slice(0, 5).map((faq) => <details key={faq.public_id} className="group py-5"><summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-bold text-slate-950 marker:content-none">{faq.question}<span className="text-2xl font-light text-blue-700 transition-transform group-open:rotate-45" aria-hidden="true">+</span></summary><p className="pr-10 pt-3 leading-7 text-slate-600">{faq.answer}</p></details>)}</div><Link href="/faq" className="mt-7 inline-flex items-center gap-2 text-sm font-bold text-blue-700 hover:underline">Toutes les questions <Icon name="arrow" className="size-4" /></Link></section>
      ) : null}

      <ContactCta settings={content.settings} />
    </main>
  );
}
