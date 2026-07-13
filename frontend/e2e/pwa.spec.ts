import { expect, test } from "@playwright/test";

test("manifest and icon assets are browser-readable", async ({ request }) => {
  const manifestResponse = await request.get("/manifest.webmanifest");
  expect(manifestResponse.ok()).toBeTruthy();
  const manifest = await manifestResponse.json();
  expect(manifest.display).toBe("standalone");
  expect(manifest.icons).toEqual(expect.arrayContaining([
    expect.objectContaining({ sizes: "192x192" }),
    expect.objectContaining({ sizes: "512x512" }),
  ]));
  const iconResponse = await request.get("/icons/icon-192.png");
  expect(iconResponse.ok()).toBeTruthy();
  expect(iconResponse.headers()["content-type"]).toContain("image/png");
});

test("offline navigation serves the generic fallback from the static cache", async ({ page, context }) => {
  await page.goto("/");
  await page.evaluate(async () => {
    await navigator.serviceWorker.ready;
  });

  const cachedUrls = await page.evaluate(async () => {
    const names = await caches.keys();
    const entries = await Promise.all(names.map(async (name) => {
      const cache = await caches.open(name);
      return Promise.all((await cache.keys()).map((request) => new URL(request.url).pathname));
    }));
    return entries.flat();
  });
  expect(cachedUrls.sort()).toEqual([
    "/icons/icon-192.png",
    "/icons/icon-512.png",
    "/icons/icon-maskable-512.png",
    "/offline",
  ].sort());
  expect(cachedUrls.some((url) => url.startsWith("/api/"))).toBeFalsy();

  await context.setOffline(true);
  await page.goto("/a-propos");
  await expect(page.getByRole("heading", { name: "Cette page n’est pas disponible sans réseau" })).toBeVisible();
});

test("offline and install surfaces do not overflow mobile or desktop viewports", async ({ page }) => {
  await page.goto("/offline");
  const dimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    content: document.documentElement.scrollWidth,
  }));
  expect(dimensions.content).toBeLessThanOrEqual(dimensions.viewport);
  await expect(page.getByRole("heading", { name: "Cette page n’est pas disponible sans réseau" })).toBeVisible();
});
