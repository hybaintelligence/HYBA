import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  clearToken,
  createAdminUser,
  deleteAdminUser,
  disburseFunding,
  reviewFundingRequest,
  setToken,
  updateAdminUser,
} from "../src/apiClient";

const success = () =>
  new Response(JSON.stringify({ id: 1, status: "ok" }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });

describe("apiClient admin and funding command contracts", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(success()));
    setToken("admin-token");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    clearToken();
  });

  it("sends admin mutations with bearer auth and maxRetries=0 semantics", async () => {
    await createAdminUser({
      username: "new-admin",
      email: "admin@example.com",
      password: "safe-test-password",
      role: "admin",
    });
    await updateAdminUser(7, { is_active: false });
    await deleteAdminUser(7);
    await disburseFunding(42);
    await reviewFundingRequest("req-1", { status: "approved", approval_notes: "sandbox approval" });

    const calls = vi.mocked(fetch).mock.calls.map(([url, init]) => ({
      url,
      method: (init as RequestInit).method,
      headers: (init as RequestInit).headers as Headers,
      body: (init as RequestInit).body ? JSON.parse(String((init as RequestInit).body)) : undefined,
    }));

    expect(calls.map((call) => [call.method, call.url])).toEqual([
      ["POST", "/api/admin/users"],
      ["PUT", "/api/admin/users/7"],
      ["DELETE", "/api/admin/users/7"],
      ["POST", "/api/admin/funding/allocations/42/disburse"],
      ["PUT", "/api/admin/funding/requests/req-1/review"],
    ]);
    for (const call of calls) expect(call.headers.get("Authorization")).toBe("Bearer admin-token");
    expect(calls[4].body).toEqual({ status: "approved", approval_notes: "sandbox approval" });
  });

  it("does not retry destructive admin calls on backend 5xx", async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ error: "server_error" }), { status: 500 }),
    );

    await expect(deleteAdminUser(99)).rejects.toMatchObject({ status: 500 });
    await expect(disburseFunding(42)).rejects.toMatchObject({ status: 500 });
    await expect(reviewFundingRequest("req-2", { status: "rejected" })).rejects.toMatchObject({
      status: 500,
    });
    expect(fetch).toHaveBeenCalledTimes(3);
  });
});
