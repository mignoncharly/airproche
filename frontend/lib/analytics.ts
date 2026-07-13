export const ANALYTICS_CONSENT_KEY = "airproche_analytics_consent";

export type AnalyticsConsent = "granted" | "denied" | null;

const eventProperties = {
  quote_started: ["trip_type"],
  quote_created: ["trip_type", "currency"],
  booking_started: ["trip_type", "currency"],
  booking_created: ["trip_type", "currency"],
  payment_started: ["provider", "currency"],
  payment_succeeded: ["provider", "currency"],
  contact_submitted: ["topic"],
} as const;

export type ConversionEvent = keyof typeof eventProperties;
type SafeValue = string | number | boolean;
type ConversionProperties = Record<string, SafeValue>;

const forbiddenKey = /(address|authorization|card|cookie|email|first.?name|last.?name|name|passenger|phone|reference|session|token)/i;
const emailValue = /\b[^\s@]+@[^\s@]+\.[^\s@]+\b/;
const phoneValue = /(?:\+?\d[\s().-]*){8,}/;
const safePropertyValue: Record<string, (value: string) => boolean> = {
  trip_type: (value) => ["airport_pickup", "airport_dropoff"].includes(value),
  currency: (value) => /^[A-Z]{3}$/.test(value),
  provider: (value) => value === "stripe",
  topic: (value) => ["booking", "quote", "payment", "accessibility", "other"].includes(value),
};

export class AnalyticsPayloadError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AnalyticsPayloadError";
  }
}

export function getAnalyticsConsent(): AnalyticsConsent {
  if (typeof window === "undefined") return null;
  const value = window.localStorage.getItem(ANALYTICS_CONSENT_KEY);
  return value === "granted" || value === "denied" ? value : null;
}

export function subscribeAnalyticsConsent(listener: () => void): () => void {
  if (typeof window === "undefined") return () => undefined;
  window.addEventListener("airproche:analytics-consent", listener);
  window.addEventListener("storage", listener);
  return () => {
    window.removeEventListener("airproche:analytics-consent", listener);
    window.removeEventListener("storage", listener);
  };
}

export function setAnalyticsConsent(consent: Exclude<AnalyticsConsent, null>): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ANALYTICS_CONSENT_KEY, consent);
  window.dispatchEvent(new CustomEvent("airproche:analytics-consent", { detail: consent }));
}

function validateProperties(event: ConversionEvent, properties: ConversionProperties): ConversionProperties {
  const allowed = new Set<string>(eventProperties[event]);
  for (const [key, value] of Object.entries(properties)) {
    if (!allowed.has(key) || forbiddenKey.test(key)) {
      throw new AnalyticsPayloadError(`Analytics property is not allowed: ${key}`);
    }
    if (typeof value !== "string" || emailValue.test(value) || phoneValue.test(value)) {
      throw new AnalyticsPayloadError(`Analytics property contains personal data: ${key}`);
    }
    if (!safePropertyValue[key]?.(value)) {
      throw new AnalyticsPayloadError(`Analytics property value is not allowed: ${key}`);
    }
  }
  return properties;
}

export function trackConversion(
  event: ConversionEvent,
  properties: ConversionProperties = {},
): boolean {
  if (!Object.hasOwn(eventProperties, event)) {
    throw new AnalyticsPayloadError(`Analytics event is not allowed: ${event}`);
  }
  const safeProperties = validateProperties(event, properties);
  if (getAnalyticsConsent() !== "granted") return false;

  const target = window as typeof window & { dataLayer?: Array<Record<string, unknown>> };
  target.dataLayer ??= [];
  target.dataLayer.push({ event: `conversion_${event}`, ...safeProperties });
  return true;
}
