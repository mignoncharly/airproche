import { afterEach, describe, expect, it, vi } from "vitest";

import { submitContact } from "./contact-api";

const input = {
  first_name: "Alice",
  last_name: "Martin",
  email: "alice@example.test",
  phone: "",
  topic: "booking" as const,
  message: "Je prépare un trajet fictif.",
  website: "",
  form_started_at: 1,
};

afterEach(() => vi.restoreAllMocks());

describe("submitContact", () => {
  it("uses CSRF and a caller-owned idempotency key", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ csrf_token: "csrf-test" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        public_id: "11111111-1111-4111-8111-111111111111",
        message: "Votre message a été reçu.",
        idempotent_replay: false,
      }), { status: 201 }));

    await submitContact(input, "contact-request-1");

    const request = fetchMock.mock.calls[1];
    expect(request[0]).toBe("/api/v1/contact/");
    expect(request[1]?.headers).toMatchObject({
      "Idempotency-Key": "contact-request-1",
      "X-CSRFToken": "csrf-test",
    });
  });

  it("does not send when CSRF initialization fails", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(null, { status: 503 }));

    await expect(submitContact(input, "contact-request-2")).rejects.toThrow(
      "formulaire est temporairement indisponible",
    );
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
