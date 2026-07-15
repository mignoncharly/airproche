import type { Metadata } from "next";

import { Icon } from "@/components/icon";
import { ContactCta, PageHero } from "@/components/marketing";
import { processSteps } from "@/lib/marketing-data";
import { getPublicContent } from "@/lib/public-content";
import { publicMetadata } from "@/lib/seo";

export const metadata: Metadata = publicMetadata("Comment ça marche", "Les étapes prévues entre la préparation de la demande et l’arrivée à destination.", "/fonctionnement");

export default async function HowItWorksPage() {
  const { settings } = await getPublicContent();
  return (
    <main>
      <PageHero eyebrow="Fonctionnement" title="Vous savez quoi transmettre, quoi attendre et qui contacter" description="AirProche vous aide à trouver un chauffeur. Celui-ci confirme directement le prix, la disponibilité et le trajet." />
      <section className="site-container py-16 sm:py-24">
        <ol className="grid gap-8">
          {processSteps.map((step, index) => <li key={step.number} className="grid gap-5 border-b border-slate-200 pb-8 sm:grid-cols-[7rem_1fr] sm:pb-10"><span className="text-5xl font-black tracking-[-0.06em] text-blue-200">{step.number}</span><div><h2 className="text-2xl font-black tracking-tight text-slate-950">{step.title}</h2><p className="mt-3 max-w-2xl leading-7 text-slate-600">{step.description}</p>{index === 0 ? <p className="mt-4 flex gap-2 text-sm text-slate-500"><Icon name="check" className="size-5 shrink-0 text-emerald-600" />La demande ne constitue pas une reservation. Attendez la confirmation directe du chauffeur.</p> : null}</div></li>)}
        </ol>
      </section>
      <section className="border-y border-slate-200 bg-slate-50 py-16 sm:py-24"><div className="site-container grid gap-6 md:grid-cols-3">{[{ title: "Avant de vous engager", text: "Le chauffeur récapitule le trajet, son prix et ses conditions." }, { title: "Paiement direct", text: "Le paiement est organisé directement avec le chauffeur ; AirProche ne l’encaisse pas." }, { title: "Avant le trajet", text: "Le chauffeur confirme directement les consignes de prise en charge et les détails utiles." }].map((item) => <article key={item.title} className="surface-card p-7"><h2 className="font-extrabold text-slate-950">{item.title}</h2><p className="mt-3 text-sm leading-6 text-slate-600">{item.text}</p></article>)}</div></section>
      <ContactCta settings={settings} />
    </main>
  );
}
