"use client";

import { useEffect, useRef, useState } from "react";

import { FormStatus } from "@/components/auth/auth-shell";
import { trackConversion } from "@/lib/analytics";
import { submitContact, type ContactInput } from "@/lib/contact-api";

const initialInput: Omit<ContactInput, "form_started_at"> = {
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  topic: "booking",
  message: "",
  website: "",
};

export function ContactForm() {
  const startedAt = useRef(0);
  const idempotencyKey = useRef("");
  const [input, setInput] = useState(initialInput);
  const [status, setStatus] = useState<"idle" | "submitting" | "sent" | "error">("idle");

  useEffect(() => {
    startedAt.current = Date.now();
    idempotencyKey.current = crypto.randomUUID();
  }, []);

  function update(field: keyof typeof initialInput, value: string) {
    setInput((current) => ({ ...current, [field]: value }));
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!startedAt.current || !idempotencyKey.current) return;
    setStatus("submitting");
    try {
      await submitContact(
        { ...input, form_started_at: startedAt.current },
        idempotencyKey.current,
      );
      setStatus("sent");
      trackConversion("contact_submitted", { topic: input.topic });
      setInput(initialInput);
      startedAt.current = Date.now();
      idempotencyKey.current = crypto.randomUUID();
    } catch {
      setStatus("error");
    }
  }

  return (
    <section className="mt-16 border-t border-slate-200 pt-12" aria-labelledby="contact-form-title">
      <div className="max-w-3xl">
        <p className="eyebrow">Demande écrite</p>
        <h2 id="contact-form-title" className="mt-3 text-3xl font-black text-slate-950">
          Envoyer un message
        </h2>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Ne transmettez aucune donnée bancaire, aucun mot de passe et aucun document d’identité.
        </p>
      </div>
      <form className="mt-8 grid max-w-3xl gap-5 sm:grid-cols-2" onSubmit={submit}>
        <label className="grid gap-2 text-sm font-bold text-slate-800">
          Prénom
          <input className="form-input" required maxLength={100} autoComplete="given-name" value={input.first_name} onChange={(event) => update("first_name", event.target.value)} />
        </label>
        <label className="grid gap-2 text-sm font-bold text-slate-800">
          Nom
          <input className="form-input" required maxLength={100} autoComplete="family-name" value={input.last_name} onChange={(event) => update("last_name", event.target.value)} />
        </label>
        <label className="grid gap-2 text-sm font-bold text-slate-800">
          E-mail
          <input className="form-input" required type="email" maxLength={254} autoComplete="email" value={input.email} onChange={(event) => update("email", event.target.value)} />
        </label>
        <label className="grid gap-2 text-sm font-bold text-slate-800">
          Téléphone
          <input className="form-input" type="tel" maxLength={32} autoComplete="tel" value={input.phone} onChange={(event) => update("phone", event.target.value)} />
        </label>
        <label className="grid gap-2 text-sm font-bold text-slate-800 sm:col-span-2">
          Sujet
          <select className="form-input" value={input.topic} onChange={(event) => update("topic", event.target.value)}>
            <option value="booking">Réservation</option>
            <option value="quote">Devis</option>
            <option value="payment">Paiement</option>
            <option value="accessibility">Accessibilité</option>
            <option value="other">Autre demande</option>
          </select>
        </label>
        <label className="grid gap-2 text-sm font-bold text-slate-800 sm:col-span-2">
          Message
          <textarea className="form-input min-h-36" required minLength={10} maxLength={4000} value={input.message} onChange={(event) => update("message", event.target.value)} />
        </label>
        <label className="absolute -left-[10000px] top-auto h-px w-px overflow-hidden" aria-hidden="true">
          Site web
          <input tabIndex={-1} autoComplete="off" value={input.website} onChange={(event) => update("website", event.target.value)} />
        </label>
        <div className="sm:col-span-2">
          {status === "sent" ? <FormStatus type="success">Votre message a bien été transmis.</FormStatus> : null}
          {status === "error" ? <FormStatus type="error">Le message n’a pas pu être envoyé. Vérifiez les champs ou réessayez plus tard.</FormStatus> : null}
          <button className="button button-primary mt-4" type="submit" disabled={status === "submitting"}>
            {status === "submitting" ? "Envoi…" : "Envoyer le message"}
          </button>
        </div>
      </form>
    </section>
  );
}
