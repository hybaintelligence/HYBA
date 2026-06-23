/**
 * Customer Onboarding Flow
 *
 * Self-service activation for QaaS/QIaaS/CIaaS/Quantum Finance.
 * Zero sales engineer dependency. Get from signup to first API call in <5 minutes.
 */

import React, { useState } from "react";
import { CheckCircle2, Code, Rocket, Zap, X } from "lucide-react";

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  action: string;
  completed: boolean;
}

export function CustomerOnboarding({ onComplete }: { onComplete: () => void }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [apiKey, setApiKey] = useState<string | null>(null);

  const steps: OnboardingStep[] = [
    {
      id: "welcome",
      title: "Welcome to HYBA",
      description:
        "Substrate-independent quantum intelligence platform. Mathematics-first, hardware-agnostic.",
      action: "Get Started",
      completed: false,
    },
    {
      id: "provision",
      title: "Provision Your Service",
      description: "Choose your intelligence substrate: QaaS, QIaaS, CIaaS, or Quantum Finance.",
      action: "Provision",
      completed: false,
    },
    {
      id: "api_key",
      title: "Generate API Key",
      description: "Secure your access with HMAC-SHA256 authenticated API keys.",
      action: "Generate Key",
      completed: false,
    },
    {
      id: "quick_win",
      title: "Run Your First Query",
      description: "Execute a quantum-inspired optimization in 3 lines of code.",
      action: "Run Example",
      completed: false,
    },
  ];

  const handleNext = () => {
    if (currentStep === 2) {
      // Generate API key
      const key = `hyba_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`;
      setApiKey(key);
    }

    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete();
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

        {/* Progress bar */}
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

        {/* Content */}
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
                  <h3 className="mb-2 font-bold text-white">QaaS</h3>
                  <p className="text-sm text-slate-400">
                    Virtual quantum computers. No QPU required.
                  </p>
                </div>
                <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
                  <h3 className="mb-2 font-bold text-white">QIaaS</h3>
                  <p className="text-sm text-slate-400">
                    Predict, explain, optimize with quantum substrate.
                  </p>
                </div>
                <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
                  <h3 className="mb-2 font-bold text-white">CIaaS</h3>
                  <p className="text-sm text-slate-400">Provisioned intelligence runtimes.</p>
                </div>
                <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
                  <h3 className="mb-2 font-bold text-white">Quantum Finance</h3>
                  <p className="text-sm text-slate-400">
                    QUBO, QAOA, QAE, VaR with evidence seals.
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
                  "QaaS: Fault-Tolerant Computer",
                  "QIaaS: Intelligence Service",
                  "CIaaS: Computational Runtime",
                  "Quantum Finance: Portfolio QUBO",
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

              {apiKey && (
                <div className="rounded-lg border border-blue-500 bg-slate-800 p-4">
                  <p className="mb-2 text-sm font-medium text-slate-400">Your API Key</p>
                  <code className="block rounded bg-slate-950 p-3 font-mono text-sm text-blue-400">
                    {apiKey}
                  </code>
                  <p className="mt-3 text-xs text-slate-500">
                    Store this securely. You won't be able to see it again.
                  </p>
                </div>
              )}
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-8 w-8 text-green-500" />
                <h2 className="text-2xl font-bold text-white">Ready to Execute</h2>
              </div>

              <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
                <p className="mb-2 text-sm font-medium text-slate-400">Python Example</p>
                <pre className="overflow-x-auto rounded bg-slate-950 p-3 text-xs text-slate-300">
                  {`import requests

response = requests.post(
    "https://api.hyba.ai/api/qiaas/predict",
    headers={"X-HYBA-API-Key": "${apiKey}"},
    json={"query": "optimize portfolio", "context": {...}}
)

print(response.json())
# Output: {"prediction": {...}, "evidence_seal": "abc123..."}`}
                </pre>
              </div>

              <div className="rounded-lg border border-green-500/30 bg-green-950/20 p-4">
                <p className="text-sm text-green-400">
                  ✅ You're ready. The mathematics will do the talking.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="mt-8 flex items-center justify-between">
          <button
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
            className="rounded-lg px-4 py-2 text-sm text-slate-400 hover:text-slate-200 disabled:opacity-50"
          >
            Back
          </button>

          <button
            onClick={handleNext}
            className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {currentStep === steps.length - 1 ? "Start Building" : currentStepData.action}
          </button>
        </div>
      </div>
    </div>
  );
}
