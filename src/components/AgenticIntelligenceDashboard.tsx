/**
 * Agentic Intelligence Dashboard - Unified interface for AIaaS
 *
 * Purpose: Main dashboard combining agent marketplace, execution panel,
 * token optimization stats, and GPU utilization metrics
 *
 * Trust Bridge: All data comes from evidence-sealed backend APIs
 */

import React, { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AgentMarketplace } from "./AgentMarketplace";
import { AgentExecutionPanel } from "./AgentExecutionPanel";
import { Zap, Cpu, BarChart3, Shield } from "lucide-react";

interface AgentDefinition {
  agent_id: string;
  name: string;
  description: string;
  capabilities: string[];
  version: string;
  evidence_tier: string;
  category: string;
}

interface TokenOptimizationStats {
  total_optimizations: number;
  avg_compression_ratio: number;
  total_tokens_saved: number;
  avg_tokens_saved_per_optimization: number;
}

interface GPUUtilizationStats {
  active_gpus: number;
  max_gpus: number;
  utilization_percent: number;
  active_tasks: string[];
}

export const AgenticIntelligenceDashboard: React.FC = () => {
  const [selectedAgent, setSelectedAgent] = useState<AgentDefinition | null>(null);
  const [tokenStats, setTokenStats] = useState<TokenOptimizationStats | null>(null);
  const [gpuStats, setGpuStats] = useState<GPUUtilizationStats | null>(null);
  const [activeTab, setActiveTab] = useState("marketplace");

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const [tokenRes, gpuRes] = await Promise.all([
        fetch("/api/agentic/optimization/tokens/stats"),
        fetch("/api/agentic/scaling/gpu/stats"),
      ]);

      if (tokenRes.ok) {
        const tokenData = await tokenRes.json();
        setTokenStats(tokenData);
      }

      if (gpuRes.ok) {
        const gpuData = await gpuRes.json();
        setGpuStats(gpuData);
      }
    } catch (err) {
      console.error("Failed to fetch stats:", err);
    }
  };

  const handleAgentSelect = (agent: AgentDefinition) => {
    setSelectedAgent(agent);
    setActiveTab("execute");
  };

  const handleExecutionComplete = () => {
    // Refresh stats after execution
    fetchStats();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Agentic Intelligence</h1>
          <p className="text-gray-400 mt-1">
            Evidence-sealed agent execution with token optimization and GPU scaling
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-emerald-500" />
          <span className="text-sm text-emerald-400">Sovereign-Gated</span>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Token Optimization Stats */}
        <div className="p-4 bg-gray-800/30 border border-gray-700 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-500" />
              <span className="text-sm text-gray-400">Token Optimization</span>
            </div>
          </div>
          {tokenStats ? (
            <div className="space-y-1">
              <div className="text-2xl font-bold text-white">
                {tokenStats.total_tokens_saved.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500">tokens saved</div>
              <div className="text-xs text-emerald-400">
                {tokenStats.avg_compression_ratio.toFixed(2)}x avg compression
              </div>
            </div>
          ) : (
            <div className="text-sm text-gray-500">Loading...</div>
          )}
        </div>

        {/* GPU Utilization Stats */}
        <div className="p-4 bg-gray-800/30 border border-gray-700 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-blue-500" />
              <span className="text-sm text-gray-400">GPU Utilization</span>
            </div>
          </div>
          {gpuStats ? (
            <div className="space-y-1">
              <div className="text-2xl font-bold text-white">
                {gpuStats.active_gpus}/{gpuStats.max_gpus}
              </div>
              <div className="text-xs text-gray-500">active GPUs</div>
              <div className="text-xs text-blue-400">
                {gpuStats.utilization_percent.toFixed(1)}% utilization
              </div>
            </div>
          ) : (
            <div className="text-sm text-gray-500">Loading...</div>
          )}
        </div>

        {/* Total Executions */}
        <div className="p-4 bg-gray-800/30 border border-gray-700 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-emerald-500" />
              <span className="text-sm text-gray-400">Total Optimizations</span>
            </div>
          </div>
          {tokenStats ? (
            <div className="space-y-1">
              <div className="text-2xl font-bold text-white">
                {tokenStats.total_optimizations}
              </div>
              <div className="text-xs text-gray-500">optimizations performed</div>
              <div className="text-xs text-emerald-400">
                {tokenStats.avg_tokens_saved_per_optimization.toFixed(0)} avg saved
              </div>
            </div>
          ) : (
            <div className="text-sm text-gray-500">Loading...</div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-gray-800/50 border border-gray-700">
          <TabsTrigger value="marketplace" className="data-[state=active]:bg-emerald-500/20">
            Agent Marketplace
          </TabsTrigger>
          <TabsTrigger value="execute" className="data-[state=active]:bg-emerald-500/20">
            Execute Task
          </TabsTrigger>
        </TabsList>

        <TabsContent value="marketplace" className="space-y-4">
          <AgentMarketplace onAgentSelect={handleAgentSelect} />
        </TabsContent>

        <TabsContent value="execute" className="space-y-4">
          <AgentExecutionPanel
            selectedAgent={selectedAgent}
            onExecutionComplete={handleExecutionComplete}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};
