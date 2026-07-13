import { z } from "zod";

const paymentSchema = z.object({
  public_id: z.string().uuid(), booking_public_id: z.string().uuid(), booking_reference: z.string(),
  booking_status: z.string(), provider: z.literal("stripe"), status: z.string(), amount: z.string(),
  currency: z.string().length(3), environment: z.enum(["test", "live"]), paid_at: z.string().nullable(),
  last_error_code: z.string().nullable(), last_error_message: z.string().nullable(),
});

const errorSchema = z.object({ error: z.object({ code: z.string(), message: z.string() }) });
const checkoutSchema = z.object({ checkout_url: z.string().url(), payment: paymentSchema, payment_attempt_id: z.number(), idempotent_replay: z.boolean() });

export type Payment = z.infer<typeof paymentSchema>;

export class PaymentApiError extends Error {
  constructor(message: string, readonly code: string, readonly status: number) { super(message); this.name = "PaymentApiError"; }
}

async function csrfToken(): Promise<string> {
  const response = await fetch("/api/v1/auth/csrf/", { credentials: "same-origin", cache: "no-store" });
  if (!response.ok) throw new PaymentApiError("La session de sécurité n’est pas disponible.", "csrf", response.status);
  return z.object({ csrf_token: z.string() }).parse(await response.json()).csrf_token;
}

async function parseError(response: Response): Promise<never> {
  const body = await response.json().catch(() => null);
  const parsed = errorSchema.safeParse(body);
  throw new PaymentApiError(parsed.success ? parsed.data.error.message : "Le paiement n’a pas pu être traité.", parsed.success ? parsed.data.error.code : "request_error", response.status);
}

export async function createStripeCheckout(bookingPublicId: string, managementToken: string): Promise<{ checkoutUrl: string; payment: Payment }> {
  const csrf = await csrfToken();
  const response = await fetch(`/api/v1/payments/bookings/${bookingPublicId}/checkout/`, {
    method: "POST", credentials: "same-origin", cache: "no-store",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrf, "X-Booking-Token": managementToken, "Idempotency-Key": crypto.randomUUID() },
    body: "{}",
  });
  if (!response.ok) return parseError(response);
  const result = checkoutSchema.parse(await response.json());
  return { checkoutUrl: result.checkout_url, payment: result.payment };
}

export async function getPaymentStatus(bookingPublicId: string, sessionId: string, managementToken = ""): Promise<Payment> {
  const headers: HeadersInit = managementToken ? { "X-Booking-Token": managementToken } : {};
  const response = await fetch(`/api/v1/payments/bookings/${bookingPublicId}/status/?session_id=${encodeURIComponent(sessionId)}`, { credentials: "same-origin", cache: "no-store", headers });
  if (!response.ok) return parseError(response);
  return paymentSchema.parse(await response.json());
}
