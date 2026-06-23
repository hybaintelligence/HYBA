import { describe, expect, it } from "vitest";
import { getFrontendBackendBaseUrl } from "../src/hooks/useLatencyMetrics";

describe("getFrontendBackendBaseUrl", () => {
  it("defaults browser health pings to the same-origin API bridge", () => {
    expect(getFrontendBackendBaseUrl()).toBe("/api");
  });
});
