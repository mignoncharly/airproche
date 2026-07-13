import { describe, expect, it } from "vitest";

import { parseSensitiveFragment } from "./sensitive-fragment";

describe("sensitive URL fragments", () => {
  it("parses encoded credentials without placing them in a query", () => {
    const params = parseSensitiveFragment("#token=fictional%2Btoken&reference=TR-FICTIONAL");
    expect(params.get("token")).toBe("fictional+token");
    expect(params.get("reference")).toBe("TR-FICTIONAL");
  });
});
