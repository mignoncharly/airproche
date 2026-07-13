import type { Metadata } from "next";

import { ContactMethods } from "@/components/contact-methods";
import { Icon } from "@/components/icon";
import { PageHero, SectionHeading } from "@/components/marketing";
import { ContactForm } from "@/features/contact/contact-form";
import { getPublicContent } from "@/lib/public-content";
import { publicMetadata } from "@/lib/seo";

export const metadata: Metadata = publicMetadata("Contact", "Coordonnées officielles et informations à préparer pour une demande de transport.", "/contact");

export default async function ContactPage() {
  const { settings } = await getPublicContent();
  return (
    <main>
      <PageHero eyebrow="Contact" title="Parlez-nous du trajet que vous préparez" description="Utilisez le formulaire sécurisé ou les coordonnées officielles publiées ci-dessous." />
      <section className="site-container py-16 sm:py-24">
        <ContactMethods settings={settings} />
        <div className="mt-16 grid gap-12 lg:grid-cols-2">
          <SectionHeading eyebrow="À préparer" title="Les informations qui nous aident à répondre" description="Ne transmettez jamais de numéro de carte bancaire, de mot de passe ou de document d’identité par téléphone, e-mail ou messagerie." />
          <ul className="grid gap-3">{["Aéroport ou lieu de prise en charge", "Destination prévue", "Date et horaire approximatif", "Nombre de passagers et de bagages", "Numéro de vol si applicable", "Besoin d’assistance à signaler"].map((item) => <li key={item} className="flex items-center gap-3 rounded-xl bg-slate-50 p-4 text-sm font-semibold text-slate-700"><Icon name="check" className="size-5 shrink-0 text-blue-700" />{item}</li>)}</ul>
        </div>
        {settings.support_hours ? <p className="mt-10 rounded-xl border border-blue-100 bg-blue-50 p-4 text-sm font-semibold text-blue-950">Horaires de contact : {settings.support_hours}</p> : null}
        <ContactForm />
      </section>
    </main>
  );
}
