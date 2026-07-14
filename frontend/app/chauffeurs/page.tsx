import type { Metadata } from "next";
import Link from "next/link";
import { EmptyNotice, PageHero } from "@/components/marketing";
import { getDrivers } from "@/lib/marketplace";

export const metadata: Metadata = { title: "Chauffeurs independants" };
export default async function DriversPage() {
  const drivers = await getDrivers();
  return <main><PageHero eyebrow="Annuaire" title="Trouvez un chauffeur independant" description="Consultez les profils verifies et contactez directement le chauffeur de votre choix." />
    <section className="site-container py-16"><div className="mb-8 rounded-2xl bg-blue-50 p-5 text-sm leading-6 text-blue-950">Airproche met en relation. Le chauffeur reste votre interlocuteur pour le prix, la confirmation, le transport et le paiement.</div>
    {drivers.length ? <div className="grid gap-5 md:grid-cols-2">{drivers.map((driver) => <article className="surface-card p-7" key={driver.public_id}><p className="text-xs font-bold uppercase tracking-wider text-blue-700">Profil verifie</p><h2 className="mt-3 text-2xl font-black text-slate-950">{driver.display_name}</h2><p className="mt-2 text-sm text-slate-600">{driver.business_name || "Chauffeur independant"}  -  jusqu&apos;a {driver.max_passengers} passagers</p><p className="mt-4 line-clamp-3 text-sm leading-6 text-slate-600">{driver.bio || "Contactez ce chauffeur pour connaitre ses disponibilites."}</p><Link className="button button-primary mt-6" href={`/chauffeurs/${driver.public_id}`}>Voir et contacter</Link></article>)}</div> : <EmptyNotice title="Aucun chauffeur publie"><p>Les profils apparaissent uniquement apres verification administrative.</p></EmptyNotice>}</section></main>;
}
