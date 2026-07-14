"use client";

import { useSyncExternalStore } from "react";

import {
  getAnalyticsConsent,
  setAnalyticsConsent,
  subscribeAnalyticsConsent,
  type AnalyticsConsent,
} from "@/lib/analytics";

const serverConsent = (): AnalyticsConsent => "denied";

export function AnalyticsConsentBanner() {
  const consent = useSyncExternalStore(
    subscribeAnalyticsConsent,
    getAnalyticsConsent,
    serverConsent,
  );

  if (consent) return null;

  return (
    <aside className="pointer-events-auto w-full rounded-2xl border border-slate-300 bg-white p-4 shadow-2xl sm:max-w-md" aria-label="Consentement aux mesures d’audience">
      <p className="text-sm font-bold text-slate-950">Mesure d’audience</p>
      <p className="mt-1 text-sm leading-6 text-slate-600">
        Nous pouvons mesurer les étapes du parcours sans transmettre vos coordonnées. Votre choix peut être refusé sans affecter le service.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button className="button button-primary" type="button" onClick={() => setAnalyticsConsent("granted")}>Accepter</button>
        <button className="button button-secondary" type="button" onClick={() => setAnalyticsConsent("denied")}>Refuser</button>
      </div>
    </aside>
  );
}
