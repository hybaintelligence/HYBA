import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("AI Assistant governance header", () => {
  it("surfaces the no-unattended-writes control for client UAT", () => {
    const source = readFileSync("src/components/AIAssistant.tsx", "utf8");
    expect(source).toContain("No-Unattended-Writes");
    expect(source).toMatch(/Human\s+approval required/);
    expect(source).toContain("commands are blocked until");
  });
});
