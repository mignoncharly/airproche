import { expect, test } from "@playwright/test";

import budgets from "../performance-budgets.json";

test("public shell stays within the mobile performance budget", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile-chromium", "The release budget targets a realistic mobile viewport.");

  await page.addInitScript(() => {
    (window as typeof window & { __layoutShift?: number }).__layoutShift = 0;
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries() as Array<PerformanceEntry & { hadRecentInput?: boolean; value?: number }>) {
        if (!entry.hadRecentInput) {
          (window as typeof window & { __layoutShift: number }).__layoutShift += entry.value ?? 0;
        }
      }
    }).observe({ type: "layout-shift", buffered: true });
  });
  await page.goto("/", { waitUntil: "load" });
  await page.waitForTimeout(250);

  const metrics = await page.evaluate(() => {
    const navigation = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming;
    const javascriptTransferBytes = performance
      .getEntriesByType("resource")
      .filter((entry) => entry.name.includes("/_next/static/") && entry.name.endsWith(".js"))
      .reduce((total, entry) => total + (entry as PerformanceResourceTiming).transferSize, 0);
    return {
      domContentLoadedMs: navigation.domContentLoadedEventEnd,
      loadMs: navigation.loadEventEnd,
      javascriptTransferBytes,
      cumulativeLayoutShift: (window as typeof window & { __layoutShift?: number }).__layoutShift ?? 0,
      viewportWidth: document.documentElement.clientWidth,
      contentWidth: document.documentElement.scrollWidth,
    };
  });

  expect(metrics.domContentLoadedMs).toBeLessThanOrEqual(budgets.mobile.domContentLoadedMs);
  expect(metrics.loadMs).toBeLessThanOrEqual(budgets.mobile.loadMs);
  expect(metrics.javascriptTransferBytes).toBeLessThanOrEqual(budgets.mobile.javascriptTransferBytes);
  expect(metrics.cumulativeLayoutShift).toBeLessThanOrEqual(budgets.mobile.cumulativeLayoutShift);
  expect(metrics.contentWidth).toBeLessThanOrEqual(metrics.viewportWidth);
});
