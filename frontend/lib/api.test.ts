import { afterEach, describe, expect, it, vi } from "vitest";

import { getBackendHealth } from "./api";

describe("getBackendHealth", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    delete process.env.BACKEND_INTERNAL_URL;
  });

  it("validates a healthy backend response", async () => {
    process.env.BACKEND_INTERNAL_URL = "http://backend.test/";
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "ok" }), { status: 200 })),
    );

    await expect(getBackendHealth()).resolves.toEqual({ status: "ok" });
    expect(fetch).toHaveBeenCalledWith("http://backend.test/api/v1/health/live/", {
      cache: "no-store",
      headers: { "X-Forwarded-Proto": "https" },
    });
  });

  it("rejects malformed responses", async () => {
    process.env.BACKEND_INTERNAL_URL = "http://backend.test";
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "secret-data" }), { status: 200 })),
    );

    await expect(getBackendHealth()).rejects.toThrow();
  });
});

