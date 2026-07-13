import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const source = readFileSync(
  fileURLToPath(new URL("../public/sw.js", import.meta.url)),
  "utf8",
);

describe("service worker policy", () => {
  it("pre-caches only the explicit static allow-list without credentials", () => {
    expect(source).toContain("const STATIC_ASSETS");
    expect(source).toContain('credentials: "omit"');
    const staticList = source.slice(
      source.indexOf("const STATIC_ASSETS"),
      source.indexOf("const SENSITIVE_PREFIXES"),
    );
    expect(staticList).not.toContain("/api/");
  });

  it("never runtime-caches API or private application paths", () => {
    for (const path of ["/api/", "/compte", "/operations", "/reservation", "/paiement"]) {
      expect(source).toContain(path);
    }
    expect(source).not.toContain("response.clone()");
    expect(source).not.toContain("authorization");
    expect(source).not.toContain("cookie");
  });

  it("uses a generic offline fallback and explicit update activation", () => {
    expect(source).toContain('caches.match("/offline")');
    expect(source).toContain('event.data?.type === "SKIP_WAITING"');
    expect(source.indexOf("self.skipWaiting()")).toBeGreaterThan(
      source.indexOf('event.data?.type === "SKIP_WAITING"'),
    );
  });
});
