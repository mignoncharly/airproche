import { afterEach, describe, expect, it, vi } from "vitest";

import { currentAccount, loginAccount, requestPasswordReset } from "./auth-api";

const user = {
  public_id: "97c2f74e-922d-46c9-a991-c78251eb9968",
  email: "person@example.com",
  first_name: "Marie",
  last_name: "Martin",
  phone: "",
  preferred_locale: "fr",
  email_verified: true,
};

describe("authentication API client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("obtains a CSRF token before sending credentials", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ csrf_token: "csrf-value" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ user }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(loginAccount(user.email, "secret-password")).resolves.toEqual(user);
    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/v1/auth/csrf/", expect.objectContaining({ credentials: "same-origin" }));
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/v1/auth/login/", expect.objectContaining({ headers: expect.objectContaining({ "X-CSRFToken": "csrf-value" }) }));
  });

  it("treats an unauthorized current-user response as a signed-out state", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 403 })));
    await expect(currentAccount()).resolves.toBeNull();
  });

  it("preserves the backend safe error message", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ csrf_token: "csrf-value" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: { code: "throttled", message: "Réessayez plus tard.", fields: null } }), { status: 429 })));

    await expect(requestPasswordReset(user.email)).rejects.toMatchObject({
      status: 429,
      code: "throttled",
      message: "Réessayez plus tard.",
    });
  });
});
