import { z } from "zod";

const quoteLineSchema = z.object({
  code: z.string(), label: z.string(), quantity: z.number().int().positive(),
  unit_amount: z.string(), total_amount: z.string(),
});

export const bookingQuoteSchema = z.object({
  public_id: z.string().uuid(), trip_type: z.enum(["airport_pickup", "airport_dropoff"]),
  airport_name: z.string(), airport_iata_code: z.string(), service_area_name: z.string(),
  pickup_at: z.string(), passenger_count: z.number().int().positive(), luggage_count: z.number().int().nonnegative(),
  total_amount: z.string(), currency: z.string().length(3), calculation_version: z.string(),
  status: z.enum(["valid", "expired"]), expires_at: z.string(), lines: z.array(quoteLineSchema),
});

const bookingSchema = z.object({
  public_id: z.string().uuid(), reference: z.string(), booking_type: z.string(), status: z.string(),
  airport: z.object({ name: z.string(), iata_code: z.string() }),
  service_area: z.object({ name: z.string(), slug: z.string() }),
  pickup_at: z.string(), passenger_count: z.number(), luggage_count: z.number(),
  total_amount: z.string(), currency: z.string(), cancellation_eligible: z.boolean(),
  management_token: z.string().nullable().optional(),
  lines: z.array(quoteLineSchema), history: z.array(z.object({ from_status: z.string(), to_status: z.string(), note: z.string(), created_at: z.string() })),
});

const errorSchema = z.object({ error: z.object({ code: z.string(), message: z.string(), fields: z.unknown().nullable().optional() }) });

export type BookingQuote = z.infer<typeof bookingQuoteSchema>;
export type Booking = z.infer<typeof bookingSchema>;

export const customerBookingSchema = bookingSchema.extend({
  payment_status: z.string(), payment_environment: z.string().nullable(), is_upcoming: z.boolean(),
});

export type CustomerBooking = z.infer<typeof customerBookingSchema>;


export class BookingApiError extends Error {
  constructor(message: string, readonly code: string, readonly status: number, readonly fields?: unknown) {
    super(message);
    this.name = "BookingApiError";
  }
}

export async function getBookingQuote(publicId: string): Promise<BookingQuote | null> {
  const base = process.env.BACKEND_INTERNAL_URL?.replace(/\/$/, "");
  if (!base) return null;
  const response = await fetch(`${base}/api/v1/public/pricing/quotes/${encodeURIComponent(publicId)}/`, { cache: "no-store" });
  if (!response.ok) return null;
  return bookingQuoteSchema.parse(await response.json());
}

async function csrfToken(): Promise<string> {
  const response = await fetch("/api/v1/auth/csrf/", { credentials: "same-origin", cache: "no-store" });
  if (!response.ok) throw new BookingApiError("La session de sécurité n’est pas disponible.", "csrf", response.status);
  const body = z.object({ csrf_token: z.string() }).parse(await response.json());
  return body.csrf_token;
}

async function parseError(response: Response): Promise<never> {
  const payload = await response.json().catch(() => null);
  const parsed = errorSchema.safeParse(payload);
  throw new BookingApiError(
    parsed.success ? parsed.data.error.message : "La réservation n’a pas pu être enregistrée.",
    parsed.success ? parsed.data.error.code : "request_error", response.status,
    parsed.success ? parsed.data.error.fields : undefined,
  );
}

export async function createBooking(input: Record<string, unknown>): Promise<Booking> {
  const token = await csrfToken();
  const response = await fetch("/api/v1/bookings/", {
    method: "POST", credentials: "same-origin", cache: "no-store",
    headers: { "Content-Type": "application/json", "X-CSRFToken": token, "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify(input),
  });
  if (!response.ok) return parseError(response);
  return bookingSchema.parse(await response.json());
}

export async function accessGuestBooking(reference: string, managementToken: string): Promise<Booking> {
  const response = await fetch("/api/v1/bookings/guest-access/", {
    method: "POST", credentials: "same-origin", cache: "no-store",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reference, management_token: managementToken }),
  });
  if (!response.ok) return parseError(response);
  return bookingSchema.parse(await response.json());
}

export async function cancelGuestBooking(publicId: string, managementToken: string, reason = ""): Promise<Booking> {
  const token = await csrfToken();
  const response = await fetch(`/api/v1/bookings/${publicId}/cancel/`, {
    method: "POST", credentials: "same-origin", cache: "no-store",
    headers: { "Content-Type": "application/json", "X-CSRFToken": token, "X-Booking-Token": managementToken, "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({ reason }),
  });
  if (!response.ok) return parseError(response);
  return bookingSchema.parse(await response.json());
}

export async function getCustomerBookings(): Promise<CustomerBooking[]> {
  const response = await fetch("/api/v1/bookings/mine/", { credentials: "same-origin", cache: "no-store" });
  if (response.status === 401 || response.status === 403) return [];
  if (!response.ok) return parseError(response);
  return customerBookingSchema.array().parse(await response.json());
}

export async function repeatBooking(publicId: string, pickupAt: string): Promise<BookingQuote> {
  const csrf = await csrfToken();
  const response = await fetch(`/api/v1/bookings/${publicId}/repeat/`, {
    method: "POST", credentials: "same-origin", cache: "no-store",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrf, "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({ pickup_at: pickupAt }),
  });
  if (!response.ok) return parseError(response);
  return bookingQuoteSchema.parse(await response.json());
}

export function bookingReceiptUrl(publicId: string): string {
  return `/api/v1/bookings/${publicId}/receipt/`;
}
