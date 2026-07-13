import { describe, expect, it } from "vitest";

import nextConfig, { contentSecurityPolicy } from "../next.config";

describe("production browser security headers", () => {
  it("locks framing, plugins, base URLs, workers, and network destinations", () => {
    expect(contentSecurityPolicy).toContain("default-src 'self'");
    expect(contentSecurityPolicy).toContain("base-uri 'self'");
    expect(contentSecurityPolicy).toContain("object-src 'none'");
    expect(contentSecurityPolicy).toContain("frame-ancestors 'none'");
    expect(contentSecurityPolicy).toContain("connect-src 'self'");
    expect(contentSecurityPolicy).toContain("worker-src 'self'");
    expect(contentSecurityPolicy).not.toContain("*");
    expect(contentSecurityPolicy).not.toContain("https:");
  });

  it("keeps the standard browser hardening headers on every route", async () => {
    const declarations = await nextConfig.headers?.();
    const allRoutes = declarations?.find((entry) => entry.source === "/:path*");
    const names = allRoutes?.headers.map((header) => header.key);
    expect(names).toEqual(expect.arrayContaining([
      "X-Content-Type-Options",
      "Referrer-Policy",
      "X-Frame-Options",
      "Cross-Origin-Opener-Policy",
      "Cross-Origin-Resource-Policy",
      "Permissions-Policy",
    ]));
  });
});
