import Link from "next/link";

import { primaryNavigation } from "@/lib/marketing-data";
import { type BusinessSettings, phoneHref, whatsappHref } from "@/lib/public-content";

import { Brand } from "./brand";

const legalLinks = [
  { href: "/confidentialite", label: "Confidentialité" },
  { href: "/conditions-generales", label: "Conditions générales" },
  { href: "/annulation", label: "Annulation" },
  { href: "/mentions-legales", label: "Mentions légales" },
  { href: "/cookies", label: "Cookies" },
  { href: "/transparence", label: "Transparence" },
] as const;

export function SiteFooter({ settings }: { settings: BusinessSettings }) {
  const hasContact = Boolean(settings.phone || settings.email || settings.whatsapp_phone);
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="site-container grid gap-10 py-14 md:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr]">
        <div className="max-w-sm">
          <Brand name={settings.business_name} />
          <p className="mt-5 text-sm leading-6 text-slate-600">{settings.tagline}</p>
          {settings.support_hours ? <p className="mt-3 text-sm font-semibold text-slate-800">{settings.support_hours}</p> : null}
        </div>
        <div>
          <h2 className="footer-title">Explorer</h2>
          <ul className="mt-4 grid gap-2 text-sm text-slate-600">
            {primaryNavigation.slice(0, 4).map((item) => <li key={item.href}><Link className="footer-link" href={item.href}>{item.label}</Link></li>)}
            <li><Link className="footer-link" href="/zones-desservies">Zones desservies</Link></li>
            <li><Link className="footer-link" href="/faq">Questions fréquentes</Link></li>
            <li><Link className="footer-link" href="/connexion">Espace client</Link></li>
          </ul>
        </div>
        <div>
          <h2 className="footer-title">Contact</h2>
          {hasContact ? (
            <ul className="mt-4 grid gap-2 text-sm text-slate-600">
              {settings.phone ? <li><a className="footer-link" href={phoneHref(settings.phone)}>{settings.phone}</a></li> : null}
              {settings.email ? <li><a className="footer-link break-all" href={`mailto:${settings.email}`}>{settings.email}</a></li> : null}
              {settings.whatsapp_phone ? <li><a className="footer-link" href={whatsappHref(settings.whatsapp_phone)} target="_blank" rel="noreferrer">WhatsApp</a></li> : null}
            </ul>
          ) : <p className="mt-4 text-sm leading-6 text-slate-500">Les coordonnées seront publiées avant l’ouverture des demandes.</p>}
        </div>
      </div>
      <div className="border-t border-slate-200">
        <div className="site-container flex flex-col gap-4 py-6 text-xs text-slate-500 md:flex-row md:items-center md:justify-between">
          <p>© {new Date().getFullYear()} {settings.business_name}. Tous droits réservés.</p>
          <nav aria-label="Informations légales" className="flex flex-wrap gap-x-5 gap-y-2">
            {legalLinks.map((item) => <Link key={item.href} className="hover:text-slate-950" href={item.href}>{item.label}</Link>)}
          </nav>
        </div>
      </div>
    </footer>
  );
}
