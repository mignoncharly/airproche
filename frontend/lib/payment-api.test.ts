import { afterEach, describe, expect, it, vi } from "vitest";

import { getPaymentStatus } from "./payment-api";

afterEach(() => vi.unstubAllGlobals());

describe("payment status credentials", () => {
  it("sends the Checkout session in a header, never in the logged URL", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      public_id: "11111111-1111-4111-8111-111111111111",
      booking_public_id: "22222222-2222-4222-8222-222222222222",
      booking_reference: "TR-FICTIONAL",
      booking_status: "pending_payment",
      provider: "stripe",
      status: "pending",
      amount: "80.00",
      currency: "EUR",
      environment: "test",
      paid_at: null,
      last_error_code: null,
      last_error_message: null,
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);

    await getPaymentStatus("22222222-2222-4222-8222-222222222222", "cs_fictional");
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).not.toContain("cs_fictional");
    expect(url).not.toContain("session_id");
    expect(options.headers).toMatchObject({ "X-Checkout-Session": "cs_fictional" });
  });
});
