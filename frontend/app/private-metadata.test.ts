import { describe, expect, it } from "vitest";

import { metadata as account } from "./compte/page";
import { metadata as operations } from "./operations/page";
import { metadata as payment } from "./paiement/retour/page";
import { metadata as booking } from "./reservation/page";

describe("private page indexing", () => {
  it.each([
    ["account", account],
    ["operations", operations],
    ["booking", booking],
    ["payment", payment],
  ])("marks %s as noindex and nofollow", (_name, metadata) => {
    expect(metadata.robots).toEqual({ index: false, follow: false });
  });
});
