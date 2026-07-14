import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const source = readFileSync(
  fileURLToPath(new URL("./pwa-manager.tsx", import.meta.url)),
  "utf8",
);
const layoutSource = readFileSync(
  fileURLToPath(new URL("../app/layout.tsx", import.meta.url)),
  "utf8",
);

describe("PWA install and update UI", () => {
  it("uses the supported Android install prompt and accurate iOS Safari steps", () => {
    expect(source).toContain('"beforeinstallprompt"');
    expect(source).toContain("installPrompt.prompt()");
    expect(source).toContain("Ouvrez cette page dans Safari");
    expect(source).toContain("Sur l’écran d’accueil");
  });

  it("reloads only after an explicit waiting-worker update action", () => {
    expect(source).toContain('postMessage({ type: "SKIP_WAITING" })');
    expect(source).toContain('addEventListener("controllerchange"');
    expect(source).toContain("if (refreshRequested.current) window.location.reload()");
    expect(source).not.toContain("registration.skipWaiting");
  });

  it("offers an accessible page-instance dismissal that resets after refresh", () => {
    expect(source).not.toContain("sessionStorage");
    expect(source).toContain("setNoticeDismissed(true)");
    expect(source).toContain("noticeDismissed ||");
    expect(source).toContain('aria-label="Fermer la proposition d’installation"');
    expect(source).toContain('<Icon name="close"');
  });

  it("shares a bounded responsive notice stack without covering consent controls", () => {
    expect(layoutSource).toContain("fixed inset-x-3 bottom-3");
    expect(layoutSource).toContain("flex flex-col items-end gap-3");
    expect(layoutSource).toContain("sm:w-[min(36rem");
    expect(layoutSource.indexOf("<AnalyticsConsentBanner />"))
      .toBeLessThan(layoutSource.indexOf("<PwaManager />"));
    expect(source).toContain("pointer-events-auto w-full max-w-xl rounded-2xl");
    expect(source).toContain("flex flex-wrap");
  });
});
