import { afterEach, describe, expect, it, vi } from "vitest";

import {
  QuoteApiError,
  createQuote,
  formatMoney,
  getLocationsAndCoverage,
} from "./locations-pricing";

const airportId = "11111111-1111-4111-8111-111111111111";
const areaId = "22222222-2222-4222-8222-222222222222";

describe("locations and authoritative pricing boundary", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    delete process.env.BACKEND_INTERNAL_URL;
  });

  it("returns an honest empty coverage state without a backend", async () => {
    await expect(getLocationsAndCoverage()).resolves.toEqual({
      airports: [],
      serviceAreas: [],
      coverage: { routes: [] },
    });
  });

  it("validates and combines published location responses", async () => {
    process.env.BACKEND_INTERNAL_URL = "http://backend.test";
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string | URL | Request) => {
        const path = String(input);
        if (path.includes("airports")) {
          return new Response(JSON.stringify([{ public_id: airportId, name: "Aéroport Test", iata_code: "TST", slug: "test", city: "Paris", country_code: "FR" }]));
        }
        if (path.includes("service-areas")) {
          return new Response(JSON.stringify([{ public_id: areaId, name: "Zone Test", slug: "zone-test", area_type: "city", country_code: "FR", region: "", city: "Paris", description: "" }]));
        }
        return new Response(JSON.stringify({ routes: [{ airport_id: airportId, service_area_id: areaId, trip_type: "airport_pickup", options: [] }] }));
      }),
    );

    const result = await getLocationsAndCoverage();

    expect(result.airports[0].iata_code).toBe("TST");
    expect(result.serviceAreas[0].slug).toBe("zone-test");
    expect(result.coverage.routes[0].airport_id).toBe(airportId);
  });

  it("submits route facts without any client-controlled amount", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          public_id: "33333333-3333-4333-8333-333333333333",
          trip_type: "airport_pickup",
          airport_name: "Aéroport Test",
          airport_iata_code: "TST",
          service_area_name: "Zone Test",
          pickup_at: "2026-08-01T12:00:00Z",
          passenger_count: 2,
          luggage_count: 1,
          total_amount: "80.00",
          currency: "EUR",
          calculation_version: "fixed-zone-v1",
          status: "valid",
          expires_at: "2026-07-13T16:30:00Z",
          lines: [{ code: "base-fare", label: "Trajet", quantity: 1, unit_amount: "80.00", total_amount: "80.00" }],
        }),
        { status: 201 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const quote = await createQuote({
      trip_type: "airport_pickup",
      airport_id: airportId,
      service_area_id: areaId,
      pickup_at: "2026-08-01T12:00:00Z",
      passenger_count: 2,
      luggage_count: 1,
      options: [],
    });

    const request = fetchMock.mock.calls[0][1] as RequestInit;
    expect(JSON.parse(String(request.body))).not.toHaveProperty("total_amount");
    expect(quote.total_amount).toBe("80.00");
    expect(formatMoney(quote.total_amount, quote.currency)).toContain("80,00");
  });

  it("preserves stable backend error codes for recovery UI", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ error: { code: "capacity", message: "Vérification manuelle.", fields: null } }),
          { status: 422 },
        ),
      ),
    );

    await expect(
      createQuote({
        trip_type: "airport_pickup",
        airport_id: airportId,
        service_area_id: areaId,
        pickup_at: "2026-08-01T12:00:00Z",
        passenger_count: 9,
        luggage_count: 1,
        options: [],
      }),
    ).rejects.toEqual(expect.objectContaining<Partial<QuoteApiError>>({ code: "capacity", status: 422 }));
  });
});
