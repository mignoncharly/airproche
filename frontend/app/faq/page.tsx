import type { Metadata } from "next";

import { EmptyNotice, PageHero } from "@/components/marketing";
import { getPublicContent } from "@/lib/public-content";
import { publicMetadata } from "@/lib/seo";

export const metadata: Metadata = publicMetadata("Questions fréquentes", "Réponses publiées sur la réservation, la prise en charge et le transport privé.", "/faq");

export default async function FAQPage() {
  const { faqs } = await getPublicContent();
  return (
    <main>
      <PageHero eyebrow="Questions fréquentes" title="Les réponses utiles, sans petite ligne cachée" description="Les réponses opérationnelles sont publiées et mises à jour par l’équipe depuis le système de contenu." />
      <section className="site-container max-w-4xl py-16 sm:py-24">
        {faqs.length ? <div className="divide-y divide-slate-200 border-y border-slate-200">{faqs.map((faq) => <details key={faq.public_id} className="group py-6"><summary className="flex cursor-pointer list-none items-center justify-between gap-5 text-lg font-extrabold text-slate-950 marker:content-none">{faq.question}<span className="text-3xl font-light text-blue-700 transition-transform group-open:rotate-45" aria-hidden="true">+</span></summary><p className="max-w-3xl pr-12 pt-4 leading-7 text-slate-600">{faq.answer}</p></details>)}</div> : <EmptyNotice title="Aucune réponse publiée"><p>La FAQ opérationnelle est encore en préparation. Nous ne publions pas de réponses génériques qui pourraient être inexactes pour votre trajet.</p></EmptyNotice>}
      </section>
    </main>
  );
}
