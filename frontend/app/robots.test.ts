import { describe, expect, it } from "vitest";

import robots from "./robots";

describe("robots metadata", () => {
  it("publishes the sitemap and blocks private and API routes", () => {
    const result = robots();
    expect(result.sitemap).toMatch(/\/sitemap\.xml$/);
    expect(result.rules).toEqual(expect.objectContaining({
      userAgent: "*",
      allow: "/",
      disallow: expect.arrayContaining(["/api/", "/compte", "/operations", "/reservation", "/paiement"]),
    }));
  });
});
