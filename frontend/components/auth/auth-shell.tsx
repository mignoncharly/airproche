import Link from "next/link";
import type { ReactNode } from "react";

import { Icon } from "@/components/icon";

export function AuthShell({ eyebrow, title, description, children }: { eyebrow: string; title: string; description: string; children: ReactNode }) {
  return (
    <main className="bg-slate-50 py-12 sm:py-18">
      <div className="site-container grid min-h-[36rem] items-center gap-10 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="hidden max-w-md lg:block">
          <span className="grid size-14 place-items-center rounded-2xl bg-blue-700 text-white shadow-lg"><Icon name="shield" className="size-7" /></span>
          <p className="mt-7 text-sm font-extrabold uppercase tracking-[0.16em] text-blue-700">Espace client sécurisé</p>
          <h2 className="mt-4 text-4xl font-black tracking-[-0.045em] text-slate-950">Vos informations restent protégées par une session sécurisée.</h2>
          <ul className="mt-7 grid gap-3 text-sm text-slate-600">{["Mot de passe jamais transmis en clair", "Actions protégées contre les requêtes externes", "Liens de vérification à usage unique"].map((item) => <li key={item} className="flex gap-3"><Icon name="check" className="size-5 shrink-0 text-emerald-600" />{item}</li>)}</ul>
        </div>
        <section className="mx-auto w-full max-w-xl rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-xl sm:p-9" aria-labelledby="auth-title">
          <p className="text-xs font-extrabold uppercase tracking-[0.15em] text-blue-700">{eyebrow}</p>
          <h1 id="auth-title" className="mt-3 text-3xl font-black tracking-[-0.035em] text-slate-950">{title}</h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">{description}</p>
          <div className="mt-8">{children}</div>
        </section>
      </div>
    </main>
  );
}

export function FormField({ label, error, children, hint }: { label: string; error?: string; children: ReactNode; hint?: string }) {
  return <label className="block"><span className="form-label">{label}</span>{children}{hint && !error ? <span className="mt-1.5 block text-xs leading-5 text-slate-500">{hint}</span> : null}{error ? <span className="form-error" role="alert">{error}</span> : null}</label>;
}

export function AuthLinks({ children }: { children: ReactNode }) {
  return <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-5 text-sm text-slate-600">{children}</div>;
}

export function AuthLink({ href, children }: { href: string; children: ReactNode }) {
  return <Link className="font-bold text-blue-700 hover:underline" href={href}>{children}</Link>;
}

export function FormStatus({ type, children }: { type: "error" | "success" | "info"; children: ReactNode }) {
  const classes = type === "error" ? "border-red-200 bg-red-50 text-red-800" : type === "success" ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-blue-200 bg-blue-50 text-blue-900";
  return <div className={`rounded-xl border p-4 text-sm leading-6 ${classes}`} role={type === "error" ? "alert" : "status"}>{children}</div>;
}
