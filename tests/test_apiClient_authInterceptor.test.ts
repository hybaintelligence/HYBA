import { describe, it, expect, vi } from "vitest";
import { authInterceptor } from "../src/apiClient";

/**
 * Unit tests for the authInterceptor. These ensure that default headers are set
 * correctly and that the Authorization header is attached when a token is present.
 */

describe("authInterceptor", () => {
  it("sets the Content-Type header to application/json when none is provided and body is not FormData", () => {
    const reqInit = authInterceptor({});
    expect(reqInit.headers instanceof Headers).toBe(true);
    const headers = reqInit.headers as Headers;
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("does not override Content-Type if it is already set or body is FormData", () => {
    // pre-existing header
    const req1 = authInterceptor({ headers: { "Content-Type": "text/plain" } });
    expect((req1.headers as Headers).get("Content-Type")).toBe("text/plain");

    // FormData should not set Content-Type automatically
    const formData = new FormData();
    const req2 = authInterceptor({ body: formData });
    expect((req2.headers as Headers).has("Content-Type")).toBe(false);
  });

  it("attaches Authorization header when a token is present in localStorage", () => {
    const token = "testToken123";
    // stub localStorage via vi.stubGlobal
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => (key === "hyba_auth_token" ? token : null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
    const req = authInterceptor({});
    const headers = req.headers as Headers;
    expect(headers.get("Authorization")).toBe(`Bearer ${token}`);
  });
});
