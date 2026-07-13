"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Page rendering failed", error.digest ?? "unknown");
  }, [error.digest]);

  return (
    <main className="mx-auto max-w-2xl px-6 py-24">
      <h1 className="text-3xl font-bold text-slate-950">Une erreur est survenue</h1>
      <p className="mt-4 text-slate-700">Veuillez réessayer. Aucune réservation n’a été validée par cet écran.</p>
      <button
        type="button"
        onClick={reset}
        className="mt-8 min-h-11 rounded-md bg-blue-700 px-5 py-3 font-semibold text-white hover:bg-blue-800"
      >
        Réessayer
      </button>
    </main>
  );
}

