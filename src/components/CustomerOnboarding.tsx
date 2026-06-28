/**
 * Customer Onboarding Flow
 *
 * Self-service activation for CIaaS. The key moment is not a canned demo;
 * it is a buyer generating access, bringing a workload, and inspecting the
 * transformation packet returned by the live API path.
 */

import React, { useState } from "react";
import { AlertTriangle, CheckCircle2, Code, Rocket, Zap, X } from "lucide-react";
import { setStoredCustomerApiKey } from "../workloadStudioApi";

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  action: string;
  completed: boolean;
}

type ApiKeyProvisionResponse = {
  key_id: string;
  api_key: string;
  label: string;
  created_at: string;
  status: string;
};

function readLocalStorage(keys: string[], fallback = "") {
  try {
    for (const key of keys) {
      const value = localStorage.getItem(key);
      if (value?.trim()) return value.trim();
    }
  } catch {
    // localStorage may be unavailable in SSR/test shells.
  }
  return fallback;
}

async function provisionCustomerApiKey(): Promise<ApiKeyProvisionResponse> {
  const tenantId = readLocalStorage(
    ["hyba_customer_tenant_id", "hyba_tenant_id", "hyba_customer_id"],
    "demo-customer",
  );
  const portalToken = readLocalStorage(["hyba_customer_portal_token", "hyba_portal_token"]);
  const headers = new Headers({ "Content-Type": "application/json", "X-HYBA-Tenant-ID": tenantId });
  if (portalToken) headers.set("X-HYBA-Customer-Token", portalToken);

  const response = await fetch(`/api/customer/${encodeURIComponent(tenantId)}/api-keys`, {
    method: "POST",
    headers,
    body: JSON.stringify({ label: "Workload Studio demo key", rotation_days: 1 }),
  });
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || body.message || detail;
    } catch {
      // keep status fallback
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return response.json() as Promise<ApiKeyProvisionResponse>;
}

function launchWorkloadStudio(onComplete: () => void) {
  try {
    localStorage.setItem("hyba_onboarding_completed", "true");
  } catch {
    // noop
  }
  onComplete();
  window.location.href = "/workload-studio";
}

export function CustomerOnboarding({ onComplete }: { onComplete: () => void }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [apiKeyId, setApiKeyId] = useState<string | null>(null);
  const [isProvisioningKey, setIsProvisioningKey] = useState(false);
  const [provisioningError, setProvisioningError] = useState<string | null>(null);

  const steps: OnboardingStep[] = [
    {
      id: "welcome",
      title: "Welcome to HYBA CIaaS",
      description:
        "Computational Intelligence as a Service. Bring a workload, run the API, inspect the transformation packet.",
      action: "Get Started",
      completed: false,
    },
    {
      id: "provision",
      title: "Provision Your CIaaS Rail",
      description:
        "Choose the intelligence runtime that will transform your workload with evidence boundaries.",
      action: "Provision",
      completed: false,
    },
    {
      id: "api_key",
      title: "Generate API Key",
      description: "Create a short-lived customer key and hand it directly to Workload Studio.",
      action: "Generate Key",
      completed: false,
    },
    {
      id: "quick_win",
      title: "Bring Your Workload",
      description:
        "Launch Workload Studio with your key already available for live CIaaS execution.",
      action: "Open Workload Studio",
      completed: false,
    },
  ];

  const handleNext = async () => {
    setProvisioningError(null);
    if (currentStep === 2 && !apiKey) {
      setIsProvisioningKey(true);
      try {
        const response = await provisionCustomerApiKey();
        setApiKey(response.api_key);
        setApiKeyId(response.key_id);
        setStoredCustomerApiKey(response.api_key);
        setCurrentStep(3);
      } catch (error) {
        setProvisioningError(
          error instanceof Error
            ? error.message
            : "Could not generate a customer API key for Workload Studio",
        );
      } finally {
        setIsProvisioningKey(false);
      }
      return;
    }

    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      launchWorkloadStudio(onComplete);
    }
  };

  const currentStepData = steps[currentStep];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/90 backdrop-blur-sm">
      <div className="relative w-full max-w-3xl rounded-2xl border border-slate-700 bg-slate-900 p-8 shadow-2xl">
        <button
          onClick={onComplete}
          className="absolute right-4 top-4 rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="mb-8 flex items-center justify-between">
          {steps.map((step, idx) => (
            <React.Fragment key={step.id}>
              <div className="flex flex-col items-center">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full border-2 ${
                    idx <= currentStep
                      ? "border-blue-500 bg-blue-500 text-white"
                      : "border-slate-600 bg-slate-800 text-slate-400"
                  }`}
                >
                  {idx < currentStep ? (
                    <CheckCircle2 className="h-5 w-5" />
                  ) : (
                    <span>{idx + 1}</span>
                  )}
                </div>
                <span className="mt-2 text-xs text-slate-400">{step.title}</span>
              </div>
              {idx < steps.length - 1 && (
                <div
                  className={`h-0.5 flex-1 ${idx < currentStep ? "bg-blue-500" : "bg-slate-700"}`}
                />
              )}
            </React.Fragment>
          ))}
        </div>

        <div className="min-h-[300px]">
          {currentStep === 0 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <Rocket className="h-8 w-8 text-blue-500" />
                <h2 className="text-2xl font-bold text-white">{currentStepData.title}</h2>
              </div>
              <p className="text-lg text-slate-300">{currentStepData.description}</p>

              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
                  <h3 className="mb-2 font-bold text-white">CIaaS</h3>
                  <p className="text-sm text-slate-400">
                    Computational intelligence runtime and evidence packet.
                  </p>
                </div>
                <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
                  <h3 className="mb-2 font-bold text-white">Evidence Boundary</h3>
                  <p className="text-sm text-slate-400">
                    Trace, provenance, limitations, and human approval preserved.
                  </p>
                </div>
                <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
                  <h3 className="mb-2 font-bold text-white">Workload Studio</h3>
                  <p className="text-sm text-slate-400">
                    Bring risk, board, incident, or audit artifacts.
                  </p>
                </div>
                <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
                  <h3 className="mb-2 font-bold text-white">Buyer Proof</h3>
                  <p className="text-sm text-slate-400">
                    Run the API and export the packet for review.
                  </p>
                </div>
              </div>
            </div>
          )}

          {currentStep === 1 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <Zap className="h-8 w-8 text-blue-500" />
                <h2 className="text-2xl font-bold text-white">{currentStepData.title}</h2>
              </div>
              <p className="text-lg text-slate-300">{currentStepData.description}</p>

              <div className="space-y-3">
                {[
                  "CIaaS: Risk register transformation",
                  "CIaaS: Board memo counterfactual review",
                  "CIaaS: Incident-log evidence packet",
                  "CIaaS: Compliance checklist audit packet",
                ].map((option) => (
                  <button
                    key={option}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 p-4 text-left transition-colors hover:border-blue-500 hover:bg-slate-750"
                  >
                    <span className="font-medium text-white">{option}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <Code className="h-8 w-8 text-blue-500" />
                <h2 className="text-2xl font-bold text-white">{currentStepData.title}</h2>
              </div>
              <p className="text-lg text-slate-300">{currentStepData.description}</p>

              {provisioningError && (
                <div className="rounded-lg border border-amber-500/50 bg-amber-950/30 p-4 text-sm text-amber-200">
                  <AlertTriangle className="mr-2 inline h-4 w-4" />
                  {provisioningError}
                </div>
              )}

              {apiKey && (
                <div className="rounded-lg border border-blue-500 bg-slate-800 p-4">
                  <p className="mb-2 text-sm font-medium text-slate-400">Your API Key</p>
                  <code className="block rounded bg-slate-950 p-3 font-mono text-sm text-blue-400">
                    {apiKey}
                  </code>
                  <p className="mt-3 text-xs text-slate-500">
                    Stored in this browser for the Workload Studio demo handoff. Key ID:{" "}
                    {apiKeyId || "pending"}.
                  </p>
                </div>
              )}
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-8 w-8 text-green-500" />
                <h2 className="text-2xl font-bold text-white">Ready for Workload Studio</h2>
              </div>

              <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
                <p className="mb-2 text-sm font-medium text-slate-400">API Call Shape</p>
                <pre className="overflow-x-auto rounded bg-slate-950 p-3 text-xs text-slate-300">
                  {`POST /api/v1/computational-intelligence-services/{service_id}/execute
headers={"X-API-Key": "${apiKey ? "<stored_for_studio>" : "<missing>"}"}
json={"workload_type":"explain","context":{"cognitive_lens":"business","workload":"..."}}`}
                </pre>
              </div>

              <div className="rounded-lg border border-green-500/30 bg-green-950/20 p-4">
                <p className="text-sm text-green-400">
                  ✅ Key handed to Workload Studio. Bring the workload; the API will do the talking.
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="mt-8 flex items-center justify-between">
          <button
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0 || isProvisioningKey}
            className="rounded-lg px-4 py-2 text-sm text-slate-400 hover:text-slate-200 disabled:opacity-50"
          >
            Back
          </button>

          <button
            onClick={handleNext}
            disabled={isProvisioningKey}
            className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {isProvisioningKey
              ? "Generating…"
              : currentStep === steps.length - 1
                ? "Open Workload Studio"
                : currentStepData.action}
          </button>
        </div>
      </div>
    </div>
  );
}
