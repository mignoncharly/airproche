import { afterEach, describe, expect, it } from "vitest";

import type { PublicContent } from "./public-content";
import {
  businessStructuredData,
  buildSitemap,
  publicMetadata,
  serializeJsonLd,
} from "./seo";

const content: PublicContent = {
  settings: {
    business_name: "Fictional Transfer",
    tagline: "Trajets fictifs.",
    phone: "+33100000000",
    whatsapp_phone: "",
    email: "contact@example.test",
    support_hours: "",
    address: "1 rue Exemple",
    city: "Paris",
    postal_code: "75001",
    country_code: "FR",
    booking_enabled: true,
    currency: "EUR",
    minimum_lead_hours: 2,
    maximum_booking_days: 90,
    quote_valid_minutes: 20,
  },
  services: [{
    slug: "accueil",
    title: "Accueil fictif",
    summary: "Service publié.",
    description: "",
    icon: "plane",
  }],
  faqs: [],
  testimonials: [],
  legal_documents: [],
};

afterEach(() => {
  delete process.env.APP_BASE_URL;
});

describe("SEO publication", () => {
  it("builds canonical absolute URLs from the configured production origin", () => {
    process.env.APP_BASE_URL = "https://app.example.test";
    expect(publicMetadata("Titre", "Description", "/services").alternates?.canonical)
      .toBe("https://app.example.test/services");
  });

  it("includes only tariff-backed entities and genuinely available content routes", () => {
    process.env.APP_BASE_URL = "https://app.example.test";
    const sitemap = buildSitemap(content, {
      airports: [
        { public_id: "11111111-1111-4111-8111-111111111111", name: "Published", iata_code: "PUB", slug: "published", city: "Paris", country_code: "FR" },
        { public_id: "22222222-2222-4222-8222-222222222222", name: "Uncovered", iata_code: "UNC", slug: "uncovered", city: "Paris", country_code: "FR" },
      ],
      serviceAreas: [
        { public_id: "33333333-3333-4333-8333-333333333333", name: "Published zone", slug: "published-zone", area_type: "city", country_code: "FR", region: "", city: "Paris", description: "" },
      ],
      coverage: { routes: [{
        airport_id: "11111111-1111-4111-8111-111111111111",
        service_area_id: "33333333-3333-4333-8333-333333333333",
        trip_type: "airport_pickup",
        options: [],
      }] },
    });
    const urls = sitemap.map((entry) => entry.url);
    expect(urls).toContain("https://app.example.test/aeroports/published");
    expect(urls).toContain("https://app.example.test/zones-desservies/published-zone");
    expect(urls).toContain("https://app.example.test/services");
    expect(urls).not.toContain("https://app.example.test/aeroports/uncovered");
    expect(urls).not.toContain("https://app.example.test/faq");

    const emptyUrls = buildSitemap(content, { airports: [], serviceAreas: [], coverage: { routes: [] } })
      .map((entry) => entry.url);
    expect(emptyUrls).not.toContain("https://app.example.test/aeroports");
    expect(emptyUrls).not.toContain("https://app.example.test/zones-desservies");
    expect(emptyUrls).not.toContain("https://app.example.test/tarifs");
  });

  it("emits managed services in escaped structured data only with a published identity", () => {
    process.env.APP_BASE_URL = "https://app.example.test";
    const data = businessStructuredData(content.settings, content.services);
    expect(data).toMatchObject({ "@type": "Organization" });
    expect(JSON.stringify(data)).toContain("Accueil fictif");
    expect(
      businessStructuredData({ ...content.settings, phone: "", email: "", address: "" }, []),
    ).toBeNull();
    expect(serializeJsonLd({ value: "</script><script>alert(1)</script>" }))
      .not.toContain("</script>");
  });
});
