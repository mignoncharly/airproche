import { EmptyNotice, PageHero } from "@/components/marketing";
import { getPublicContent, type LegalDocumentKind } from "@/lib/public-content";

const fallbackTitles: Record<LegalDocumentKind, string> = {
  privacy: "Politique de confidentialité",
  terms: "Conditions générales",
  cancellation: "Politique d’annulation",
  legal_notice: "Mentions légales",
  cookies: "Politique relative aux cookies",
};

export async function LegalPage({ kind }: { kind: LegalDocumentKind }) {
  const content = await getPublicContent();
  const document = content.legal_documents.find((item) => item.kind === kind);
  const title = document?.title ?? fallbackTitles[kind];

  return (
    <main>
      <PageHero eyebrow="Informations légales" title={title} description="Le document applicable est publié avec sa version et sa date d’entrée en vigueur." />
      <section className="site-container max-w-4xl py-16 sm:py-22">
        {document ? (
          <article>
            <p className="text-sm font-semibold text-slate-500">Version {document.version} · Applicable depuis le {new Intl.DateTimeFormat("fr-FR", { dateStyle: "long" }).format(new Date(document.effective_at))}</p>
            <div className="mt-8 whitespace-pre-line text-base leading-8 text-slate-700">{document.body}</div>
          </article>
        ) : (
          <EmptyNotice title="Document non publié">
            <p>Ce texte doit encore être validé et publié par l’entreprise. Aucune réservation n’est ouverte tant que les informations légales nécessaires ne sont pas disponibles.</p>
          </EmptyNotice>
        )}
      </section>
    </main>
  );
}
