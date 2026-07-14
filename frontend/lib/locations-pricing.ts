import { z } from "zod";

export const airportSchema = z.object({
  public_id: z.string().uuid(),
  name: z.string(),
  iata_code: z.string().length(3),
  slug: z.string(),
  city: z.string(),
  country_code: z.string().length(2),
});

export const airportDetailSchema = airportSchema.extend({
  address: z.string(),
  latitude: z.string(),
  longitude: z.string(),
  timezone: z.string(),
  terminal_guidance: z.string(),
  description: z.string(),
  seo_title: z.string(),
  seo_description: z.string(),
});

export const serviceAreaSchema = z.object({
  public_id: z.string().uuid(),
  name: z.string(),
  slug: z.string(),
  area_type: z.enum(["city", "region", "postal_zone", "custom"]),
  country_code: z.string().length(2),
  region: z.string(),
  city: z.string(),
  description: z.string(),
});

export const serviceAreaDetailSchema = serviceAreaSchema.extend({
  postal_codes: z.array(z.string()),
});

export const coverageOptionSchema = z.object({
  code: z.string(),
  label: z.string(),
  pricing_method: z.enum(["fixed", "per_unit"]),
  maximum_quantity: z.number().int().positive(),
});

export const coverageRouteSchema = z.object({
  airport_id: z.string().uuid(),
  service_area_id: z.string().uuid(),
  trip_type: z.enum(["airport_pickup", "airport_dropoff"]),
  options: z.array(coverageOptionSchema),
});

export const coverageSchema = z.object({ routes: z.array(coverageRouteSchema) });

const quoteLineSchema = z.object({
  code: z.string(),
  label: z.string(),
  quantity: z.number().int().positive(),
  unit_amount: z.string(),
  total_amount: z.string(),
});

export const quoteSchema = z.object({
  public_id: z.string().uuid(),
  trip_type: z.enum(["airport_pickup", "airport_dropoff"]),
  airport_name: z.string(),
  airport_iata_code: z.string(),
  service_area_name: z.string(),
  pickup_at: z.string(),
  passenger_count: z.number().int().positive(),
  luggage_count: z.number().int().nonnegative(),
  total_amount: z.string(),
  currency: z.string().length(3),
  calculation_version: z.string(),
  status: z.enum(["valid", "expired"]),
  expires_at: z.string(),
  lines: z.array(quoteLineSchema),
});

const apiErrorSchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
    fields: z.unknown().nullable().optional(),
    request_id: z.string().nullable().optional(),
  }),
});

export type Airport = z.infer<typeof airportSchema>;
export type AirportDetail = z.infer<typeof airportDetailSchema>;
export type ServiceArea = z.infer<typeof serviceAreaSchema>;
export type ServiceAreaDetail = z.infer<typeof serviceAreaDetailSchema>;
export type Coverage = z.infer<typeof coverageSchema>;
export type CoverageRoute = z.infer<typeof coverageRouteSchema>;
export type Quote = z.infer<typeof quoteSchema>;

export type QuoteRequest = {
  trip_type: "airport_pickup" | "airport_dropoff";
  airport_id: string;
  service_area_id: string;
  pickup_at: string;
  passenger_count: number;
  luggage_count: number;
  options: Array<{ code: string; quantity: number }>;
};

export class QuoteApiError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "QuoteApiError";
  }
}

function serverApiBase(): string | null {
  return process.env.BACKEND_INTERNAL_URL?.replace(/\/$/, "") ?? null;
}

async function serverGet<T>(path: string, schema: z.ZodType<T>): Promise<T | null> {
  const base = serverApiBase();
  if (!base) return null;
  try {
    const response = await fetch(`${base}${path}`, {
      headers: { "X-Forwarded-Proto": "https" },
      next: { revalidate: 60 },
    });
    if (!response.ok) return null;
    return schema.parse(await response.json());
  } catch (error) {
    console.error("Locations/pricing API unavailable", error instanceof Error ? error.message : "unknown");
    return null;
  }
}

export async function getLocationsAndCoverage(): Promise<{
  airports: Airport[];
  serviceAreas: ServiceArea[];
  coverage: Coverage;
}> {
  const [airports, serviceAreas, coverage] = await Promise.all([
    serverGet("/api/v1/public/locations/airports/", airportSchema.array()),
    serverGet("/api/v1/public/locations/service-areas/", serviceAreaSchema.array()),
    serverGet("/api/v1/public/pricing/coverage/", coverageSchema),
  ]);
  return {
    airports: airports ?? [],
    serviceAreas: serviceAreas ?? [],
    coverage: coverage ?? { routes: [] },
  };
}

export async function getAirport(slug: string): Promise<AirportDetail | null> {
  return serverGet(`/api/v1/public/locations/airports/${encodeURIComponent(slug)}/`, airportDetailSchema);
}

export async function getServiceArea(slug: string): Promise<ServiceAreaDetail | null> {
  return serverGet(
    `/api/v1/public/locations/service-areas/${encodeURIComponent(slug)}/`,
    serviceAreaDetailSchema,
  );
}

export async function createQuote(payload: QuoteRequest): Promise<Quote> {
  const response = await fetch("/api/v1/public/pricing/quotes/", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const parsed = apiErrorSchema.safeParse(body);
    throw new QuoteApiError(
      parsed.success ? parsed.data.error.message : "L’estimation n’a pas pu être calculée.",
      parsed.success ? parsed.data.error.code : "request_error",
      response.status,
    );
  }
  return quoteSchema.parse(body);
}

export function formatMoney(amount: string, currency: string): string {
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency }).format(Number(amount));
}
