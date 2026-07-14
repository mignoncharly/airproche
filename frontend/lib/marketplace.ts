import { z } from "zod";

const airportSchema = z.object({ public_id: z.string().uuid(), name: z.string(), iata_code: z.string(), slug: z.string(), city: z.string(), country_code: z.string() });
const areaSchema = z.object({ public_id: z.string().uuid(), name: z.string(), slug: z.string(), area_type: z.string(), country_code: z.string(), region: z.string(), city: z.string(), description: z.string() });
export const driverSchema = z.object({
  public_id: z.string().uuid(), display_name: z.string(), business_name: z.string(), bio: z.string(),
  max_passengers: z.number(), accepted_payment_methods: z.array(z.enum(["cash", "card_terminal", "bank_transfer", "private_payment_link"])), airports: z.array(airportSchema), service_areas: z.array(areaSchema), accepts_quote_requests: z.boolean(),
});
export type MarketplaceDriver = z.infer<typeof driverSchema>;

function base() { return process.env.BACKEND_INTERNAL_URL?.replace(/\/$/, ""); }
export async function getDrivers(): Promise<MarketplaceDriver[]> {
  if (!base()) return [];
  try {
    const response = await fetch(`${base()}/api/v1/marketplace/drivers/`, { next: { revalidate: 60 } });
    return response.ok ? driverSchema.array().parse(await response.json()) : [];
  } catch { return []; }
}
export async function getDriver(id: string): Promise<MarketplaceDriver | null> {
  if (!base()) return null;
  try {
    const response = await fetch(`${base()}/api/v1/marketplace/drivers/${encodeURIComponent(id)}/`, { next: { revalidate: 60 } });
    return response.ok ? driverSchema.parse(await response.json()) : null;
  } catch { return null; }
}
