import { z } from "zod";

const businessSettingsSchema = z.object({
  business_name: z.string(),
  tagline: z.string(),
  phone: z.string(),
  whatsapp_phone: z.string(),
  email: z.string(),
  support_hours: z.string(),
  address: z.string(),
  city: z.string(),
  postal_code: z.string(),
  country_code: z.string(),
  booking_enabled: z.boolean(),
  currency: z.string().length(3),
  minimum_lead_hours: z.number().int().nonnegative(),
  maximum_booking_days: z.number().int().positive(),
  quote_valid_minutes: z.number().int().positive(),
});

const serviceSchema = z.object({
  slug: z.string(),
  title: z.string(),
  summary: z.string(),
  description: z.string(),
  icon: z.enum(["plane", "luggage", "home", "hotel", "users", "route"]),
});

const faqSchema = z.object({
  public_id: z.string().uuid(),
  question: z.string(),
  answer: z.string(),
});

const testimonialSchema = z.object({
  public_id: z.string().uuid(),
  author_name: z.string(),
  author_context: z.string(),
  quote: z.string(),
  rating: z.number().int().min(1).max(5),
});

const legalDocumentSchema = z.object({
  kind: z.enum(["privacy", "terms", "cancellation", "legal_notice", "cookies", "transparency"]),
  version: z.string(),
  title: z.string(),
  body: z.string(),
  effective_at: z.string(),
});

export const publicContentSchema = z.object({
  settings: businessSettingsSchema,
  services: z.array(serviceSchema),
  faqs: z.array(faqSchema),
  testimonials: z.array(testimonialSchema),
  legal_documents: z.array(legalDocumentSchema),
});

export type PublicContent = z.infer<typeof publicContentSchema>;
export type BusinessSettings = PublicContent["settings"];
export type LegalDocumentKind = PublicContent["legal_documents"][number]["kind"];

const emptyContent: PublicContent = {
  settings: {
    business_name: "Transfert Privé",
    tagline: "Votre transfert aéroport, organisé avec soin.",
    phone: "",
    whatsapp_phone: "",
    email: "",
    support_hours: "",
    address: "",
    city: "",
    postal_code: "",
    country_code: "FR",
    booking_enabled: false,
    currency: "EUR",
    minimum_lead_hours: 12,
    maximum_booking_days: 365,
    quote_valid_minutes: 30,
  },
  services: [],
  faqs: [],
  testimonials: [],
  legal_documents: [],
};

export async function getPublicContent(): Promise<PublicContent> {
  const base = process.env.BACKEND_INTERNAL_URL;
  if (!base) return emptyContent;

  try {
    const response = await fetch(`${base.replace(/\/$/, "")}/api/v1/public/content/`, {
      next: { revalidate: 60 },
    });
    if (!response.ok) throw new Error(`public content status ${response.status}`);
    return publicContentSchema.parse(await response.json());
  } catch (error) {
    console.error("Public content is unavailable", error instanceof Error ? error.message : "unknown");
    return emptyContent;
  }
}

export function phoneHref(phone: string): string {
  return `tel:${phone.replace(/[^+\d]/g, "")}`;
}

export function whatsappHref(phone: string): string {
  return `https://wa.me/${phone.replace(/\D/g, "")}`;
}
