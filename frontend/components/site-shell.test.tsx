import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { primaryNavigation } from "@/lib/marketing-data";
import type { BusinessSettings } from "@/lib/public-content";

import { SiteFooter } from "./site-footer";
import { SiteHeader } from "./site-header";

const settings: BusinessSettings = {
  business_name: "Accueil Privé",
  tagline: "Un trajet organisé.",
  phone: "+33123456789",
  whatsapp_phone: "",
  email: "contact@example.test",
  support_hours: "",
  address: "",
  city: "",
  postal_code: "",
  country_code: "FR",
  booking_enabled: false,
  currency: "EUR",
  minimum_lead_hours: 12,
  maximum_booking_days: 365,
  quote_valid_minutes: 30,
};

describe("marketing shell", () => {
  it("renders every primary route as a real link", () => {
    const markup = renderToStaticMarkup(<SiteHeader settings={settings} />);

    for (const item of primaryNavigation) {
      expect(markup).toContain(`href="${item.href}"`);
    }
    expect(markup).toContain('aria-label="Navigation principale"');
    expect(markup).toContain('aria-label="Navigation mobile"');
  });

  it("renders configured contact channels and legal routes", () => {
    const markup = renderToStaticMarkup(<SiteFooter settings={settings} />);

    expect(markup).toContain("tel:+33123456789");
    expect(markup).toContain("mailto:contact@example.test");
    expect(markup).toContain('href="/mentions-legales"');
    expect(markup).not.toContain("WhatsApp");
  });
});
