import type { BusinessSettings } from "@/lib/public-content";
import { phoneHref, whatsappHref } from "@/lib/public-content";

import { EmptyNotice } from "./marketing";
import { Icon } from "./icon";

export function ContactMethods({ settings }: { settings: BusinessSettings }) {
  const methods = [
    settings.phone ? { icon: "phone" as const, label: "Téléphone", value: settings.phone, href: phoneHref(settings.phone), external: false } : null,
    settings.whatsapp_phone ? { icon: "message" as const, label: "WhatsApp", value: settings.whatsapp_phone, href: whatsappHref(settings.whatsapp_phone), external: true } : null,
    settings.email ? { icon: "mail" as const, label: "E-mail", value: settings.email, href: `mailto:${settings.email}`, external: false } : null,
  ].filter((method) => method !== null);

  if (!methods.length) {
    return <EmptyNotice title="Coordonnées en cours de configuration"><p>Aucun canal de contact n’est encore publié. Les demandes de transport ne sont donc pas ouvertes depuis ce site.</p></EmptyNotice>;
  }

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {methods.map((method) => (
        <a key={method.label} href={method.href} target={method.external ? "_blank" : undefined} rel={method.external ? "noreferrer" : undefined} className="surface-card group p-6 hover:border-blue-300">
          <span className="grid size-12 place-items-center rounded-2xl bg-blue-50 text-blue-700"><Icon name={method.icon} className="size-6" /></span>
          <span className="mt-5 block text-xs font-extrabold uppercase tracking-[0.14em] text-slate-500">{method.label}</span>
          <span className="mt-2 block break-all font-bold text-slate-950 group-hover:text-blue-700">{method.value}</span>
        </a>
      ))}
    </div>
  );
}
