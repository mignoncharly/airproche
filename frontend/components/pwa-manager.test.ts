import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const source = readFileSync(
  fileURLToPath(new URL("./pwa-manager.tsx", import.meta.url)),
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

  it("uses a bounded responsive install surface", () => {
    expect(source).toContain("inset-x-3");
    expect(source).toContain("max-w-xl");
    expect(source).toContain("flex flex-wrap");
  });
});
