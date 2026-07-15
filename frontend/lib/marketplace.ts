import { z } from "zod";

import { mutateWithCsrf } from "./auth-api";

const airportSchema = z.object({ public_id: z.string().uuid(), name: z.string(), iata_code: z.string(), slug: z.string(), city: z.string(), country_code: z.string() });
const areaSchema = z.object({ public_id: z.string().uuid(), name: z.string(), slug: z.string(), area_type: z.string(), country_code: z.string(), region: z.string(), city: z.string(), description: z.string() });
const vehicleSchema = z.object({ make: z.string(), model: z.string(), year: z.number().nullable(), category: z.string(), color: z.string(), passenger_capacity: z.number(), luggage_capacity: z.number(), photo_url: z.string(), air_conditioning: z.boolean(), child_seat: z.boolean(), wheelchair_accessible: z.boolean(), pets_allowed: z.boolean(), non_smoking: z.boolean(), amenities: z.array(z.string()) });
export const driverSchema = z.object({
  public_id: z.string().uuid(), slug: z.string(), display_name: z.string(), business_name: z.string(), bio: z.string(), profile_photo_url: z.string(), years_experience: z.number(), languages: z.array(z.string()), directions: z.array(z.string()), max_passengers: z.number(), accepted_payment_methods: z.array(z.enum(["cash", "card_terminal", "bank_transfer", "private_payment_link"])), airports: z.array(airportSchema), service_areas: z.array(areaSchema), vehicle: vehicleSchema.nullable(), indicative_price_from: z.string().nullable(), indicative_price_currency: z.string(), pricing_note: z.string(), minimum_notice_hours: z.number(), typical_response_minutes: z.number().nullable(), availability_note: z.string(), accepts_quote_requests: z.boolean(), public_phone: z.string(), public_whatsapp: z.string(), verified_at: z.string().nullable(),
});
export type MarketplaceDriver = z.infer<typeof driverSchema>;
const pageSchema = z.object({ count: z.number(), next: z.string().nullable(), previous: z.string().nullable(), results: z.array(driverSchema) });
export type DriverPage = z.infer<typeof pageSchema>;

export type DriverSearch = { q?: string; airport?: string; service_area?: string; direction?: string; passengers?: string; luggage?: string; language?: string; vehicle_category?: string; accessible?: string; child_seat?: string; sort?: string; page?: string };

function base() { return process.env.BACKEND_INTERNAL_URL?.replace(/\/$/, ""); }
function queryString(filters: DriverSearch) { const query = new URLSearchParams(); Object.entries(filters).forEach(([key, value]) => { if (value) query.set(key, value); }); return query.toString(); }

export async function getDrivers(filters: DriverSearch = {}): Promise<DriverPage> {
  if (!base()) return { count: 0, next: null, previous: null, results: [] };
  try {
    const query = queryString(filters);
    const response = await fetch(`${base()}/api/v1/marketplace/drivers/${query ? `?${query}` : ""}`, { headers: { "X-Forwarded-Proto": "https" }, next: { revalidate: 60 } });
    return response.ok ? pageSchema.parse(await response.json()) : { count: 0, next: null, previous: null, results: [] };
  } catch { return { count: 0, next: null, previous: null, results: [] }; }
}

export async function getDriver(identifier: string): Promise<MarketplaceDriver | null> {
  if (!base()) return null;
  try {
    const response = await fetch(`${base()}/api/v1/marketplace/drivers/${encodeURIComponent(identifier)}/`, { headers: { "X-Forwarded-Proto": "https" }, next: { revalidate: 60 } });
    return response.ok ? driverSchema.parse(await response.json()) : null;
  } catch { return null; }
}

export const inquirySchema = z.object({ public_id: z.string().uuid(), reference: z.string(), airport_name: z.string(), airport_code: z.string(), direction: z.string(), customer_name: z.string(), customer_email: z.string(), customer_phone: z.string(), customer_whatsapp: z.string(), preferred_contact_method: z.string(), whatsapp_consent: z.boolean(), destination: z.string(), pickup_at: z.string().nullable(), passenger_count: z.number(), luggage_count: z.number(), message: z.string(), status: z.string(), status_label: z.string(), created_at: z.string(), updated_at: z.string(), history: z.array(z.object({ from_status: z.string(), to_status: z.string(), status_label: z.string(), customer_visible_note: z.string(), changed_at: z.string() })), notes: z.array(z.object({ body: z.string(), customer_visible: z.boolean(), created_at: z.string() })), notification_status: z.record(z.string(), z.string()), consent: z.object({ privacy_policy_version: z.string(), granted_at: z.string(), allowed_contact_channels: z.array(z.string()) }).nullable() });
export type DriverInquiry = z.infer<typeof inquirySchema>;
const inquiryPageSchema = z.object({ count: z.number(), next: z.string().nullable(), previous: z.string().nullable(), unread_count: z.number(), results: z.array(inquirySchema) });

export async function getMyInquiries(params: Record<string, string> = {}) {
  const response = await fetch(`/api/v1/marketplace/me/inquiries/?${new URLSearchParams(params)}`, { credentials: "same-origin", cache: "no-store" });
  if (!response.ok) throw new Error("Les demandes sont momentanément indisponibles.");
  return inquiryPageSchema.parse(await response.json());
}

export async function transitionMyInquiry(id: string, status: string, note = "", customer_visible_note = "") {
  const body = await mutateWithCsrf(`/api/v1/marketplace/me/inquiries/${id}/transition/`, { method: "POST", body: JSON.stringify({ status, note, customer_visible_note }) });
  return inquirySchema.parse(body);
}

export async function addInquiryNote(id: string, body: string, customer_visible = false) {
  const result = await mutateWithCsrf(`/api/v1/marketplace/me/inquiries/${id}/notes/`, { method: "POST", body: JSON.stringify({ body, customer_visible }) });
  return inquirySchema.parse(result);
}
