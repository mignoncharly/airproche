import type { MetadataRoute } from "next";

import { getLocationsAndCoverage } from "@/lib/locations-pricing";
import { getPublicContent } from "@/lib/public-content";
import { buildSitemap } from "@/lib/seo";

export const dynamic = "force-dynamic";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [content, locations] = await Promise.all([
    getPublicContent(),
    getLocationsAndCoverage(),
  ]);
  return buildSitemap(content, locations);
}
