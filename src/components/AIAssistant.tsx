/**
 * AI-Powered Adaptive Assistant
 *
 * Provides intelligent assistance for mining operations, diagnostics,
 * and system optimization using the intelligence fabric backend.
 */

import React, { useState, useEffect, useRef } from "react";
import {
  Activity,
  Brain,
  Zap,
  MessageSquare,
  X,
  Maximize2,
  Minimize2,
  ShieldCheck,
} from "lucide-react";
import { useSkillMode, SKILL_MODE_LABELS } from "../skillMode";

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  metadata?: {
    phiScore?: number;
    resonance?: number;
    governance?: string[];
  };
}

interface AIAssistantProps {
  token: string;
  miningStatus?: any;
  telemetryData?: any;
  userRole?: string;
  onCommand?: (command: string) => void;
}

type ProposedAction = {
  command: string;
  risk: "low" | "medium" | "high";
  blastRadius: string;
  approvalRequired: boolean;
  reason: string;
};

const LOW_RISK_ALLOWLIST = new Set(["refresh_telemetry"]);

const UNATTENDED_WRITES_ENABLED = import.meta.env.VITE_UNATTENDED_WRITES === "true";

function classifyAction(command: string, userRole?: string, skillMode?: string): ProposedAction {
  const normalized = String(command || "").trim();
  const lowRisk = LOW_RISK_ALLOWLIST.has(normalized);
  const privileged = ["admin", "ceo_heir_apparent", "chairman", "cto"].includes(
    String(userRole || "").toLowerCase(),
  );

  // Check for UNATTENDED_WRITES flag and expert mode
  const canBypassApproval = UNATTENDED_WRITES_ENABLED && skillMode === "expert" && privileged;

  return {
    command: normalized,
    risk: lowRisk
      ? "low"
      : normalized.includes("stop") ||
          normalized.includes("disconnect") ||
          normalized.includes("switch")
        ? "high"
        : "medium",
    blastRadius: lowRisk
      ? "Read-only telemetry refresh; no system writes."
      : "May affect runtime configuration, tenant state, or external integrations.",
    approvalRequired: !lowRisk && !canBypassApproval,
    reason: canBypassApproval
      ? "Expert mode with UNATTENDED_WRITES enabled - auto-approved for privileged users."
      : lowRisk
        ? "Pre-authorized read-only command."
        : "Governance requires explicit approval before execution.",
  };
}

const AIAssistant: React.FC<AIAssistantProps> = ({
  token,
  miningStatus,
  telemetryData,
  userRole,
  onCommand,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "system",
      content:
        "AI Assistant ready in proposal-only mode. I can explain, simulate, prepare remediation plans, and request approval before any action.",
      timestamp: Date.now(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [pendingAction, setPendingAction] = useState<ProposedAction | null>(null);
  const { skillMode } = useSkillMode();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Generate contextual suggestions based on system state
  useEffect(() => {
    const newSuggestions: string[] = [];

    if (miningStatus?.hashrate && miningStatus.hashrate < 100000) {
      newSuggestions.push("How can I improve my hashrate?");
    }

    if (telemetryData?.consciousness_events > 100) {
      newSuggestions.push("What do consciousness events mean?");
    }

    if (miningStatus?.pool?.status === "disconnected") {
      newSuggestions.push("Help me diagnose pool connection issues");
    }

    if (!miningStatus?.active) {
      newSuggestions.push("Guide me through starting mining");
    }

    // Always offer general assistance
    if (newSuggestions.length === 0) {
      newSuggestions.push(
        "Explain this like I’m a CFO",
        "What action is safe?",
        "Prepare a remediation plan, but do not execute",
      );
    }

    setSuggestions(newSuggestions);
  }, [miningStatus, telemetryData]);

  const processMessage = async (userMessage: string) => {
    setIsProcessing(true);

    // Add user message
    const userMsg: Message = {
      role: "user",
      content: userMessage,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      // Build context for the AI
      const context = {
        miningStatus: miningStatus || {},
        telemetry: telemetryData || {},
        timestamp: new Date().toISOString(),
      };

      // Call intelligence fabric endpoint with Salamander regeneration capability
      const response = await fetch("/api/intelligence/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          query: userMessage,
          context: JSON.stringify({ ...context, skill_mode: skillMode }),
          substrates: ["manifold", "consciousness", "quantum"],
          enable_regeneration: true,
          auto_fix: false,
          proposal_only: true,
          require_human_approval: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`AI service error: ${response.status}`);
      }

      const result = await response.json();

      // Add assistant response
      const assistantMsg: Message = {
        role: "assistant",
        content: result.explanation || result.response || "I processed your request.",
        timestamp: Date.now(),
        metadata: {
          phiScore: result.phi_score,
          resonance: result.resonance,
          governance: result.governance_tags,
        },
      };
      setMessages((prev) => [...prev, assistantMsg]);

      const proposedAction = result.regeneration_action || result.suggested_action;
      if (proposedAction) {
        setPendingAction(classifyAction(String(proposedAction), userRole, skillMode));
        setMessages((prev) => [
          ...prev,
          {
            role: "system",
            content: `Prepared proposal only: ${proposedAction}. Review blast radius and explicitly approve before execution.`,
            timestamp: Date.now(),
            metadata: { governance: ["proposal_only", "human_approval_required"] },
          },
        ]);
      }
    } catch (error) {
      console.error("AI Assistant error:", error);

      // Fallback to local heuristic assistance
      const fallbackResponse = generateFallbackResponse(userMessage, miningStatus, telemetryData);

      const assistantMsg: Message = {
        role: "assistant",
        content: fallbackResponse,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    }

    setIsProcessing(false);
    setInput("");
  };

  const generateFallbackResponse = (query: string, status: any, telemetry: any): string => {
    const q = query.toLowerCase();

    // Mining status queries
    if (q.includes("hashrate") || q.includes("hash rate")) {
      const hashrate = status?.hashrate || 0;
      const formatted = (hashrate / 1e6).toFixed(2);
      return `Your current hashrate is ${formatted} MH/s. ${
        hashrate < 100000
          ? "This is relatively low. Consider increasing PHI_SCALING_FACTOR or SEARCH_DEPTH for better performance."
          : "Your hashrate is performing well."
      }`;
    }

    if (q.includes("pool") && (q.includes("connect") || q.includes("disconnect"))) {
      return `Pool status: ${status?.pool?.status || "unknown"}. ${
        status?.pool?.status === "connected"
          ? "Pool connection is healthy."
          : "Check your pool URL and credentials in the pool configuration panel."
      }`;
    }

    // Telemetry queries
    if (q.includes("consciousness") || q.includes("phi")) {
      const events = telemetry?.consciousness_events || 0;
      const phi = telemetry?.phi_resonance || 0;
      return `Consciousness events: ${events.toLocaleString()}, φ-resonance: ${phi.toFixed(4)}. ${
        events > 1000
          ? "Your system is showing strong structural coherence."
          : "Consider adjusting coherence thresholds for better resonance."
      }`;
    }

    if (q.includes("compression") || q.includes("memory")) {
      const ratio = telemetry?.compression_ratio || 1.0;
      return `Current compression ratio: ${ratio.toFixed(2)}x. ${
        ratio > 2.0
          ? "Excellent memory efficiency!"
          : "Memory compression is active but could be improved."
      }`;
    }

    // Configuration queries
    if (q.includes("optimize") || q.includes("improve")) {
      return `To optimize performance:
1. Adjust PHI_SCALING_FACTOR (current: ${status?.config?.phi_scaling || "default"})
2. Tune SEARCH_DEPTH for deeper exploration
3. Monitor consciousness events for coherence feedback
4. Enable autonomous mode for self-optimization`;
    }

    // Start/stop queries
    if (q.includes("start") && q.includes("mining")) {
      return status?.active
        ? "Mining is already active. Check the dashboard for real-time metrics."
        : "To start mining: configure your pool in the Pool Management panel, then click 'Start Mining' in the dashboard.";
    }

    // Diagnostics
    if (q.includes("diagnose") || q.includes("problem") || q.includes("issue")) {
      const issues: string[] = [];
      if (!status?.active) issues.push("Mining is not active");
      if (status?.pool?.status !== "connected") issues.push("Pool not connected");
      if ((status?.hashrate || 0) < 10000) issues.push("Very low hashrate");

      return issues.length > 0
        ? `Detected issues:\n${issues.map((i, idx) => `${idx + 1}. ${i}`).join("\n")}\n\nRecommendation: Check pool configuration and ensure mining is started.`
        : "All systems appear operational. No issues detected.";
    }

    // Default
    return `I understand you're asking about: "${query}". Try these specific queries:
- "What's my current hashrate?"
- "Optimize my mining configuration"
- "Diagnose system issues"
- "Explain consciousness events"`;
  };

  const approveProposedAction = () => {
    if (!pendingAction || !onCommand) return;
    const proposal = classifyAction(pendingAction.command, userRole, skillMode);
    if (proposal.approvalRequired) {
      const approved = window.confirm(
        `Approve HYBA action?\n\nCommand: ${proposal.command}\nRisk: ${proposal.risk}\nBlast radius: ${proposal.blastRadius}`,
      );
      if (!approved) return;
    }
    onCommand(proposal.command);
    setMessages((prev) => [
      ...prev,
      {
        role: "system",
        content: `Approved action executed: ${proposal.command}`,
        timestamp: Date.now(),
      },
    ]);
    setPendingAction(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isProcessing) {
      processMessage(input.trim());
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 p-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-110 z-50"
        title="Open AI Assistant"
      >
        <Brain className="w-6 h-6" />
      </button>
    );
  }

  return (
    <div
      className={`fixed bottom-6 right-6 bg-gradient-to-br from-slate-900 to-slate-800 border border-white/10 rounded-2xl shadow-2xl z-50 transition-all duration-300 ${
        isMinimized ? "w-80 h-16" : "w-96 h-[600px]"
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Brain className="w-5 h-5 text-purple-400" />
            {isProcessing && (
              <Zap className="w-3 h-3 text-yellow-400 absolute -top-1 -right-1 animate-pulse" />
            )}
          </div>
          <span className="font-semibold text-white">Adaptive AI Assistant</span>
          <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold text-emerald-200">
            proposal only
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 hover:bg-white/10 rounded transition-colors"
          >
            {isMinimized ? (
              <Maximize2 className="w-4 h-4 text-white/60" />
            ) : (
              <Minimize2 className="w-4 h-4 text-white/60" />
            )}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1 hover:bg-white/10 rounded transition-colors"
          >
            <X className="w-4 h-4 text-white/60" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 h-[420px]">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.role !== "user" && (
                  <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                    <Brain className="w-4 h-4 text-purple-400" />
                  </div>
                )}
                <div
                  className={`rounded-lg p-3 max-w-[80%] ${
                    msg.role === "user"
                      ? "bg-blue-500/20 text-blue-100"
                      : msg.role === "system"
                        ? "bg-slate-700/50 text-slate-300 text-sm"
                        : "bg-purple-500/20 text-purple-100"
                  }`}
                >
                  <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                  {msg.metadata?.phiScore && (
                    <div className="mt-2 text-xs opacity-70">
                      φ-score: {msg.metadata.phiScore.toFixed(3)}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isProcessing && (
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center">
                  <Activity className="w-4 h-4 text-purple-400 animate-pulse" />
                </div>
                <div className="bg-purple-500/20 text-purple-100 rounded-lg p-3">
                  <div className="flex gap-1">
                    <div
                      className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0ms" }}
                    />
                    <div
                      className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"
                      style={{ animationDelay: "150ms" }}
                    />
                    <div
                      className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"
                      style={{ animationDelay: "300ms" }}
                    />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="mx-4 mb-2 rounded-lg border border-emerald-400/20 bg-emerald-500/10 p-3 text-xs text-emerald-100">
            <div className="flex items-center gap-2 font-semibold">
              <ShieldCheck className="h-3.5 w-3.5" /> {SKILL_MODE_LABELS[skillMode]} lens · Human
              approval required
            </div>
            <p className="mt-1 text-emerald-100/80">
              HYBA may explain, simulate, and prepare remediation, but commands are blocked until
              explicit approval.
            </p>
          </div>
          {pendingAction && (
            <div className="mx-4 mb-2 rounded-lg border border-amber-400/30 bg-amber-500/10 p-3 text-xs text-amber-100">
              <p className="font-semibold">Remediation Proposal: {pendingAction.command}</p>
              <p className="mt-1">Risk: {pendingAction.risk.toUpperCase()}</p>
              <p className="mt-1">Blast radius: {pendingAction.blastRadius}</p>
              <p className="mt-1">Approval reason: {pendingAction.reason}</p>
              <button
                onClick={approveProposedAction}
                className="mt-2 rounded bg-amber-400 px-3 py-1 font-semibold text-slate-950"
              >
                Approve with human signature
              </button>
            </div>
          )}

          {/* Suggestions */}
          {suggestions.length > 0 && messages.length === 1 && (
            <div className="px-4 py-2 border-t border-white/10">
              <p className="text-xs text-white/50 mb-2">Suggested questions:</p>
              <div className="flex flex-wrap gap-2">
                {suggestions.map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInput(suggestion)}
                    className="text-xs px-3 py-1 bg-white/5 hover:bg-white/10 rounded-full text-white/70 hover:text-white transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="p-4 border-t border-white/10">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me anything..."
                disabled={isProcessing}
                className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white placeholder-white/30 focus:outline-none focus:border-purple-400/50 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!input.trim() || isProcessing}
                className="px-4 py-2 bg-purple-500 hover:bg-purple-600 disabled:bg-purple-500/30 text-white rounded-lg transition-colors disabled:cursor-not-allowed"
              >
                <MessageSquare className="w-5 h-5" />
              </button>
            </form>
          </div>
        </>
      )}
    </div>
  );
};

export default AIAssistant;
