import { z } from "zod";

const healthSchema = z.object({ status: z.literal("ok") });

function serverApiBase(): string {
  const value = process.env.BACKEND_INTERNAL_URL;
  if (!value) {
    throw new Error("BACKEND_INTERNAL_URL is required for server-side API calls.");
  }
  return value.replace(/\/$/, "");
}

export async function getBackendHealth(): Promise<{ status: "ok" }> {
  const response = await fetch(`${serverApiBase()}/api/v1/health/live/`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Backend health request failed with status ${response.status}.`);
  }
  return healthSchema.parse(await response.json());
}

