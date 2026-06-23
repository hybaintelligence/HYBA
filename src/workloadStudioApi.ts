type CustomerCIAASService = {
  service_id: string;
  name?: string;
  state?: "provisioned" | "running" | "stopped" | string;
  service_tier?: string;
  tenancy?: string;
  evidence_seal?: string;
  claim_boundary?: string;
  usage?: Record<string, unknown>;
};

type CustomerWorkloadRequest = {
  workload_type: "explain" | "orchestrate" | "counterfactual" | "governance_audit" | "substrate_health";
  context: Record<string, unknown>;
  substrates?: Array<"penrose_or" | "iit_4" | "deutsch">;
  idempotency_key?: string;
};

const BACKEND_URL = "/api";
const TOKEN_KEY = "hyba_auth_token";
export const CUSTOMER_API_KEY_STORAGE = "hyba_customer_api_key";

/**
 * SECURITY SCOPE: hyba_customer_api_key is stored in localStorage for CIaaS
 * Workload Studio demo activation only. This keeps a buyer out of DevTools
 * during a controlled demo, but it is not the intended production custody
 * model for customer data handling.
 *
 * Threat model: XSS on this origin can expose the key. Production deployments
 * must migrate to HttpOnly cookies or server-side session custody before broad
 * customer data handling. Complementary controls should include CSP headers,
 * short-lived/rotated keys, and immediate key revocation from the customer
 * portal after each demo session.
 */
export const CUSTOMER_API_KEY_ALIASES = [
  CUSTOMER_API_KEY_STORAGE,
  "hyba_api_key",
  "ciass_api_key",
] as const;

export function getStoredCustomerApiKey(): string {
  try {
    for (const key of CUSTOMER_API_KEY_ALIASES) {
      const value = localStorage.getItem(key);
      if (value?.trim()) return value.trim();
    }
  } catch {
    // localStorage can be unavailable under SSR/test shells.
  }
  return "";
}

export function setStoredCustomerApiKey(apiKey: string): void {
  try {
    if (apiKey.trim()) {
      localStorage.setItem(CUSTOMER_API_KEY_STORAGE, apiKey.trim());
    } else {
      localStorage.removeItem(CUSTOMER_API_KEY_STORAGE);
    }
  } catch {
    // noop; callers still pass the key in memory for the current session.
  }
}

function buildCustomerHeaders(apiKeyOverride?: string): Headers {
  const headers = new Headers();
  headers.set("Content-Type", "application/json");
  const apiKey = apiKeyOverride?.trim() || getStoredCustomerApiKey();
  if (apiKey) {
    // Public CIaaS routes require X-API-Key. Keep X-HYBA-API-Key as a harmless
    // compatibility header for older examples and customer snippets.
    headers.set("X-API-Key", apiKey);
    headers.set("X-HYBA-API-Key", apiKey);
  }
  try {
    const bearer = localStorage.getItem(TOKEN_KEY);
    if (bearer) headers.set("Authorization", `Bearer ${bearer}`);
  } catch {
    // noop
  }
  return headers;
}

async function customerRequest<T>(
  path: string,
  init: RequestInit,
  apiKeyOverride?: string,
): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: buildCustomerHeaders(apiKeyOverride),
  });
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || body.message || detail;
    } catch {
      // keep HTTP status fallback
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return response.json() as Promise<T>;
}

export async function listCustomerCIAASServicesForStudio(
  apiKeyOverride?: string,
): Promise<CustomerCIAASService[]> {
  return customerRequest<CustomerCIAASService[]>(
    "/v1/computational-intelligence-services",
    { method: "GET" },
    apiKeyOverride,
  );
}

export async function executeCustomerCIAASWorkloadForStudio(
  serviceId: string,
  request: CustomerWorkloadRequest,
  apiKeyOverride?: string,
): Promise<Record<string, unknown>> {
  return customerRequest<Record<string, unknown>>(
    `/v1/computational-intelligence-services/${serviceId}/execute`,
    { method: "POST", body: JSON.stringify(request) },
    apiKeyOverride,
  );
}
