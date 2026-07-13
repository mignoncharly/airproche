import type { Metadata, MetadataRoute } from "next";

import type { Airport, Coverage, ServiceArea } from "./locations-pricing";
import type { BusinessSettings, PublicContent } from "./public-content";

const DEFAULT_ORIGIN = "http://localhost:3000";

export function siteOrigin(): string {
  const configured = process.env.APP_BASE_URL || DEFAULT_ORIGIN;
  return new URL(configured).origin;
}

export function absoluteUrl(path: string): string {
  return new URL(path.startsWith("/") ? path : `/${path}`, `${siteOrigin()}/`).toString();
}

export function publicMetadata(
  title: string,
  description: string,
  path: string,
): Metadata {
  return {
    title,
    description,
    alternates: { canonical: absoluteUrl(path) },
    robots: { index: true, follow: true },
    openGraph: {
      type: "website",
      locale: "fr_FR",
      title,
      description,
      url: absoluteUrl(path),
    },
  };
}

type LocationData = {
  airports: Airport[];
  serviceAreas: ServiceArea[];
  coverage: Coverage;
};

export function buildSitemap(
  content: PublicContent,
  data: LocationData,
): MetadataRoute.Sitemap {
  const paths = ["/", "/fonctionnement", "/a-propos"];
  if (data.coverage.routes.length) {
    paths.push("/aeroports", "/zones-desservies", "/tarifs");
  }
  if (content.services.length) paths.push("/services");
  if (content.faqs.length) paths.push("/faq");
  if (content.settings.email || content.settings.phone) paths.push("/contact");

  const airportIds = new Set(data.coverage.routes.map((route) => route.airport_id));
  const areaIds = new Set(data.coverage.routes.map((route) => route.service_area_id));
  const entityPaths = [
    ...data.airports
      .filter((airport) => airportIds.has(airport.public_id))
      .map((airport) => `/aeroports/${airport.slug}`),
    ...data.serviceAreas
      .filter((area) => areaIds.has(area.public_id))
      .map((area) => `/zones-desservies/${area.slug}`),
  ];

  return [...new Set([...paths, ...entityPaths])].map((path) => ({
    url: absoluteUrl(path),
    changeFrequency: path === "/" ? "daily" : "weekly",
    priority: path === "/" ? 1 : path.split("/").length > 2 ? 0.7 : 0.8,
  }));
}

export function businessStructuredData(
  settings: BusinessSettings,
  services: PublicContent["services"],
): Record<string, unknown> | null {
  const hasPublishedIdentity = Boolean(settings.phone || settings.email || settings.address);
  if (!hasPublishedIdentity) return null;

  const data: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "@id": absoluteUrl("/#business"),
    name: settings.business_name,
    url: absoluteUrl("/"),
    areaServed: settings.country_code,
  };
  if (settings.phone) data.telephone = settings.phone;
  if (settings.email) data.email = settings.email;
  if (settings.address) {
    data.address = {
      "@type": "PostalAddress",
      streetAddress: settings.address,
      addressLocality: settings.city || undefined,
      postalCode: settings.postal_code || undefined,
      addressCountry: settings.country_code,
    };
  }
  const publishedServices = services
    .filter((service) => service.slug && service.title && service.summary)
    .map((service) => ({
      "@type": "Offer",
      itemOffered: {
        "@type": "Service",
        name: service.title,
        description: service.summary,
      },
    }));
  if (publishedServices.length) data.makesOffer = publishedServices;
  return data;
}

export function airportStructuredData(airport: {
  name: string;
  iata_code: string;
  city: string;
  country_code: string;
  address: string;
  latitude: string;
  longitude: string;
  slug: string;
}): Record<string, unknown> {
  return {
    "@context": "https://schema.org",
    "@type": "Airport",
    "@id": absoluteUrl(`/aeroports/${airport.slug}#airport`),
    name: airport.name,
    iataCode: airport.iata_code,
    address: {
      "@type": "PostalAddress",
      streetAddress: airport.address,
      addressLocality: airport.city,
      addressCountry: airport.country_code,
    },
    geo: {
      "@type": "GeoCoordinates",
      latitude: airport.latitude,
      longitude: airport.longitude,
    },
  };
}

export function serializeJsonLd(data: Record<string, unknown>): string {
  return JSON.stringify(data).replaceAll("<", "\\u003c");
}
