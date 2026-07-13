import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ANALYTICS_CONSENT_KEY,
  AnalyticsPayloadError,
  setAnalyticsConsent,
  trackConversion,
} from "./analytics";

type TestWindow = {
  localStorage: Storage;
  dispatchEvent: ReturnType<typeof vi.fn>;
  dataLayer?: Array<Record<string, unknown>>;
};

function fakeStorage(): Storage {
  const values = new Map<string, string>();
  return {
    get length() { return values.size; },
    clear: () => values.clear(),
    getItem: (key) => values.get(key) ?? null,
    key: (index) => [...values.keys()][index] ?? null,
    removeItem: (key) => { values.delete(key); },
    setItem: (key, value) => { values.set(key, value); },
  };
}

describe("consent-aware analytics", () => {
  let browser: TestWindow;

  beforeEach(() => {
    browser = { localStorage: fakeStorage(), dispatchEvent: vi.fn() };
    vi.stubGlobal("window", browser);
    vi.stubGlobal("CustomEvent", class { constructor(public type: string, public init: unknown) {} });
  });

  it("does not dispatch before consent or after refusal", () => {
    expect(trackConversion("quote_started", { trip_type: "airport_pickup" })).toBe(false);
    setAnalyticsConsent("denied");
    expect(trackConversion("quote_started", { trip_type: "airport_pickup" })).toBe(false);
    expect(browser.dataLayer).toBeUndefined();
  });

  it("dispatches only an allow-listed event after consent", () => {
    setAnalyticsConsent("granted");
    expect(trackConversion("payment_succeeded", { provider: "stripe", currency: "EUR" })).toBe(true);
    expect(browser.dataLayer).toEqual([
      { event: "conversion_payment_succeeded", provider: "stripe", currency: "EUR" },
    ]);
  });

  it("rejects PII even when consent is absent", () => {
    expect(() => trackConversion("contact_submitted", { topic: "person@example.test" })).toThrow(AnalyticsPayloadError);
    expect(() => trackConversion("booking_created", { phone: "+33 6 00 00 00 00" })).toThrow(AnalyticsPayloadError);
  });

  it("rejects unknown properties and events", () => {
    expect(() => trackConversion("quote_created", { airport: "CDG" })).toThrow(AnalyticsPayloadError);
    expect(() => trackConversion("arbitrary" as "quote_created", {})).toThrow(AnalyticsPayloadError);
  });

  it("stores and broadcasts the explicit consent decision", () => {
    setAnalyticsConsent("granted");
    expect(browser.localStorage.getItem(ANALYTICS_CONSENT_KEY)).toBe("granted");
    expect(browser.dispatchEvent).toHaveBeenCalledOnce();
  });
});
