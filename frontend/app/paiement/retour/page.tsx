import type { Metadata } from "next";
import Link from "next/link";
import { PageHero } from "@/components/marketing";

export const metadata: Metadata = { title: "Ancien paiement AirProche", robots: { index: false, follow: false } };
export default function PaymentReturnPage() { return <main><PageHero eyebrow="Paiement direct" title="AirProche n’encaisse pas le prix du transport" description="Les nouveaux paiements sont convenus directement avec le chauffeur indépendant." /><section className="site-container py-16 text-center"><Link className="button button-primary" href="/chauffeurs">Retour à l’annuaire</Link></section></main>; }
