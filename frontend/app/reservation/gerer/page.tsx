import type { Metadata } from "next";
import Link from "next/link";
import { PageHero } from "@/components/marketing";

export const metadata: Metadata = { title: "Ancien espace réservation", robots: { index: false, follow: false } };
export default function ManageBookingPage() { return <main><PageHero eyebrow="Parcours historique" title="La gestion des nouveaux trajets se fait directement avec le chauffeur" description="Pour une ancienne réservation AirProche, contactez l’assistance en indiquant uniquement votre référence." /><section className="site-container flex justify-center gap-3 py-16"><Link className="button button-primary" href="/contact">Contacter l’assistance</Link><Link className="button button-secondary" href="/chauffeurs">Voir les chauffeurs</Link></section></main>; }
