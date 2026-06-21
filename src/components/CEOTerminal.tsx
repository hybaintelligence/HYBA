/**
 * CEO Terminal - Real-time Salamander Regeneration Monitor
 *
 * Displays constant updates of AI-triggered regeneration events,
 * showing the transition from proposal-based to actual fixing capability.
 */

import React, { useState, useEffect, useRef, useCallback } from "react";
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
  Edit,
  FileText,
  CheckSquare,
  Square,
  FileText as FileExport,
} from "lucide-react";

interface RegenerationEvent {
  id: string;
  timestamp: string;
  module_id: string;
  lane_id?: number;
  event_type: "fault_detected" | "quarantine" | "blastema_formation" | "redifferentiation" | "recovery" | "failure" | "rejection" | "retry" | "multi_step_regeneration" | "agent_update" | "regeneration_step";
  severity: "low" | "medium" | "high" | "critical";
  status: "pending" | "in_progress" | "completed" | "failed" | "rejected";
  phi_score?: number;
  fidelity?: number;
  duration_ms?: number;
  message: string;
  details?: Record<string, any>;
  ai_triggered: boolean;
  // PHASE 2: Enhanced fields
  impact_score?: number;
  files_changed?: string[];
  rollback_possible?: boolean;
  approval_status?: "auto_approved" | "pending_approval" | "rejected" | "approved";
  // PHASE 3: Verification and retry fields
  verification_status?: "pending" | "passed" | "failed" | "timeout" | "skipped" | "error";
  verification_passed?: boolean;
  retry_count?: number;
  retry_history?: any[];
  ai_confidence_score?: number;
  ai_explanation?: string;
  // PHASE 5: Multi-agent fields
  regeneration_id?: string;
  steps?: Array<{
    step: string;
    status: string;
    agent: string;
    data: any;
    confidence: number;
    explanation: string;
    execution_time_ms: number;
    timestamp: number;
  }>;
  specialist_results?: Record<string, any>;
  diagnosis?: any;
  plan?: any;
  verification?: any;
  execution?: any;
  agent?: string;
  agent_result?: {
    status: string;
    confidence: number;
    explanation: string;
  };
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
  const [pendingApprovals, setPendingApprovals] = useState<RegenerationEvent[]>([]);
  const [selectedEvents, setSelectedEvents] = useState<Set<string>>(new Set());
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'reconnecting'>('disconnected');
  const [filter, setFilter] = useState<"all" | "ai_triggered" | "system" | "failures" | "pending">("all");
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());
  const terminalRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // PHASE 3: Advanced WebSocket connection with fallback
  const connectWebSocket = useCallback(() => {
    if (!token) return;

    const room = "ceo"; // Default room for CEO Terminal
    const clientId = `ceo-${Date.now()}`;
    const wsUrl = `ws://localhost:3001/api/security/regeneration/ws?room=${room}&client_id=${clientId}&token=${token}`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionStatus('connected');
      setIsConnected(true);
      reconnectAttemptsRef.current = 0;
      console.log('✅ CEO Terminal WebSocket connected to room:', room);
      
      // Clear polling if it was active
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        if (message.type === 'regeneration_event') {
          const newEvent = message.event;
          setEvents(prev => {
            const updated = [newEvent, ...prev.filter(e => e.id !== newEvent.id)];
            return updated.slice(0, maxEvents);
          });
          
          if (newEvent.approval_status === 'pending_approval') {
            setPendingApprovals(prev => {
              const updated = [newEvent, ...prev.filter(e => e.id !== newEvent.id)];
              return updated;
            });
          }
        } else if (message.type === 'connection_established') {
          console.log(`Connected to room: ${message.room} as client: ${message.client_id}`);
        } else if (message.type === 'initial_state') {
          if (message.events && Array.isArray(message.events)) {
            setEvents(message.events);
          }
          if (message.pending_approvals && Array.isArray(message.pending_approvals)) {
            setPendingApprovals(message.pending_approvals);
          }
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onclose = () => {
      setConnectionStatus('disconnected');
      setIsConnected(false);
      console.log('WebSocket closed. Starting polling fallback...');
      startPollingFallback();
      scheduleReconnect();
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('disconnected');
    };
  }, [token, maxEvents]);

  const startPollingFallback = useCallback(() => {
    if (pollingRef.current) return;
    
    pollingRef.current = setInterval(async () => {
      try {
        const response = await fetch("/api/security/regeneration/events?limit=100&include_pending=true", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (response.ok) {
          const data = await response.json();
          if (data.events && Array.isArray(data.events)) {
            setEvents(data.events);
          }
          if (data.pending_approvals && Array.isArray(data.pending_approvals)) {
            setPendingApprovals(data.pending_approvals);
          }
        }
      } catch (e) {
        console.error('Polling fallback failed:', e);
      }
    }, 3000);
  }, [token]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) return;
    
    const backoffDelay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
    reconnectAttemptsRef.current++;
    
    console.log(`Scheduling reconnect in ${backoffDelay}ms (attempt ${reconnectAttemptsRef.current})`);
    
    reconnectTimeoutRef.current = setTimeout(() => {
      reconnectTimeoutRef.current = null;
      setConnectionStatus('reconnecting');
      connectWebSocket();
    }, backoffDelay);
  }, [connectWebSocket]);

  // Heartbeat
  useEffect(() => {
    const heartbeat = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping');
      }
    }, 15000);

    return () => clearInterval(heartbeat);
  }, []);

  // Initial connection
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connectWebSocket]);

  // PHASE 2: Approval action handlers
  const handleApproval = async (eventId: string, action: "approve" | "reject" | "edit", editedParameters?: Record<string, any>) => {
    try {
      const response = await fetch("/api/security/regeneration/approve", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          event_id: eventId,
          action,
          edited_parameters: editedParameters,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        // Refresh the events after approval action
        const eventsResponse = await fetch("/api/security/regeneration/events?limit=100&include_pending=true", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (eventsResponse.ok) {
          const data = await eventsResponse.json();
          if (data.events && Array.isArray(data.events)) {
            setEvents(data.events);
          }
          if (data.pending_approvals && Array.isArray(data.pending_approvals)) {
            setPendingApprovals(data.pending_approvals);
          }
        }
      }
    } catch (error) {
      console.error("Failed to handle approval:", error);
    }
  };

  // PHASE 3: Bulk approval handler
  const handleBulkApproval = async (action: "approve" | "reject") => {
    const eventIds = Array.from(selectedEvents);
    if (eventIds.length === 0) return;

    try {
      const response = await fetch("/api/security/regeneration/bulk_approve", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          event_ids: eventIds,
          action,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        // Refresh the events after bulk approval
        const eventsResponse = await fetch("/api/security/regeneration/events?limit=100&include_pending=true", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (eventsResponse.ok) {
          const data = await eventsResponse.json();
          if (data.events && Array.isArray(data.events)) {
            setEvents(data.events);
          }
          if (data.pending_approvals && Array.isArray(data.pending_approvals)) {
            setPendingApprovals(data.pending_approvals);
          }
        }
        // Clear selection
        setSelectedEvents(new Set());
      }
    } catch (error) {
      console.error("Failed to handle bulk approval:", error);
    }
  };

  // PHASE 3: Toggle event selection for bulk actions
  const toggleEventSelection = (eventId: string) => {
    const newSelection = new Set(selectedEvents);
    if (newSelection.has(eventId)) {
      newSelection.delete(eventId);
    } else {
      newSelection.add(eventId);
    }
    setSelectedEvents(newSelection);
  };

  // PHASE 3: Select all pending events
  const selectAllPending = () => {
    const pendingIds = pendingApprovals.map(e => e.id);
    setSelectedEvents(new Set(pendingIds));
  };

  // PHASE 3: Clear selection
  const clearSelection = () => {
    setSelectedEvents(new Set());
  };

  // PHASE 3: Audit trail export
  const exportAuditTrail = async (format: "json" | "pdf") => {
    const logs = events.map(e => ({
      id: e.id,
      timestamp: e.timestamp,
      module_id: e.module_id,
      event_type: e.event_type,
      severity: e.severity,
      status: e.status,
      message: e.message,
      ai_triggered: e.ai_triggered,
      impact_score: e.impact_score,
      files_changed: e.files_changed,
      rollback_possible: e.rollback_possible,
      approval_status: e.approval_status,
      verification_status: e.verification_status,
      verification_passed: e.verification_passed,
      retry_count: e.retry_count,
      details: e.details,
    }));
    
    if (format === "json") {
      const blob = new Blob([JSON.stringify(logs, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `regeneration_audit_trail_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } else if (format === "pdf") {
      // For PDF, we'll export as JSON for now with a note
      // In production, this would use a PDF generation library
      const blob = new Blob([JSON.stringify(logs, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `regeneration_audit_trail_${Date.now()}.json`; // PDF export placeholder
      a.click();
      URL.revokeObjectURL(url);
    }
  };

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
        "Regeneration failed - module remains in quarantined state",
        "Regeneration protocol unsuccessful - escalation required",
        "Critical failure in regeneration process",
      ],
      rejection: [
        "AI-triggered regeneration rejected by human operator",
        "Regeneration proposal declined - manual intervention required",
        "AI fix rejected - alternative approach needed",
      ],
      retry: [
        "Verification failed - initiating self-healing retry",
        "Automatic retry triggered with enriched failure context",
        "Regeneration retry attempt in progress",
      ],
      // PHASE 5: Multi-agent event types
      multi_step_regeneration: [
        "Multi-step regeneration initiated with hierarchical agent coordination",
        "Orchestrator coordinating specialist agents for complex regeneration",
        "Hierarchical multi-agent pipeline activated",
      ],
      agent_update: [
        "Agent activity update received",
        "Specialist agent reporting progress",
        "Agent coordination event",
      ],
      regeneration_step: [
        "Regeneration pipeline step completed",
        "Multi-step regeneration milestone reached",
        "Pipeline stage update",
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
    if (event.event_type === "retry") return <RefreshCw className="w-4 h-4 text-orange-500" />;
    // PHASE 3: Verification status icons
    if (event.verification_status === "passed") return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (event.verification_status === "failed") return <XCircle className="w-4 h-4 text-red-500" />;
    if (event.verification_status === "timeout") return <Clock className="w-4 h-4 text-yellow-500" />;
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
    if (filter === "pending") return event.approval_status === "pending_approval";
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
              connectionStatus === 'connected' ? "bg-green-500/20 text-green-400" :
              connectionStatus === 'reconnecting' ? "bg-yellow-500/20 text-yellow-400" :
              "bg-red-500/20 text-red-400"
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                connectionStatus === 'connected' ? "bg-green-400" :
                connectionStatus === 'reconnecting' ? "bg-yellow-400 animate-pulse" :
                "bg-red-400"
              }`} />
              {connectionStatus === 'connected' ? "Live • WebSocket" :
               connectionStatus === 'reconnecting' ? "Reconnecting..." :
               "Disconnected • Polling"}
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
              onClick={() => setFilter("pending")}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                filter === "pending" ? "bg-purple-500 text-white" : "bg-slate-700 text-slate-300 hover:bg-slate-600"
              }`}
            >
              Pending ({pendingApprovals.length})
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
          {selectedEvents.size > 0 && (
            <span className="text-xs text-purple-400 font-medium">{selectedEvents.size} selected</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* PHASE 3: Bulk approval buttons */}
          {filter === "pending" && selectedEvents.size > 0 && (
            <>
              <button
                onClick={() => handleBulkApproval("approve")}
                className="flex items-center gap-1 px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-xs text-white transition-colors"
              >
                <CheckCircle className="w-3 h-3" />
                Approve All ({selectedEvents.size})
              </button>
              <button
                onClick={() => handleBulkApproval("reject")}
                className="flex items-center gap-1 px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-xs text-white transition-colors"
              >
                <XCircle className="w-3 h-3" />
                Reject All ({selectedEvents.size})
              </button>
              <button
                onClick={clearSelection}
                className="flex items-center gap-1 px-3 py-1 bg-slate-600 hover:bg-slate-700 rounded text-xs text-white transition-colors"
              >
                Clear Selection
              </button>
            </>
          )}
          {filter === "pending" && selectedEvents.size === 0 && pendingApprovals.length > 0 && (
            <button
              onClick={selectAllPending}
              className="flex items-center gap-1 px-3 py-1 bg-purple-600 hover:bg-purple-700 rounded text-xs text-white transition-colors"
            >
              <CheckSquare className="w-3 h-3" />
              Select All ({pendingApprovals.length})
            </button>
          )}
          {/* PHASE 3: Audit trail export */}
          <button
            onClick={() => exportAuditTrail("json")}
            className="flex items-center gap-1 px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded text-xs text-slate-300 transition-colors"
          >
            <FileExport className="w-3 h-3" />
            Audit Trail
          </button>
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
                  {/* PHASE 3: Checkbox for bulk selection */}
                  {event.approval_status === "pending_approval" && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleEventSelection(event.id);
                      }}
                      className="flex-shrink-0"
                    >
                      {selectedEvents.has(event.id) ? (
                        <CheckSquare className="w-4 h-4 text-purple-400" />
                      ) : (
                        <Square className="w-4 h-4 text-slate-500" />
                      )}
                    </button>
                  )}
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
                      {event.approval_status === "pending_approval" && (
                        <span className="text-xs font-medium px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-400">
                          PENDING APPROVAL
                        </span>
                      )}
                      {/* PHASE 3: Verification status badge */}
                      {event.verification_status && (
                        <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                          event.verification_status === "passed" ? "bg-green-500/20 text-green-400" :
                          event.verification_status === "failed" ? "bg-red-500/20 text-red-400" :
                          event.verification_status === "timeout" ? "bg-yellow-500/20 text-yellow-400" :
                          "bg-slate-500/20 text-slate-400"
                        }`}>
                          VERIFICATION: {event.verification_status.toUpperCase()}
                        </span>
                      )}
                      {event.retry_count && event.retry_count > 0 && (
                        <span className="text-xs font-medium px-2 py-0.5 rounded bg-orange-500/20 text-orange-400">
                          RETRY #{event.retry_count}
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
                    {/* PHASE 2: Enhanced fields display */}
                    {event.impact_score !== undefined && (
                      <div>
                        <span className="text-slate-500">Impact Score:</span>
                        <span className="text-slate-300 ml-2">{(event.impact_score * 100).toFixed(1)}%</span>
                      </div>
                    )}
                    {event.files_changed && event.files_changed.length > 0 && (
                      <div>
                        <span className="text-slate-500">Files Changed:</span>
                        <span className="text-slate-300 ml-2">{event.files_changed.length} files</span>
                      </div>
                    )}
                    {event.rollback_possible !== undefined && (
                      <div>
                        <span className="text-slate-500">Rollback Possible:</span>
                        <span className={`ml-2 ${event.rollback_possible ? "text-green-400" : "text-red-400"}`}>
                          {event.rollback_possible ? "Yes" : "No"}
                        </span>
                      </div>
                    )}
                    {/* PHASE 3: Verification status details */}
                    {event.verification_status && (
                      <div>
                        <span className="text-slate-500">Verification Status:</span>
                        <span className={`ml-2 ${
                          event.verification_status === "passed" ? "text-green-400" :
                          event.verification_status === "failed" ? "text-red-400" :
                          "text-slate-400"
                        }`}>
                          {event.verification_status}
                        </span>
                      </div>
                    )}
                    {event.retry_count !== undefined && event.retry_count > 0 && (
                      <div>
                        <span className="text-slate-500">Retry Count:</span>
                        <span className="ml-2 text-slate-300">{event.retry_count}</span>
                      </div>
                    )}
                    {/* PHASE 3: AI confidence score */}
                    {event.ai_confidence_score !== undefined && (
                      <div>
                        <span className="text-slate-500">AI Confidence:</span>
                        <span className="ml-2 text-slate-300">{(event.ai_confidence_score * 100).toFixed(1)}%</span>
                      </div>
                    )}
                  </div>
                  
                  {/* PHASE 2: Approval buttons for pending regenerations */}
                  {event.approval_status === "pending_approval" && (
                    <div className="mt-3 flex items-center gap-2">
                      <button
                        onClick={() => handleApproval(event.id, "approve")}
                        className="flex items-center gap-1 px-3 py-1.5 bg-green-600 hover:bg-green-700 rounded text-xs text-white transition-colors"
                      >
                        <CheckCircle className="w-3 h-3" />
                        Approve
                      </button>
                      <button
                        onClick={() => handleApproval(event.id, "reject")}
                        className="flex items-center gap-1 px-3 py-1.5 bg-red-600 hover:bg-red-700 rounded text-xs text-white transition-colors"
                      >
                        <XCircle className="w-3 h-3" />
                        Reject
                      </button>
                      <button
                        onClick={() => handleApproval(event.id, "edit", { severity: "low" })}
                        className="flex items-center gap-1 px-3 py-1.5 bg-slate-600 hover:bg-slate-700 rounded text-xs text-white transition-colors"
                      >
                        <Edit className="w-3 h-3" />
                        Edit
                      </button>
                    </div>
                  )}
                  
                  {/* PHASE 2: Files changed display */}
                  {event.files_changed && event.files_changed.length > 0 && expandedEvents.has(event.id) && (
                    <div className="mt-3 p-2 bg-slate-900 rounded">
                      <div className="text-xs text-slate-500 mb-1">Files to be changed:</div>
                      <ul className="text-xs text-slate-400 space-y-1">
                        {event.files_changed.map((file, idx) => (
                          <li key={idx} className="flex items-center gap-2">
                            <FileText className="w-3 h-3" />
                            {file}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {/* PHASE 3: AI explanation display */}
                  {event.ai_explanation && expandedEvents.has(event.id) && (
                    <div className="mt-3 p-2 bg-slate-900 rounded">
                      <div className="text-xs text-slate-500 mb-1">AI Explanation:</div>
                      <p className="text-xs text-slate-400">{event.ai_explanation}</p>
                    </div>
                  )}
                  
                  {/* PHASE 3: Retry history display */}
                  {event.retry_history && event.retry_history.length > 0 && expandedEvents.has(event.id) && (
                    <div className="mt-3 p-2 bg-slate-900 rounded">
                      <div className="text-xs text-slate-500 mb-1">Retry History:</div>
                      <div className="text-xs text-slate-400 space-y-2">
                        {event.retry_history.map((retry, idx) => (
                          <div key={idx} className="border-l-2 border-orange-500 pl-2">
                            <div className="font-medium">Attempt #{retry.retry_count}</div>
                            <div className="text-slate-500">{retry.timestamp}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
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
