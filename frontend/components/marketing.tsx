import Link from "next/link";
import type { ReactNode } from "react";

import type { BusinessSettings } from "@/lib/public-content";

import { Icon } from "./icon";

export function Eyebrow({ children }: { children: ReactNode }) {
  return <p className="eyebrow">{children}</p>;
}

export function PageHero({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return (
    <section className="page-hero">
      <div className="site-container max-w-4xl py-16 sm:py-22">
        <Eyebrow>{eyebrow}</Eyebrow>
        <h1 className="mt-5 text-balance text-4xl font-black tracking-[-0.045em] text-slate-950 sm:text-6xl">{title}</h1>
        <p className="mt-6 max-w-2xl text-pretty text-lg leading-8 text-slate-600">{description}</p>
      </div>
    </section>
  );
}

export function SectionHeading({ eyebrow, title, description, centered = false, inverted = false }: { eyebrow: string; title: string; description?: string; centered?: boolean; inverted?: boolean }) {
  return (
    <div className={centered ? "mx-auto max-w-2xl text-center" : "max-w-2xl"}>
      <Eyebrow>{eyebrow}</Eyebrow>
      <h2 className={`mt-4 text-balance text-3xl font-black tracking-[-0.035em] sm:text-4xl ${inverted ? "text-white" : "text-slate-950"}`}>{title}</h2>
      {description ? <p className={`mt-5 text-pretty leading-7 ${inverted ? "text-slate-300" : "text-slate-600"}`}>{description}</p> : null}
    </div>
  );
}

export function ContactCta({ settings, title = "Préparons votre prochain trajet" }: { settings: BusinessSettings; title?: string }) {
  const hasPublishedContact = Boolean(
    settings.phone || settings.email || settings.whatsapp_phone,
  );
  return (
    <section className="site-container py-16 sm:py-24">
      <div className="overflow-hidden rounded-[2rem] bg-[#10213f] px-6 py-10 text-white shadow-xl sm:px-12 sm:py-14 lg:flex lg:items-center lg:justify-between lg:gap-10">
        <div className="max-w-2xl">
          <p className="text-sm font-bold uppercase tracking-[0.16em] text-blue-300">Un besoin particulier ?</p>
          <h2 className="mt-3 text-3xl font-black tracking-[-0.035em] sm:text-4xl">{title}</h2>
          <p className="mt-4 max-w-xl leading-7 text-slate-300">Expliquez-nous le trajet et les besoins du passager. Nous vous indiquerons les prochaines étapes.</p>
        </div>
        <div className="mt-8 flex flex-wrap gap-3 lg:mt-0 lg:shrink-0">
          <Link href="/contact" className="button bg-white text-slate-950 hover:bg-blue-50">{hasPublishedContact ? "Voir les contacts" : "Disponibilité du service"} <Icon name="arrow" className="size-4" /></Link>
          <Link href="/chauffeurs" className="button border border-white/25 text-white hover:bg-white/10">Voir les chauffeurs</Link>
        </div>
      </div>
    </section>
  );
}

export function EmptyNotice({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6">
      <h2 className="font-bold text-slate-950">{title}</h2>
      <div className="mt-2 text-sm leading-6 text-slate-600">{children}</div>
    </div>
  );
}
