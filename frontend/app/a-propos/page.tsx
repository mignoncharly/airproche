import type { Metadata } from "next";

import { Icon } from "@/components/icon";
import { ContactCta, PageHero, SectionHeading } from "@/components/marketing";
import { trustPoints } from "@/lib/marketing-data";
import { getPublicContent } from "@/lib/public-content";

export const metadata: Metadata = { title: "À propos", description: "La vision du service : un accueil privé fiable, humain et clairement organisé." };

export default async function AboutPage() {
  const { settings } = await getPublicContent();
  return (
    <main>
      <PageHero eyebrow="À propos" title="Faire baisser l’incertitude avant même le trajet" description="Le service est conçu pour les voyageurs comme pour les proches qui organisent leur arrivée à distance." />
      <section className="site-container py-16 sm:py-24">
        <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
          <SectionHeading eyebrow="Notre approche" title="Le professionnalisme se voit dans les détails" description="Une heure, un point de rencontre, une destination et un moyen de contact clairement établis : ce sont ces informations simples qui rendent une arrivée plus sereine." />
          <div className="rounded-[2rem] bg-blue-50 p-8 sm:p-10"><Icon name="shield" className="size-10 text-blue-700" /><p className="mt-7 text-2xl font-black tracking-tight text-slate-950">La confiance ne repose pas sur une promesse vague.</p><p className="mt-4 leading-7 text-slate-600">Elle repose sur une tarification compréhensible, un paiement vérifié, des consignes utiles et un interlocuteur identifiable.</p></div>
        </div>
        <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{trustPoints.map((point) => <article key={point.title} className="surface-card p-6"><Icon name={point.icon} className="size-7 text-blue-700" /><h2 className="mt-5 font-extrabold text-slate-950">{point.title}</h2><p className="mt-2 text-sm leading-6 text-slate-600">{point.description}</p></article>)}</div>
      </section>
      <section className="border-y border-slate-200 bg-slate-50 py-16 sm:py-24"><div className="site-container max-w-3xl"><SectionHeading eyebrow="Transparence" title="Ce que nous ne prétendons pas encore proposer" description="Le lancement ne présente ni suivi de vol en direct, ni affectation automatique, ni notification WhatsApp automatisée. Ces fonctions ne seront annoncées qu’après intégration et validation réelles." /></div></section>
      <ContactCta settings={settings} />
    </main>
  );
}
