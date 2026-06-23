export class HYBAServiceError extends Error {}
export class HYBAAuthError extends HYBAServiceError {}
export class HYBARateLimitError extends HYBAServiceError {}
export class HYBAQuotaExhaustedError extends HYBAServiceError {}

type Json = Record<string, unknown>;

export class HYBAClient {
  public qaas: { execute: (circuitSpec: Json) => Promise<Json> };
  public qiaas: { predict: (payload: Json) => Promise<Json> };
  public finance: { portfolioOptimize: (weights: number[], constraints: Json) => Promise<Json> };

  constructor(
    private apiKey: string,
    private baseUrl = "https://api.hyba.ai",
  ) {
    if (!apiKey) throw new HYBAAuthError("apiKey is required");
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.qaas = { execute: async (circuitSpec) => this.executeQaaS(circuitSpec) };
    this.qiaas = {
      predict: async (payload) =>
        this.request("POST", "/api/qiaas/query", { query_type: "predict", context: payload }),
    };
    this.finance = {
      portfolioOptimize: async (weights, constraints) =>
        this.portfolioOptimize(weights, constraints),
    };
  }

  private async executeQaaS(circuitSpec: Json): Promise<Json> {
    const computerId = circuitSpec.computer_id as string | undefined;
    const payload = { ...circuitSpec };
    delete payload.computer_id;
    if (computerId)
      return this.request(
        "POST",
        `/api/v1/fault-tolerant-computers/${computerId}/execute`,
        payload,
      );
    const computer = await this.request("POST", "/api/v1/fault-tolerant-computers", {
      name: "sdk-computer",
    });
    await this.request("POST", `/api/v1/fault-tolerant-computers/${computer.computer_id}/start`);
    return this.request(
      "POST",
      `/api/v1/fault-tolerant-computers/${computer.computer_id}/execute`,
      Object.keys(payload).length ? payload : { operation: "surface_code_cycle" },
    );
  }

  private async portfolioOptimize(weights: number[], constraints: Json): Promise<Json> {
    const n = weights.length;
    const covariance =
      constraints.covariance_matrix ??
      Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => (i === j ? 1 : 0)));
    return this.request("POST", "/api/quantum-finance/portfolio/qaoa-design", {
      expected_returns: weights,
      covariance_matrix: covariance,
      budget: 1,
      ...constraints,
    });
  }

  private async request(method: string, path: string, body?: unknown): Promise<Json> {
    for (let attempt = 0; attempt < 4; attempt++) {
      const response = await fetch(this.baseUrl + path, {
        method,
        headers: {
          "X-API-Key": this.apiKey,
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      if (response.status === 429 && attempt < 3) {
        await new Promise((r) => setTimeout(r, Math.min(2 ** attempt, 8) * 1000));
        continue;
      }
      const text = await response.text();
      if (response.status === 401 || response.status === 403) throw new HYBAAuthError(text);
      if (response.status === 429) throw new HYBARateLimitError(text);
      if (response.status === 402) throw new HYBAQuotaExhaustedError(text);
      if (!response.ok) throw new HYBAServiceError(text);
      return text ? JSON.parse(text) : {};
    }
    throw new HYBARateLimitError("rate limit retry budget exhausted");
  }
}
