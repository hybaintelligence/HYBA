/**
 * Quick Start Tutorial
 * 
 * Interactive "Hello World" for QaaS/QIaaS/CIaaS.
 * Get from zero to first API call in <2 minutes.
 */

import React, { useState } from 'react';
import { CheckCircle2, Code, Copy, Play } from 'lucide-react';

type TutorialType = 'qaas' | 'qiaas' | 'ciaas' | 'quantum_finance';

interface QuickStartProps {
  type: TutorialType;
  apiKey?: string;
}

export function QuickStartTutorial({ type, apiKey = 'YOUR_API_KEY' }: QuickStartProps) {
  const [step, setStep] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  
  const tutorials = {
    qaas: {
      title: 'QaaS: Run a Quantum Circuit',
      steps: [
        {
          title: 'Provision a Quantum Computer',
          description: 'Create a virtual fault-tolerant quantum computer',
          code: `curl -X POST https://api.hyba.ai/api/v1/fault-tolerant-computers \\
  -H "X-HYBA-API-Key: ${apiKey}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "my-quantum-computer",
    "tier": "developer",
    "isolation": "single-tenant",
    "code_distance": 3,
    "logical_qubits": 10,
    "data_residency": "us"
  }'`,
        },
        {
          title: 'Execute Quantum Operation',
          description: 'Run a surface code cycle',
          code: `curl -X POST https://api.hyba.ai/api/v1/fault-tolerant-computers/{computer_id}/execute \\
  -H "X-HYBA-API-Key: ${apiKey}" \\
  -d '{
    "operation": "surface_code_cycle",
    "logical_qubits": [0, 1, 2],
    "circuit_depth": 10,
    "shots": 1000
  }'`,
        },
        {
          title: 'View Results',
          description: 'Evidence-sealed execution results',
          code: `{
  "execution_id": "exec_abc123",
  "results": {...},
  "evidence_seal": "sha256:...",
  "claim_boundary": "Surface code simulation, no QPU"
}`,
        },
      ],
    },
    qiaas: {
      title: 'QIaaS: Predict & Explain',
      steps: [
        {
          title: 'Submit Prediction Query',
          description: 'Quantum-substrate intelligence prediction',
          code: `curl -X POST https://api.hyba.ai/api/qiaas/predict \\
  -H "X-HYBA-API-Key: ${apiKey}" \\
  -d '{
    "query": "optimize resource allocation",
    "context": {"resources": 100, "constraints": [...]}
  }'`,
        },
        {
          title: 'Get Explanation',
          description: 'Understand why the prediction was made',
          code: `curl -X POST https://api.hyba.ai/api/qiaas/explain \\
  -H "X-HYBA-API-Key: ${apiKey}" \\
  -d '{
    "prediction_id": "pred_xyz789",
    "explanation_depth": "detailed"
  }'`,
        },
        {
          title: 'Review Evidence',
          description: 'Evidence seal and confidence metrics',
          code: `{
  "prediction": {...},
  "confidence": 0.94,
  "evidence_seal": "sha256:...",
  "reasoning_trace": [...]
}`,
        },
      ],
    },
    ciaas: {
      title: 'CIaaS: Provision Intelligence Runtime',
      steps: [
        {
          title: 'Provision Service',
          description: 'Create dedicated computational intelligence runtime',
          code: `curl -X POST https://api.hyba.ai/api/v1/computational-intelligence-services \\
  -H "X-HYBA-API-Key: ${apiKey}" \\
  -d '{
    "name": "my-intelligence-service",
    "service_tier": "production",
    "tenancy": "dedicated-control-plane",
    "logical_compute_units": 100
  }'`,
        },
        {
          title: 'Execute Workload',
          description: 'Run intelligence workload',
          code: `curl -X POST https://api.v1/computational-intelligence-services/{service_id}/execute \\
  -H "X-HYBA-API-Key: ${apiKey}" \\
  -d '{
    "workload_type": "orchestrate",
    "context": {...}
  }'`,
        },
        {
          title: 'Monitor Execution',
          description: 'Real-time intelligence metrics',
          code: `{
  "workload_id": "wl_abc123",
  "status": "completed",
  "evidence_seal": "sha256:...",
  "metrics": {
    "phi_saturation": 0.87,
    "integration_depth": 12
  }
}`,
        },
      ],
    },
    quantum_finance: {
      title: 'Quantum Finance: Portfolio QUBO',
      steps: [
        {
          title: 'Design Portfolio QUBO',
          description: 'Convert portfolio optimization to QUBO',
          code: `curl -X POST https://api.hyba.ai/api/quantum-finance/portfolio/qaoa-design \\
  -H "X-HYBA-API-Key: ${apiKey}" \\
  -d '{
    "assets": ["AAPL", "GOOGL", "MSFT"],
    "returns": [0.12, 0.15, 0.10],
    "covariance": [[...], [...], [...]],
    "risk_tolerance": 0.5
  }'`,
        },
        {
          title: 'Get QAOA Parameters',
          description: 'Ising Hamiltonian and circuit design',
          code: `{
  "qubo_matrix": [[...]],
  "ising_hamiltonian": {...},
  "qaoa_layers": 3,
  "optimal_params": [0.5, 0.7, ...],
  "evidence_seal": "sha256:..."
}`,
        },
        {
          title: 'Calculate VaR',
          description: 'Quantum-enhanced risk metrics',
          code: `curl -X POST https://api.hyba.ai/api/quantum-finance/risk/var \\
  -H "X-HYBA-API-Key: ${apiKey}" \\
  -d '{
    "portfolio": {...},
    "confidence_level": 0.95,
    "time_horizon": 1
  }'`,
        },
      ],
    },
  };
  
  const currentTutorial = tutorials[type];
  const currentStep = currentTutorial.steps[step];
  
  const handleCopy = () => {
    navigator.clipboard.writeText(currentStep.code);
  };
  
  const handleRun = async () => {
    setLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    setResult({
      status: 'success',
      execution_time_ms: 120,
      evidence_seal: 'sha256:abc123...',
    });
    setLoading(false);
  };
  
  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-6 text-xl font-bold text-slate-950">{currentTutorial.title}</h3>
        
        {/* Step indicator */}
        <div className="mb-6 flex items-center justify-between">
          {currentTutorial.steps.map((s, idx) => (
            <React.Fragment key={idx}>
              <div className="flex flex-col items-center">
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full ${
                    idx <= step
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-200 text-slate-400'
                  }`}
                >
                  {idx < step ? <CheckCircle2 className="h-5 w-5" /> : idx + 1}
                </div>
                <span className="mt-2 text-xs text-slate-600">{s.title}</span>
              </div>
              {idx < currentTutorial.steps.length - 1 && (
                <div
                  className={`h-0.5 flex-1 ${
                    idx < step ? 'bg-blue-600' : 'bg-slate-200'
                  }`}
                />
              )}
            </React.Fragment>
          ))}
        </div>
        
        {/* Step content */}
        <div className="space-y-4">
          <div>
            <h4 className="font-bold text-slate-950">{currentStep.title}</h4>
            <p className="text-sm text-slate-600">{currentStep.description}</p>
          </div>
          
          <div className="relative rounded-lg border border-slate-300 bg-slate-950 p-4">
            <button
              onClick={handleCopy}
              className="absolute right-2 top-2 rounded-lg bg-slate-800 p-2 text-slate-400 hover:bg-slate-700 hover:text-slate-200"
            >
              <Copy className="h-4 w-4" />
            </button>
            <pre className="overflow-x-auto pr-12 text-xs text-slate-300">
              {currentStep.code}
            </pre>
          </div>
          
          {step < currentTutorial.steps.length - 1 && (
            <button
              onClick={handleRun}
              disabled={loading}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              <Play className="h-4 w-4" />
              {loading ? 'Running...' : 'Run this step'}
            </button>
          )}
          
          {result && (
            <div className="rounded-lg border border-green-200 bg-green-50 p-4">
              <div className="flex items-center gap-2 text-green-900">
                <CheckCircle2 className="h-5 w-5" />
                <span className="font-medium">Success</span>
              </div>
              <pre className="mt-2 text-xs text-green-800">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
        
        {/* Navigation */}
        <div className="mt-6 flex items-center justify-between">
          <button
            onClick={() => setStep(Math.max(0, step - 1))}
            disabled={step === 0}
            className="rounded-lg px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 disabled:opacity-50"
          >
            Previous
          </button>
          <button
            onClick={() => setStep(Math.min(currentTutorial.steps.length - 1, step + 1))}
            disabled={step === currentTutorial.steps.length - 1}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {step === currentTutorial.steps.length - 1 ? 'Done' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
}
