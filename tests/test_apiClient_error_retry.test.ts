import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  authInterceptor,
  clearToken,
  getHealth,
  getSecurityStatus,
  setToken,
} from "../src/apiClient";

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    status: init.status ?? 200,
    headers: { "Content-Type": "application/json", ...(init.headers || {}) },
    statusText: init.statusText,
  });
}

describe("apiClient retry, auth, and error contracts", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    const storage = new Map<string, string>();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => { storage.set(key, value); },
      removeItem: (key: string) => { storage.delete(key); },
      clear: () => { storage.clear(); },
      key: vi.fn(),
      length: 0,
    });
    clearToken();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    clearToken();
  });

  it("adds JSON content-type and bearer token, but leaves FormData content-type to the browser", () => {
    setToken("contract-token");
    const jsonInit = authInterceptor({ headers: { "X-Request-ID": "rid-1" }, body: "{}" });
    const jsonHeaders = jsonInit.headers as Headers;
    expect(jsonHeaders.get("Authorization")).toBe("Bearer contract-token");
    expect(jsonHeaders.get("Content-Type")).toBe("application/json");
    expect(jsonHeaders.get("X-Request-ID")).toBe("rid-1");

    const formInit = authInterceptor({ body: new FormData() });
    const formHeaders = formInit.headers as Headers;
    expect(formHeaders.get("Authorization")).toBe("Bearer contract-token");
    expect(formHeaders.has("Content-Type")).toBe(false);
  });

  it("retries GET requests on 429/5xx and propagates request id from final API errors", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse({ error: "rate_limited", message: "slow down" }, { status: 429 }),
      )
      .mockResolvedValueOnce(
        jsonResponse({ error: "unavailable", message: "try later" }, { status: 503 }),
      )
      .mockResolvedValueOnce(
        jsonResponse(
          { error: "still_unavailable", message: "nope" },
          {
            status: 503,
            headers: { "x-request-id": "rid-final" },
          },
        ),
      )
      .mockResolvedValue(
        jsonResponse(
          { error: "still_unavailable", message: "nope" },
          {
            status: 503,
            headers: { "x-request-id": "rid-final" },
          },
        ),
      );

    await expect(getSecurityStatus()).rejects.toMatchObject({
      name: "HybaApiError",
      code: "still_unavailable",
      message: "nope",
      status: 503,
      requestId: "rid-final",
    });
    expect(fetchMock).toHaveBeenCalledTimes(4);
  });

  it("does not retry non-retriable 4xx responses", async () => {
    const fetchMock = vi
      .mocked(fetch)
      .mockResolvedValue(
        jsonResponse({ detail: { error: "forbidden", message: "denied" } }, { status: 403 }),
      );

    await expect(getHealth()).rejects.toMatchObject({ code: "forbidden", status: 403 });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("surfaces thrown network failures after retry budget is exhausted", async () => {
    const fetchMock = vi.mocked(fetch).mockRejectedValue(new TypeError("network offline"));
    await expect(getHealth()).rejects.toThrow("network offline");
    expect(fetchMock).toHaveBeenCalledTimes(4);
  });
});
