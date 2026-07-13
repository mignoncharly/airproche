import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-24">
      <h1 className="text-3xl font-bold text-slate-950">Page introuvable</h1>
      <p className="mt-4 text-slate-700">La page demandée n’existe pas ou n’est plus disponible.</p>
      <Link className="mt-8 inline-flex min-h-11 items-center font-semibold text-blue-700 underline" href="/">
        Revenir à l’accueil
      </Link>
    </main>
  );
}

