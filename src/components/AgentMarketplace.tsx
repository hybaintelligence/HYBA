/**
 * Agent Marketplace - Browse and discover pre-built HYBA agents
 *
 * Purpose: Interface for the agent marketplace with filtering, search,
 * and agent capability visualization
 *
 * Trust Bridge: All agent definitions come from evidence-sealed backend
 */

import React, { useEffect, useState } from "react";
import { Search, Filter, Cpu, Shield, TrendingUp, Database, Lock } from "lucide-react";

interface AgentCapability {
  name: string;
  description: string;
  confidence_threshold: number;
}

interface AgentDefinition {
  agent_id: string;
  name: string;
  description: string;
  capabilities: string[];
  version: string;
  evidence_tier: string;
  confidence_threshold: number;
  requires_gpu: boolean;
  max_tokens: number | null;
  category: string;
}

interface AgentMarketplaceProps {
  onAgentSelect?: (agent: AgentDefinition) => void;
}

const EvidenceTierBadge: React.FC<{ tier: string }> = ({ tier }) => {
  const colors = {
    quantum_backed: "bg-purple-500/20 text-purple-300 border-purple-500/50",
    heuristic: "bg-emerald-500/20 text-emerald-300 border-emerald-500/50",
    classical_fallback: "bg-blue-500/20 text-blue-300 border-blue-500/50",
  };

  const labels = {
    quantum_backed: "Quantum-Backed",
    heuristic: "Heuristic",
    classical_fallback: "Classical",
  };

  return (
    <span
      className={`px-2 py-1 text-xs font-medium border rounded ${
        colors[tier as keyof typeof colors] || colors.classical_fallback
      }`}
    >
      {labels[tier as keyof typeof labels] || tier}
    </span>
  );
};

const CategoryIcon: React.FC<{ category: string }> = ({ category }) => {
  const icons = {
    finance: TrendingUp,
    security: Shield,
    operations: Cpu,
    analysis: Database,
    general: Lock,
  };

  const Icon = icons[category as keyof typeof icons] || icons.general;
  return <Icon className="w-5 h-5" />;
};

export const AgentMarketplace: React.FC<AgentMarketplaceProps> = ({
  onAgentSelect,
}) => {
  const [agents, setAgents] = useState<AgentDefinition[]>([]);
  const [filteredAgents, setFilteredAgents] = useState<AgentDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<AgentDefinition | null>(null);

  const categories = ["finance", "security", "operations", "analysis", "general"];

  useEffect(() => {
    fetchAgents();
  }, []);

  useEffect(() => {
    filterAgents();
  }, [agents, searchQuery, selectedCategory]);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/agentic/agents");
      if (!response.ok) throw new Error("Failed to fetch agents");
      const data = await response.json();
      setAgents(data);
      setFilteredAgents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const filterAgents = () => {
    let filtered = [...agents];

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (agent) =>
          agent.name.toLowerCase().includes(query) ||
          agent.description.toLowerCase().includes(query) ||
          agent.capabilities.some((cap) => cap.toLowerCase().includes(query))
      );
    }

    if (selectedCategory) {
      filtered = filtered.filter((agent) => agent.category === selectedCategory);
    }

    setFilteredAgents(filtered);
  };

  const handleAgentClick = (agent: AgentDefinition) => {
    setSelectedAgent(agent);
    if (onAgentSelect) {
      onAgentSelect(agent);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading agent marketplace...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-400">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Agent Marketplace</h2>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">
            {filteredAgents.length} agents available
          </span>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search agents by name, description, or capabilities..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-emerald-500"
          />
        </div>
        <div className="flex gap-2">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() =>
                setSelectedCategory(
                  selectedCategory === category ? null : category
                )
              }
              className={`px-3 py-2 rounded-lg border transition-colors ${
                selectedCategory === category
                  ? "bg-emerald-500/20 border-emerald-500 text-emerald-300"
                  : "bg-gray-800/50 border-gray-700 text-gray-300 hover:border-gray-600"
              }`}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAgents.map((agent) => (
          <div
            key={agent.agent_id}
            onClick={() => handleAgentClick(agent)}
            className={`p-4 bg-gray-800/30 border rounded-lg cursor-pointer transition-all hover:bg-gray-800/50 ${
              selectedAgent?.agent_id === agent.agent_id
                ? "border-emerald-500 bg-emerald-500/10"
                : "border-gray-700"
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <CategoryIcon category={agent.category} />
                <h3 className="font-semibold text-white">{agent.name}</h3>
              </div>
              <EvidenceTierBadge tier={agent.evidence_tier} />
            </div>

            <p className="text-sm text-gray-400 mb-3 line-clamp-2">
              {agent.description}
            </p>

            <div className="flex flex-wrap gap-1 mb-3">
              {agent.capabilities.slice(0, 3).map((capability) => (
                <span
                  key={capability}
                  className="px-2 py-1 text-xs bg-gray-700/50 text-gray-300 rounded"
                >
                  {capability}
                </span>
              ))}
              {agent.capabilities.length > 3 && (
                <span className="px-2 py-1 text-xs bg-gray-700/50 text-gray-300 rounded">
                  +{agent.capabilities.length - 3}
                </span>
              )}
            </div>

            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>v{agent.version}</span>
              <div className="flex items-center gap-2">
                {agent.requires_gpu && <Cpu className="w-4 h-4" />}
                <span>{agent.confidence_threshold}% confidence</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Selected Agent Detail */}
      {selectedAgent && (
        <div className="p-6 bg-gray-800/30 border border-emerald-500/50 rounded-lg">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-xl font-bold text-white mb-1">
                {selectedAgent.name}
              </h3>
              <p className="text-sm text-gray-400">{selectedAgent.description}</p>
            </div>
            <EvidenceTierBadge tier={selectedAgent.evidence_tier} />
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <span className="text-xs text-gray-500">Agent ID</span>
              <p className="text-sm text-white font-mono">{selectedAgent.agent_id}</p>
            </div>
            <div>
              <span className="text-xs text-gray-500">Version</span>
              <p className="text-sm text-white">{selectedAgent.version}</p>
            </div>
            <div>
              <span className="text-xs text-gray-500">Category</span>
              <p className="text-sm text-white capitalize">{selectedAgent.category}</p>
            </div>
            <div>
              <span className="text-xs text-gray-500">Confidence Threshold</span>
              <p className="text-sm text-white">{selectedAgent.confidence_threshold}%</p>
            </div>
          </div>

          <div className="mb-4">
            <span className="text-xs text-gray-500 block mb-2">Capabilities</span>
            <div className="flex flex-wrap gap-2">
              {selectedAgent.capabilities.map((capability) => (
                <span
                  key={capability}
                  className="px-3 py-1 text-sm bg-emerald-500/20 text-emerald-300 rounded border border-emerald-500/30"
                >
                  {capability}
                </span>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4 text-sm">
            {selectedAgent.requires_gpu && (
              <div className="flex items-center gap-2 text-gray-300">
                <Cpu className="w-4 h-4" />
                <span>GPU Required</span>
              </div>
            )}
            {selectedAgent.max_tokens && (
              <div className="flex items-center gap-2 text-gray-300">
                <Database className="w-4 h-4" />
                <span>Max {selectedAgent.max_tokens.toLocaleString()} tokens</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
