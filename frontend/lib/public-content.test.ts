import { afterEach, describe, expect, it, vi } from "vitest";

import { getPublicContent, phoneHref, publicContentSchema, whatsappHref } from "./public-content";

describe("public content boundary", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    delete process.env.BACKEND_INTERNAL_URL;
  });

  it("returns an honest non-bookable state when the backend URL is absent", async () => {
    await expect(getPublicContent()).resolves.toMatchObject({
      settings: { booking_enabled: false },
      services: [],
      faqs: [],
      testimonials: [],
      legal_documents: [],
    });
  });

  it("rejects unverified API shapes instead of trusting them", () => {
    expect(() => publicContentSchema.parse({ settings: { booking_enabled: "yes" } })).toThrow();
  });

  it("normalizes public contact links", () => {
    expect(phoneHref("+33 (0)1 23 45 67 89")).toBe("tel:+330123456789");
    expect(whatsappHref("+33 6 12 34 56 78")).toBe("https://wa.me/33612345678");
  });
});
