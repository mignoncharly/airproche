import Link from "next/link";

import { primaryNavigation } from "@/lib/marketing-data";
import type { BusinessSettings } from "@/lib/public-content";

import { Brand } from "./brand";
import { Icon } from "./icon";

export function SiteHeader({ settings }: { settings: BusinessSettings }) {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/95 backdrop-blur">
      <div className="site-container flex h-18 items-center justify-between gap-6">
        <Brand name={settings.business_name} />
        <nav aria-label="Navigation principale" className="hidden items-center gap-7 lg:flex">
          {primaryNavigation.map((item) => (
            <Link key={item.href} href={item.href} className="nav-link">{item.label}</Link>
          ))}
        </nav>
        <div className="hidden items-center gap-3 lg:flex">
          <Link href="/connexion" className="button button-secondary">Espace client</Link>
          <Link href="/contact" className="button button-primary">Nous contacter <Icon name="arrow" className="size-4" /></Link>
        </div>
        <details className="group relative lg:hidden">
          <summary className="grid size-11 cursor-pointer list-none place-items-center rounded-xl border border-slate-300 text-slate-950 marker:content-none" aria-label="Ouvrir le menu">
            <span className="flex w-5 flex-col gap-1.5" aria-hidden="true"><span className="h-0.5 bg-current" /><span className="h-0.5 bg-current" /><span className="h-0.5 bg-current" /></span>
          </summary>
          <div className="absolute right-0 top-14 w-[min(21rem,calc(100vw-2rem))] rounded-2xl border border-slate-200 bg-white p-3 shadow-xl">
            <nav aria-label="Navigation mobile" className="flex flex-col">
              {primaryNavigation.map((item) => (
                <Link key={item.href} href={item.href} className="rounded-xl px-4 py-3 font-semibold text-slate-800 hover:bg-slate-100">{item.label}</Link>
              ))}
              <Link href="/faq" className="rounded-xl px-4 py-3 font-semibold text-slate-800 hover:bg-slate-100">Questions fréquentes</Link>
              <Link href="/connexion" className="rounded-xl px-4 py-3 font-semibold text-slate-800 hover:bg-slate-100">Espace client</Link>
              <Link href="/contact" className="button button-primary mt-2">Nous contacter</Link>
            </nav>
          </div>
        </details>
      </div>
    </header>
  );
}
