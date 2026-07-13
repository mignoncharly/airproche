import { z } from "zod";

const errorSchema = z.object({ error: z.object({ code: z.string().optional(), message: z.string().optional() }).optional() });
const driverSchema = z.object({ public_id: z.string().uuid(), name: z.string(), first_name: z.string(), last_name: z.string(), phone: z.string(), email: z.string(), max_passengers: z.number(), active: z.boolean(), service_area_ids: z.array(z.string().uuid()), notes: z.string() }).passthrough();
const vehicleSchema = z.object({ public_id: z.string().uuid(), registration: z.string(), label: z.string(), seats: z.number(), luggage_capacity: z.number(), accessibility_capable: z.boolean(), active: z.boolean(), notes: z.string() }).passthrough();
const paymentSchema = z.object({ public_id: z.string().uuid(), booking_reference: z.string(), booking_status: z.string(), provider: z.string(), status: z.string(), amount: z.string(), currency: z.string(), environment: z.string(), paid_at: z.string().nullable(), last_error_code: z.string(), last_error_message: z.string() }).passthrough();
const assignmentSchema = z.object({ public_id: z.string().uuid(), driver: driverSchema, vehicle: vehicleSchema, assigned_at: z.string(), unassigned_at: z.string().nullable(), override_reason: z.string(), active: z.boolean() }).passthrough();
const bookingSchema = z.object({ public_id: z.string().uuid(), reference: z.string(), status: z.string(), booking_type: z.string(), pickup_at: z.string(), passenger_count: z.number(), luggage_count: z.number(), total_amount: z.string(), currency: z.string(), booker_first_name: z.string(), booker_last_name: z.string(), booker_email: z.string(), booker_phone: z.string(), customer_email: z.string().nullable(), airport: z.object({ name: z.string(), iata_code: z.string() }), service_area: z.object({ name: z.string(), slug: z.string() }), history: z.array(z.object({ from_status: z.string(), to_status: z.string(), note: z.string(), created_at: z.string() })), notes: z.array(z.object({ visibility: z.string(), body: z.string(), created_at: z.string() })), assignment: assignmentSchema.nullable(), payment: paymentSchema.nullable() }).passthrough();
const summarySchema = z.object({ period: z.object({ from: z.string(), to: z.string(), timezone: z.string() }), has_data: z.boolean(), total_bookings: z.number(), pending_assignment: z.number(), unassigned_upcoming: z.number(), active_trips: z.number(), payment_attention: z.number(), confirmed_revenue: z.string(), currency: z.string() });

export type OperationsDriver = z.infer<typeof driverSchema>;
export type OperationsVehicle = z.infer<typeof vehicleSchema>;
export type OperationsBooking = z.infer<typeof bookingSchema>;
export type OperationsSummary = z.infer<typeof summarySchema>;

export class OperationsApiError extends Error {
  constructor(message: string, readonly status: number, readonly code = "request_error") { super(message); this.name = "OperationsApiError"; }
}

async function parseError(response: Response): Promise<never> {
  const body = await response.json().catch(() => null);
  const parsed = errorSchema.safeParse(body);
  throw new OperationsApiError(parsed.success ? parsed.data.error?.message ?? "La demande opérationnelle a échoué." : "La demande opérationnelle a échoué.", response.status, parsed.success ? parsed.data.error?.code ?? "request_error" : "request_error");
}

async function csrfToken(): Promise<string> {
  const response = await fetch("/api/v1/auth/csrf/", { credentials: "same-origin", cache: "no-store" });
  if (!response.ok) return parseError(response);
  return z.object({ csrf_token: z.string() }).parse(await response.json()).csrf_token;
}

async function getJson<T>(path: string, schema: z.ZodType<T>): Promise<T> {
  const response = await fetch(path, { credentials: "same-origin", cache: "no-store" });
  if (!response.ok) return parseError(response);
  return schema.parse(await response.json());
}

async function mutate<T>(path: string, body: unknown, schema: z.ZodType<T>): Promise<T> {
  const csrf = await csrfToken();
  const response = await fetch(path, { method: "POST", credentials: "same-origin", cache: "no-store", headers: { "Content-Type": "application/json", "X-CSRFToken": csrf, "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(body) });
  if (!response.ok) return parseError(response);
  return schema.parse(await response.json());
}

export function getOperationsSummary(): Promise<OperationsSummary> { return getJson("/api/v1/staff/operations/summary/", summarySchema); }

export function getOperationsBookings(filters: { q?: string; status?: string; assigned?: string; payment?: string } = {}): Promise<OperationsBooking[]> {
  const params = new URLSearchParams(Object.entries(filters).filter(([, value]) => Boolean(value)) as [string, string][]);
  return getJson(`/api/v1/staff/operations/bookings/${params.size ? `?${params.toString()}` : ""}`, bookingSchema.array());
}

export function getOperationsDrivers(): Promise<OperationsDriver[]> { return getJson("/api/v1/staff/operations/drivers/", driverSchema.array()); }
export function getOperationsVehicles(): Promise<OperationsVehicle[]> { return getJson("/api/v1/staff/operations/vehicles/", vehicleSchema.array()); }

export function transitionOperationBooking(publicId: string, toStatus: string, note = ""): Promise<OperationsBooking> { return mutate(`/api/v1/staff/operations/bookings/${publicId}/transition/`, { to_status: toStatus, note }, bookingSchema); }
export function addOperationNote(publicId: string, body: string, visibility: "internal" | "customer" = "internal") { return mutate(`/api/v1/staff/operations/bookings/${publicId}/notes/`, { body, visibility }, z.object({ id: z.number() }).passthrough()); }
export function assignOperationBooking(publicId: string, driverId: string, vehicleId: string, allowOverride = false, overrideReason = "") { return mutate(`/api/v1/staff/operations/bookings/${publicId}/assignment/`, { driver_id: driverId, vehicle_id: vehicleId, allow_override: allowOverride, override_reason: overrideReason }, assignmentSchema); }
export function unassignOperationBooking(assignmentId: string, reason = "") { return mutate(`/api/v1/staff/operations/assignments/${assignmentId}/unassign/`, { reason }, assignmentSchema); }
export function refundOperationPayment(paymentId: string, reason: string) { return mutate(`/api/v1/payments/${paymentId}/refund/`, { reason }, z.object({ id: z.number(), status: z.string() }).passthrough()); }

