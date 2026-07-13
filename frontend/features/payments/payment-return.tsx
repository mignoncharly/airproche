"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { trackConversion } from "@/lib/analytics";
import { PaymentApiError, type Payment, getPaymentStatus } from "@/lib/payment-api";
import { formatMoney } from "@/lib/locations-pricing";
import { useSensitiveFragment } from "@/lib/sensitive-fragment";

export function PaymentReturnFromFragment() {
  const fragment = useSensitiveFragment();
  if (fragment === null) return <section className="surface-card p-6 sm:p-8"><p className="text-sm text-slate-600">Vérification du retour sécurisé…</p></section>;
  return <PaymentReturn bookingId={fragment.get("booking") ?? ""} sessionId={fragment.get("session_id") ?? ""} cancelled={fragment.get("cancelled") === "1"} />;
}

export function PaymentReturn({ bookingId, sessionId, cancelled }: { bookingId: string; sessionId: string; cancelled: boolean }) {
  const [payment, setPayment] = useState<Payment | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(!cancelled);
  const trackedSuccess = useRef(false);

  useEffect(() => {
    if (cancelled) return;
    let active = true;
    let attempts = 0;
    async function poll() {
      try {
        const result = await getPaymentStatus(bookingId, sessionId);
        if (!active) return;
        setPayment(result);
        if (result.status === "succeeded" && !trackedSuccess.current) {
          trackConversion("payment_succeeded", { provider: "stripe", currency: result.currency });
          trackedSuccess.current = true;
        }
        if (["succeeded", "failed", "canceled", "mismatched", "refunded"].includes(result.status) || attempts >= 5) setChecking(false);
        else { attempts += 1; window.setTimeout(poll, 2500); }
      } catch (caught) { if (active) { setError(caught instanceof PaymentApiError ? caught.message : "Le statut du paiement ne peut pas être vérifié."); setChecking(false); } }
    }
    void poll();
    return () => { active = false; };
  }, [bookingId, cancelled, sessionId]);

  if (cancelled) return <section className="surface-card p-6 sm:p-8"><p className="eyebrow">Paiement interrompu</p><h1 className="mt-3 text-3xl font-black text-slate-950">Votre réservation est conservée</h1><p className="mt-4 text-sm leading-6 text-slate-600">Aucun paiement confirmé n’a été reçu. Vous pourrez reprendre le paiement depuis votre lien de gestion.</p><Link className="button button-secondary mt-7" href="/tarifs">Retour aux tarifs</Link></section>;
  return <section className="surface-card p-6 sm:p-8" aria-live="polite"><p className="eyebrow">Retour de paiement</p>{checking ? <><h1 className="mt-3 text-3xl font-black text-slate-950">Vérification en cours</h1><p className="mt-4 text-sm leading-6 text-slate-600">Nous attendons la confirmation sécurisée de Stripe. Ne fermez pas cette page.</p></> : error ? <><h1 className="mt-3 text-3xl font-black text-slate-950">Statut indisponible</h1><p className="mt-4 text-sm leading-6 text-slate-600">{error}</p></> : payment?.status === "succeeded" ? <><h1 className="mt-3 text-3xl font-black text-slate-950">Paiement confirmé</h1><p className="mt-4 text-sm leading-6 text-slate-600">La réservation {payment.booking_reference} est confirmée pour {formatMoney(payment.amount, payment.currency)}.</p></> : <><h1 className="mt-3 text-3xl font-black text-slate-950">Paiement non confirmé</h1><p className="mt-4 text-sm leading-6 text-slate-600">Le paiement est actuellement « {payment?.status ?? "en attente"} ». Vous pouvez réessayer depuis la gestion de réservation.</p></>}<Link className="button button-primary mt-7" href="/reservation/gerer">Gérer ma réservation</Link></section>;
}
