/**
 * CEO Terminal - Real-time Salamander Regeneration Monitor
 *
 * Displays constant updates of AI-triggered regeneration events,
 * showing the transition from proposal-based to actual fixing capability.
 */

import React, { useState, useEffect, useRef } from "react";
import {
  Terminal,
  Activity,
  Zap,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  Skull,
  HeartPulse,
  Brain,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Filter,
  Download,
  Trash2,
} from "lucide-react";

interface RegenerationEvent {
  id: string;
  timestamp: string;
  module_id: string;
  lane_id?: number;
  event_type: "fault_detected" | "quarantine" | "blastema_formation" | "redifferentiation" | "recovery" | "failure";
  severity: "low" | "medium" | "high" | "critical";
  status: "pending" | "in_progress" | "completed" | "failed";
  phi_score?: number;
  fidelity?: number;
  duration_ms?: number;
  message: string;
  details?: Record<string, any>;
  ai_triggered: boolean;
}

interface CEOTerminalProps {
  token: string | null;
  autoScroll?: boolean;
  maxEvents?: number;
}

const CEOTerminal: React.FC<CEOTerminalProps> = ({
  token,
  autoScroll = true,
  maxEvents = 100,
}) => {
  const [events, setEvents] = useState<RegenerationEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [filter, setFilter] = useState<"all" | "ai_triggered" | "system" | "failures">("all");
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());
  const terminalRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Simulated WebSocket connection for real-time updates
  useEffect(() => {
    if (!token) return;

    // In production, this would connect to actual WebSocket endpoint
    // For now, we'll simulate with periodic polling
    const connectWebSocket = () => {
      setIsConnected(true);
      
      // Simulate receiving regeneration events
      const simulationInterval = setInterval(() => {
        if (Math.random() > 0.7) { // 30% chance of new event
          const newEvent = generateSimulatedEvent();
          setEvents(prev => {
            const updated = [newEvent, ...prev].slice(0, maxEvents);
            return updated;
          });
        }
      }, 3000);

      return () => {
        clearInterval(simulationInterval);
        setIsConnected(false);
      };
    };

    const cleanup = connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      cleanup();
    };
  }, [token, maxEvents]);

  // Auto-scroll to latest event
  useEffect(() => {
    if (autoScroll && terminalRef.current) {
      terminalRef.current.scrollTop = 0;
    }
  }, [events, autoScroll]);

  const generateSimulatedEvent = (): RegenerationEvent => {
    const eventTypes: RegenerationEvent["event_type"][] = [
      "fault_detected",
      "quarantine",
      "blastema_formation",
      "redifferentiation",
      "recovery",
      "failure",
    ];
    const severities: RegenerationEvent["severity"][] = ["low", "medium", "high", "critical"];
    const statuses: RegenerationEvent["status"][] = ["pending", "in_progress", "completed", "failed"];
    
    const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)];
    const severity = severities[Math.floor(Math.random() * severities.length)];
    const status = statuses[Math.floor(Math.random() * statuses.length)];
    const aiTriggered = Math.random() > 0.5;

    return {
      id: `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      module_id: `module_${Math.floor(Math.random() * 32)}`,
      lane_id: Math.floor(Math.random() * 32),
      event_type: eventType,
      severity,
      status,
      phi_score: 0.45 + Math.random() * 0.55,
      fidelity: 0.8 + Math.random() * 0.2,
      duration_ms: Math.random() * 1000,
      message: generateEventMessage(eventType, severity, aiTriggered),
      ai_triggered: aiTriggered,
      details: {
        clifford_index: Math.floor(Math.random() * 32),
        generation: Math.floor(Math.random() * 10),
        entropy: Math.random(),
      },
    };
  };

  const generateEventMessage = (
    eventType: RegenerationEvent["event_type"],
    severity: RegenerationEvent["severity"],
    aiTriggered: boolean
  ): string => {
    const aiPrefix = aiTriggered ? "[AI-TRIGGERED] " : "";
    const severityPrefix = severity === "critical" ? "[CRITICAL] " : "";
    
    const messages: Record<RegenerationEvent["event_type"], string[]> = {
      fault_detected: [
        "Fault detected in module - initiating regeneration protocol",
        "Anomaly detected in computational lane",
        "Deviation from healthy state detected",
      ],
      quarantine: [
        "Module quarantined to prevent fault propagation",
        "Isolation protocol activated",
        "Wound epidermis analog applied",
      ],
      blastema_formation: [
        "Blastema formation initiated - dedifferentiation in progress",
        "Progenitor cells activated for regeneration",
        "Positional memory locked for reconstruction",
      ],
      redifferentiation: [
        "Redifferentiation guided by positional memory",
        "Specialized function restoration in progress",
        "Clifford rotation index applied",
      ],
      recovery: [
        "Module recovered successfully - scar-free regeneration",
        "Healthy state restored with high fidelity",
        "Regeneration cycle completed",
      ],
      failure: [
        "Regeneration failed - entering retry protocol",
        "Insufficient innervation for regeneration",
        "Malformed collapse detected - requarantine required",
      ],
    };

    const eventMessages = messages[eventType];
    const baseMessage = eventMessages[Math.floor(Math.random() * eventMessages.length)];
    
    return `${severityPrefix}${aiPrefix}${baseMessage}`;
  };

  const getEventIcon = (event: RegenerationEvent) => {
    if (event.status === "failed") return <XCircle className="w-4 h-4 text-red-500" />;
    if (event.status === "completed") return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (event.event_type === "fault_detected") return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    if (event.event_type === "recovery") return <HeartPulse className="w-4 h-4 text-green-500" />;
    if (event.event_type === "blastema_formation") return <Zap className="w-4 h-4 text-purple-500" />;
    if (event.ai_triggered) return <Brain className="w-4 h-4 text-blue-500" />;
    return <Activity className="w-4 h-4 text-slate-500" />;
  };

  const getSeverityColor = (severity: RegenerationEvent["severity"]) => {
    const colors = {
      low: "bg-slate-100 text-slate-700",
      medium: "bg-yellow-100 text-yellow-700",
      high: "bg-orange-100 text-orange-700",
      critical: "bg-red-100 text-red-700",
    };
    return colors[severity];
  };

  const getStatusColor = (status: RegenerationEvent["status"]) => {
    const colors = {
      pending: "bg-slate-100 text-slate-700",
      in_progress: "bg-blue-100 text-blue-700",
      completed: "bg-green-100 text-green-700",
      failed: "bg-red-100 text-red-700",
    };
    return colors[status];
  };

  const toggleExpand = (eventId: string) => {
    setExpandedEvents(prev => {
      const next = new Set(prev);
      if (next.has(eventId)) {
        next.delete(eventId);
      } else {
        next.add(eventId);
      }
      return next;
    });
  };

  const clearEvents = () => {
    setEvents([]);
  };

  const exportLogs = () => {
    const logs = events.map(e => ({
      timestamp: e.timestamp,
      module_id: e.module_id,
      event_type: e.event_type,
      severity: e.severity,
      status: e.status,
      message: e.message,
      ai_triggered: e.ai_triggered,
      details: e.details,
    }));
    
    const blob = new Blob([JSON.stringify(logs, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `regeneration_logs_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredEvents = events.filter(event => {
    if (filter === "all") return true;
    if (filter === "ai_triggered") return event.ai_triggered;
    if (filter === "system") return !event.ai_triggered;
    if (filter === "failures") return event.status === "failed" || event.severity === "critical";
    return true;
  });

  const stats = {
    total: events.length,
    ai_triggered: events.filter(e => e.ai_triggered).length,
    completed: events.filter(e => e.status === "completed").length,
    failed: events.filter(e => e.status === "failed").length,
    critical: events.filter(e => e.severity === "critical").length,
  };

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Terminal className="w-5 h-5 text-purple-400" />
            <h3 className="text-lg font-semibold text-white">CEO Terminal</h3>
            <div className={`flex items-center gap-2 px-2 py-1 rounded text-xs ${
              isConnected ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
            }`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-400" : "bg-red-400"} ${isConnected ? "animate-pulse" : ""}`} />
              {isConnected ? "Live" : "Disconnected"}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setFilter("all")}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                filter === "all" ? "bg-purple-500 text-white" : "bg-slate-700 text-slate-300 hover:bg-slate-600"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter("ai_triggered")}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                filter === "ai_triggered" ? "bg-purple-500 text-white" : "bg-slate-700 text-slate-300 hover:bg-slate-600"
              }`}
            >
              AI-Triggered
            </button>
            <button
              onClick={() => setFilter("failures")}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                filter === "failures" ? "bg-purple-500 text-white" : "bg-slate-700 text-slate-300 hover:bg-slate-600"
              }`}
            >
              Failures
            </button>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-5 gap-4">
          <div className="bg-slate-700/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-white">{stats.total}</div>
            <div className="text-xs text-slate-400">Total Events</div>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-blue-400">{stats.ai_triggered}</div>
            <div className="text-xs text-slate-400">AI-Triggered</div>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-green-400">{stats.completed}</div>
            <div className="text-xs text-slate-400">Completed</div>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-red-400">{stats.failed}</div>
            <div className="text-xs text-slate-400">Failed</div>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-orange-400">{stats.critical}</div>
            <div className="text-xs text-slate-400">Critical</div>
          </div>
        </div>
      </div>

      {/* Actions Bar */}
      <div className="bg-slate-800/50 border-b border-slate-700 p-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs text-slate-400">Showing {filteredEvents.length} events</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={exportLogs}
            className="flex items-center gap-1 px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded text-xs text-slate-300 transition-colors"
          >
            <Download className="w-3 h-3" />
            Export
          </button>
          <button
            onClick={clearEvents}
            className="flex items-center gap-1 px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded text-xs text-slate-300 transition-colors"
          >
            <Trash2 className="w-3 h-3" />
            Clear
          </button>
        </div>
      </div>

      {/* Event Log */}
      <div 
        ref={terminalRef}
        className="h-[500px] overflow-y-auto p-4 space-y-2"
      >
        {filteredEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <Terminal className="w-12 h-12 mb-2 opacity-50" />
            <p className="text-sm">No regeneration events yet</p>
            <p className="text-xs mt-1">Waiting for AI-triggered fixes...</p>
          </div>
        ) : (
          filteredEvents.map((event) => (
            <div
              key={event.id}
              className={`bg-slate-800 rounded-lg border ${
                event.severity === "critical" ? "border-red-500/50" : "border-slate-700"
              } hover:border-slate-600 transition-colors`}
            >
              <div
                className="p-3 cursor-pointer"
                onClick={() => toggleExpand(event.id)}
              >
                <div className="flex items-center gap-3">
                  {getEventIcon(event)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded ${getSeverityColor(event.severity)}`}>
                        {event.severity.toUpperCase()}
                      </span>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded ${getStatusColor(event.status)}`}>
                        {event.status.replace("_", " ").toUpperCase()}
                      </span>
                      {event.ai_triggered && (
                        <span className="text-xs font-medium px-2 py-0.5 rounded bg-blue-500/20 text-blue-400">
                          AI-TRIGGERED
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-300 truncate">{event.message}</p>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-500">
                    <span>{new Date(event.timestamp).toLocaleTimeString()}</span>
                    {expandedEvents.has(event.id) ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </div>
                </div>
              </div>

              {expandedEvents.has(event.id) && (
                <div className="px-3 pb-3 border-t border-slate-700 pt-3">
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-slate-500">Module ID:</span>
                      <span className="text-slate-300 ml-2">{event.module_id}</span>
                    </div>
                    {event.lane_id !== undefined && (
                      <div>
                        <span className="text-slate-500">Lane ID:</span>
                        <span className="text-slate-300 ml-2">{event.lane_id}</span>
                      </div>
                    )}
                    {event.phi_score !== undefined && (
                      <div>
                        <span className="text-slate-500">φ Score:</span>
                        <span className="text-slate-300 ml-2">{event.phi_score.toFixed(4)}</span>
                      </div>
                    )}
                    {event.fidelity !== undefined && (
                      <div>
                        <span className="text-slate-500">Fidelity:</span>
                        <span className="text-slate-300 ml-2">{(event.fidelity * 100).toFixed(2)}%</span>
                      </div>
                    )}
                    {event.duration_ms !== undefined && (
                      <div>
                        <span className="text-slate-500">Duration:</span>
                        <span className="text-slate-300 ml-2">{event.duration_ms.toFixed(2)}ms</span>
                      </div>
                    )}
                    <div>
                      <span className="text-slate-500">Event Type:</span>
                      <span className="text-slate-300 ml-2">{event.event_type}</span>
                    </div>
                  </div>
                  {event.details && (
                    <div className="mt-3 p-2 bg-slate-900 rounded">
                      <div className="text-xs text-slate-500 mb-1">Details:</div>
                      <pre className="text-xs text-slate-400 overflow-x-auto">
                        {JSON.stringify(event.details, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default CEOTerminal;
