import { notFound } from "next/navigation";
import { PageHero } from "@/components/marketing";
import { InquiryForm } from "@/features/marketplace/inquiry-form";
import { getDriver } from "@/lib/marketplace";

const paymentLabels: Record<string, string> = { cash: "Especes", card_terminal: "Carte sur terminal", bank_transfer: "Virement bancaire", private_payment_link: "Lien de paiement prive" };

export default async function DriverPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params; const driver = await getDriver(id); if (!driver) notFound();
  return <main><PageHero eyebrow="Chauffeur independant" title={driver.display_name} description={driver.bio || "Profil professionnel verifie par la plateforme."} />
    <section className="site-container grid gap-8 py-16 lg:grid-cols-[0.8fr_1.2fr]"><div className="surface-card p-6"><h2 className="text-xl font-black">Couverture publiee</h2><p className="mt-4 text-sm text-slate-600">Aeroports : {driver.airports.map((a) => a.name).join(", ") || "sur demande"}</p><p className="mt-2 text-sm text-slate-600">Zones : {driver.service_areas.map((a) => a.name).join(", ") || "sur demande"}</p><p className="mt-2 text-sm text-slate-600">Paiement accepte : {driver.accepted_payment_methods.map((method) => paymentLabels[method] ?? method).join(", ") || "a confirmer avec le chauffeur"}</p><p className="mt-5 text-sm leading-6 text-slate-600">Airproche ne collecte pas le paiement du trajet. Aucun envoi de formulaire ne vaut reservation.</p></div>{driver.accepts_quote_requests ? <InquiryForm driverId={driver.public_id} airports={driver.airports} /> : null}</section></main>;
}
