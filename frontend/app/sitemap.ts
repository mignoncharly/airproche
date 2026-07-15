import type { MetadataRoute } from "next";

import { getLocationsAndCoverage } from "@/lib/locations-pricing";
import { getPublicContent } from "@/lib/public-content";
import { buildSitemap } from "@/lib/seo";
import { getDrivers } from "@/lib/marketplace";

export const dynamic = "force-dynamic";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [content, locations, drivers] = await Promise.all([
    getPublicContent(),
    getLocationsAndCoverage(),
    getDrivers({}),
  ]);
  const base = buildSitemap(content, locations);
  return [...base, ...drivers.results.map((driver) => ({ url: new URL(`/chauffeurs/${driver.slug}`, process.env.APP_BASE_URL ?? "http://localhost:3000").toString(), changeFrequency: "weekly" as const, priority: 0.8 }))];
}
