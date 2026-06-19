import React from "react";
import { renderToString } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import App from "../src/App";
import * as apiClient from "../src/apiClient";
import { ErrorBoundary } from "../src/components/ErrorBoundary";

class RenderFailure extends React.Component {
  render() {
    throw new Error("component integration sentinel");
  }
}

const createStorage = () => {
  const values = new Map<string, string>();
  return {
    getItem: vi.fn((key: string) => values.get(key) ?? null),
    setItem: vi.fn((key: string, value: string) => values.set(key, value)),
    removeItem: vi.fn((key: string) => values.delete(key)),
    clear: vi.fn(() => values.clear()),
  };
};

describe("HYBA Frontend Components", () => {
  it("App component renders the operator console shell without throwing", () => {
    vi.stubGlobal("localStorage", createStorage());

    const html = renderToString(React.createElement(App));

    expect(html).toContain("HYBA");
    expect(html).toContain("Operator");
    vi.unstubAllGlobals();
  });

  it("apiClient exports frontend integration endpoint functions", () => {
    const expectedExports = [
      "fetchTelemetryData",
      "fetchPoolConfig",
      "connectToPool",
      "configurePool",
      "switchPool",
      "disconnectFromPool",
      "pauseMining",
      "resumeMining",
      "loginApi",
      "registerApi",
      "fetchProfileApi",
      "fetchProductsApi",
      "authInterceptor",
      "getToken",
      "setToken",
      "clearToken",
    ];

    for (const exportName of expectedExports) {
      expect(apiClient[exportName as keyof typeof apiClient], exportName).toEqual(
        expect.any(Function),
      );
    }
  });

  it("ErrorBoundary derives fallback state with the rendering error message", () => {
    const error = new Error("component integration sentinel");
    const state = ErrorBoundary.getDerivedStateFromError(error);
    const boundary = new ErrorBoundary({ children: React.createElement(RenderFailure) });
    boundary.setState = vi.fn();
    boundary.state = state;

    const html = renderToString(boundary.render() as React.ReactElement);

    expect(state.hasError).toBe(true);
    expect(html).toContain("Substrate Interface Discontinuity");
    expect(html).toContain("component integration sentinel");
  });

  it("auth token helpers integrate with the auth interceptor", () => {
    const storage = createStorage();
    vi.stubGlobal("localStorage", storage);

    apiClient.setToken("frontend-token-123");
    const intercepted = apiClient.authInterceptor({ headers: { "X-Test": "true" } });
    const headers = intercepted.headers as Headers;

    expect(apiClient.getToken()).toBe("frontend-token-123");
    expect(headers.get("Authorization")).toBe("Bearer frontend-token-123");
    expect(headers.get("Content-Type")).toBe("application/json");
    apiClient.clearToken();
    expect(apiClient.getToken()).toBeNull();
    vi.unstubAllGlobals();
  });
});
