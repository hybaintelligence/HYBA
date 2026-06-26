/**
 * Agent Execution Panel - Execute agent tasks with real-time feedback
 *
 * Purpose: Interface for executing agent tasks with token optimization,
 * GPU scaling configuration, and evidence seal visualization
 *
 * Trust Bridge: All executions return cryptographically sealed evidence
 */

import React, { useState } from "react";
import { Play, Settings, BarChart3, Shield, Clock, Zap, Cpu } from "lucide-react";

interface AgentTaskRequest {
  agent_id: string;
  task_type: string;
  prompt: string;
  context: Record<string, any>;
  priority: string;
  optimize_tokens: boolean;
  enable_gpu_scaling: boolean;
  governance_rail: string;
}

interface AgentExecutionResult {
  task_id: string;
  agent_id: string;
  status: string;
  result: Record<string, any>;
  evidence: Record<string, any>;
  token_optimization_applied: boolean;
  tokens_saved: number | null;
  gpu_scaling_used: boolean;
  gpus_utilized: number | null;
  execution_time_ms: number;
  confidence: number;
  cryptographic_seal: Record<string, any>;
  sovereign_human_gate: boolean;
  auto_apply: boolean;
}

interface AgentDefinition {
  agent_id: string;
  name: string;
  description: string;
  capabilities: string[];
  version: string;
  evidence_tier: string;
  category: string;
}

interface AgentExecutionPanelProps {
  selectedAgent: AgentDefinition | null;
  onExecutionComplete?: (result: AgentExecutionResult) => void;
}

export const AgentExecutionPanel: React.FC<AgentExecutionPanelProps> = ({
  selectedAgent,
  onExecutionComplete,
}) => {
  const [prompt, setPrompt] = useState("");
  const [taskType, setTaskType] = useState("general");
  const [optimizeTokens, setOptimizeTokens] = useState(true);
  const [enableGpuScaling, setEnableGpuScaling] = useState(false);
  const [governanceRail, setGovernanceRail] = useState("enterprise");
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState<AgentExecutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const executeTask = async () => {
    if (!selectedAgent) {
      setError("Please select an agent first");
      return;
    }

    if (!prompt.trim()) {
      setError("Please enter a prompt");
      return;
    }

    setExecuting(true);
    setError(null);
    setResult(null);

    try {
      const request: AgentTaskRequest = {
        agent_id: selectedAgent.agent_id,
        task_type: taskType,
        prompt,
        context: {},
        priority: "medium",
        optimize_tokens: optimizeTokens,
        enable_gpu_scaling: enableGpuScaling,
        governance_rail: governanceRail,
      };

      const response = await fetch("/api/agentic/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Execution failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
      if (onExecutionComplete) {
        onExecutionComplete(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setExecuting(false);
    }
  };

  if (!selectedAgent) {
    return (
      <div className="flex items-center justify-center h-64 border border-dashed border-gray-700 rounded-lg">
        <div className="text-center">
          <Shield className="w-12 h-12 mx-auto mb-3 text-gray-500" />
          <p className="text-gray-400">Select an agent from the marketplace to execute</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Agent Info */}
      <div className="p-4 bg-gray-800/30 border border-gray-700 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-white">{selectedAgent.name}</h3>
            <p className="text-sm text-gray-400">{selectedAgent.description}</p>
          </div>
          <span className="px-2 py-1 text-xs bg-emerald-500/20 text-emerald-300 rounded border border-emerald-500/30">
            {selectedAgent.evidence_tier}
          </span>
        </div>
      </div>

      {/* Task Configuration */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Task Type
          </label>
          <select
            value={taskType}
            onChange={(e) => setTaskType(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-emerald-500"
          >
            {selectedAgent.capabilities.map((capability) => (
              <option key={capability} value={capability}>
                {capability}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Prompt
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter your task prompt..."
            rows={4}
            className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-emerald-500 resize-none"
          />
        </div>

        {/* Advanced Options */}
        <div className="border-t border-gray-700 pt-4">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
          >
            <Settings className="w-4 h-4" />
            {showAdvanced ? "Hide" : "Show"} Advanced Options
          </button>

          {showAdvanced && (
            <div className="mt-4 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-yellow-500" />
                  <span className="text-sm text-gray-300">Token Optimization</span>
                </div>
                <button
                  onClick={() => setOptimizeTokens(!optimizeTokens)}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    optimizeTokens ? "bg-emerald-500" : "bg-gray-700"
                  }`}
                >
                  <div
                    className={`w-5 h-5 bg-white rounded-full transition-transform ${
                      optimizeTokens ? "translate-x-6" : "translate-x-0.5"
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-blue-500" />
                  <span className="text-sm text-gray-300">GPU Scaling</span>
                </div>
                <button
                  onClick={() => setEnableGpuScaling(!enableGpuScaling)}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    enableGpuScaling ? "bg-emerald-500" : "bg-gray-700"
                  }`}
                >
                  <div
                    className={`w-5 h-5 bg-white rounded-full transition-transform ${
                      enableGpuScaling ? "translate-x-6" : "translate-x-0.5"
                    }`}
                  />
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Governance Rail
                </label>
                <select
                  value={governanceRail}
                  onChange={(e) => setGovernanceRail(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="treasury">Treasury (R&D)</option>
                  <option value="enterprise">Enterprise (Production)</option>
                  <option value="sovereign">Sovereign (Regulated)</option>
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Execute Button */}
        <button
          onClick={executeTask}
          disabled={executing}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-emerald-500 hover:bg-emerald-600 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium rounded-lg transition-colors"
        >
          {executing ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Executing...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Execute Task
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-lg">
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div className="space-y-4">
          {/* Status */}
          <div className="p-4 bg-gray-800/30 border border-gray-700 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-white">Execution Result</h4>
              <span
                className={`px-2 py-1 text-xs rounded ${
                  result.status === "EXECUTION_STAGED"
                    ? "bg-emerald-500/20 text-emerald-300"
                    : "bg-yellow-500/20 text-yellow-300"
                }`}
              >
                {result.status}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-400" />
                <span className="text-gray-400">Execution Time:</span>
                <span className="text-white">{result.execution_time_ms.toFixed(2)}ms</span>
              </div>
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-gray-400" />
                <span className="text-gray-400">Confidence:</span>
                <span className="text-white">{result.confidence.toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* Optimization Stats */}
          {(result.token_optimization_applied || result.gpu_scaling_used) && (
            <div className="p-4 bg-gray-800/30 border border-gray-700 rounded-lg">
              <h4 className="font-semibold text-white mb-3">Optimization Applied</h4>
              <div className="space-y-2 text-sm">
                {result.token_optimization_applied && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Tokens Saved:</span>
                    <span className="text-emerald-300">
                      {result.tokens_saved?.toLocaleString() || 0}
                    </span>
                  </div>
                )}
                {result.gpu_scaling_used && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">GPUs Utilized:</span>
                    <span className="text-blue-300">{result.gpus_utilized}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Evidence Seal */}
          <div className="p-4 bg-gray-800/30 border border-emerald-500/50 rounded-lg">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-4 h-4 text-emerald-500" />
              <h4 className="font-semibold text-white">Evidence Seal</h4>
            </div>
            <div className="space-y-2 text-sm font-mono">
              <div className="flex justify-between">
                <span className="text-gray-400">Algorithm:</span>
                <span className="text-white">{result.cryptographic_seal.algorithm}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Body Hash:</span>
                <span className="text-white text-xs">
                  {result.cryptographic_seal.body_hash?.slice(0, 16)}...
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Seal:</span>
                <span className="text-white text-xs">
                  {result.cryptographic_seal.seal?.slice(0, 16)}...
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Sovereign Gate:</span>
                <span className={result.sovereign_human_gate ? "text-emerald-300" : "text-red-300"}>
                  {result.sovereign_human_gate ? "Active" : "Inactive"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Auto Apply:</span>
                <span className={result.auto_apply ? "text-red-300" : "text-emerald-300"}>
                  {result.auto_apply ? "Enabled" : "Disabled"}
                </span>
              </div>
            </div>
          </div>

          {/* Result Data */}
          {result.result && Object.keys(result.result).length > 0 && (
            <div className="p-4 bg-gray-800/30 border border-gray-700 rounded-lg">
              <h4 className="font-semibold text-white mb-3">Result Data</h4>
              <pre className="text-sm text-gray-300 overflow-x-auto">
                {JSON.stringify(result.result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
