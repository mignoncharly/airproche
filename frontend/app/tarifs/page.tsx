import type { Metadata } from "next";
import Link from "next/link";
import { PageHero } from "@/components/marketing";

export const metadata: Metadata = { title: "Tarifs des chauffeurs", robots: { index: false, follow: true } };
export default function PricingPage() { return <main><PageHero eyebrow="Évolution du service" title="Les tarifs sont proposés directement par chaque chauffeur" description="AirProche ne calcule, ne garantit et n’encaisse pas le prix du transport." /><section className="site-container py-16"><div className="mx-auto max-w-2xl rounded-[2rem] border border-blue-200 bg-blue-50 p-8"><h2 className="text-2xl font-black">Consultez les profils disponibles</h2><p className="mt-4 leading-7 text-slate-700">Les éventuels montants affichés sur un profil sont indicatifs. Le chauffeur confirme directement sa disponibilité, le tarif final, le paiement et ses conditions.</p><Link className="button button-primary mt-6" href="/chauffeurs">Trouver un chauffeur</Link></div></section></main>; }
