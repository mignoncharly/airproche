import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import OfflinePage, { metadata } from "./page";

describe("offline page", () => {
  it("is generic, responsive, and excluded from indexing", () => {
    const markup = renderToStaticMarkup(<OfflinePage />);
    expect(markup).toContain("Hors connexion");
    expect(markup).toContain("min-h-[65vh]");
    expect(markup).not.toContain("référence de réservation");
    expect(metadata.robots).toEqual({ index: false, follow: false });
  });
});
