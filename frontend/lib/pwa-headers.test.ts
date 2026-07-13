import { describe, expect, it } from "vitest";

import nextConfig from "../next.config";

describe("PWA response headers", () => {
  it("prevents stale service-worker scripts", async () => {
    const rules = await nextConfig.headers?.();
    const worker = rules?.find((rule) => rule.source === "/sw.js");
    expect(worker?.headers).toEqual(expect.arrayContaining([
      { key: "Cache-Control", value: "no-cache, no-store, must-revalidate" },
      { key: "Service-Worker-Allowed", value: "/" },
    ]));
  });
});
