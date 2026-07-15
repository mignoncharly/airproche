import type { Metadata } from "next";
import Link from "next/link";
import { PageHero } from "@/components/marketing";

export const metadata: Metadata = { title: "Ancien parcours de réservation", robots: { index: false, follow: false } };
export default function ReservationPage() { return <main><PageHero eyebrow="Service remplacé" title="AirProche transmet désormais des demandes aux chauffeurs indépendants" description="L’envoi d’une demande ne confirme pas le trajet. Le chauffeur vous répond directement." /><section className="site-container py-16"><div className="mx-auto max-w-xl text-center"><Link className="button button-primary" href="/chauffeurs">Rechercher un chauffeur</Link></div></section></main>; }
