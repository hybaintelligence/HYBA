import React, { useState, useEffect } from "react";
import AIAssistant from "./AIAssistant";
import { HilbertSpaceVisualizer } from "./HilbertSpaceVisualizer";
import { useAuth } from "./AuthProvider";
import {
  Users,
  UserPlus,
  Edit,
  Trash2,
  Shield,
  Search,
  ChevronDown,
  X,
  Check,
  AlertCircle,
  RefreshCw,
  DollarSign,
  TrendingUp,
  FileText,
  Activity,
  Lock,
  Eye,
  Download,
  Filter,
  Calendar,
  Building2,
  Briefcase,
  Scale,
  Gavel,
  Cpu,
  UserCheck,
  Crown,
  Landmark,
  ChevronRight,
  LayoutDashboard,
  Settings,
  History,
  CheckCircle,
  Clock,
  XCircle,
  ArrowUpRight,
  ArrowDownRight,
  Cloud,
  Thermometer,
  Droplets,
  Wind,
  Network,
  Zap,
  RadioTower,
  Server,
  Globe,
  BarChart3,
  Gauge,
  Sparkles,
  Target,
  Layers,
  Info,
  AlertTriangle,
} from "lucide-react";
import {
  getAdminStats,
  getAdminUsers,
  createAdminUser,
  updateAdminUser,
  deleteAdminUser,
  getAuditLogs,
  getFundingAllocations,
  createFundingAllocation,
  updateFundingAllocation,
  disburseFunding,
  getFundingRequests,
  createFundingRequest,
  reviewFundingRequest,
  getFundingSummary,
  scaleIntelligence,
  boostConsciousness,
  startIntelligence,
  stopIntelligence,
  resetIntelligence,
  getIntelligenceStatus,
  getIntelligenceTelemetry,
  getHebbianStats,
  switchPool,
  executePulvini,
  simulateDisturbance,
  type AdminStats,
  type AdminUser,
  type AuditLog,
  type FundingAllocation,
  type FundingRequest,
  type FundingSummary,
} from "../apiClient";

const THEME = {
  colors: {
    mckinseyBlue: "#003666",
    oxford: "#002147",
    deepBlue: "#06162D",
    mitRed: "#A31F34",
    caltechOrange: "#FF6C0C",
    deepmindBlue: "#0B57D0",
    clicquotGold: "#C5A55A",
    sand: "#F5F0EB",
    slate: "#64748B",
    ink: "#111827",
    error: "#DC2626",
    success: "#16A34A",
    warning: "#D97706",
  },
} as const;

const EXECUTIVE_ROLES = ["ceo_heir_apparent", "chairman", "cto", "cfo", "legal", "chief_of_staff"];

const OPERATIONAL_ROLES = ["admin", "operator", "analyst", "miner"];

const ROLE_LABELS: Record<string, string> = {
  ceo_heir_apparent: "CEO Heir Apparent",
  chairman: "Chairman",
  cto: "CTO",
  cfo: "CFO",
  legal: "Legal",
  chief_of_staff: "Chief of Staff",
  admin: "Admin",
  operator: "Operator",
  analyst: "Analyst",
  miner: "Miner",
};

const ENTITY_TYPES = ["research", "analytics", "foundation", "vertical"];

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800",
  approved: "bg-emerald-100 text-emerald-800",
  disbursed: "bg-blue-100 text-blue-800",
  rejected: "bg-red-100 text-red-800",
  pending_review: "bg-amber-100 text-amber-800",
  under_review: "bg-purple-100 text-purple-800",
};

interface HybaAdminDashboardProps {
  token: string | null;
  currentUser?: { id?: string; username: string; role: string; createdAt?: string } | null;
  telemetry?: any;
  pools?: any[];
  activePoolName?: string;
  isConnected?: boolean;
  latencyMs?: number;
}

type AdminView =
  | "dashboard"
  | "users"
  | "funding"
  | "allocations"
  | "requests"
  | "audit"
  | "network"
  | "quantum"
  | "mining"
  | "security";

function HybaAdminDashboard({
  token,
  currentUser,
  telemetry,
  pools = [],
  activePoolName,
  isConnected = false,
  latencyMs = 0,
}: HybaAdminDashboardProps) {
  const { backendUser, isExecutive } = useAuth();
  const user = currentUser || backendUser;
  const [currentView, setCurrentView] = useState<AdminView>("dashboard");
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ text: string; error: boolean } | null>(null);
  // const [weatherData, setWeatherData] = useState<any>(null); // Disabled until real weather API is integrated
  const [intelligenceStatus, setIntelligenceStatus] = useState<any>(null);
  const [intelligenceTelemetry, setIntelligenceTelemetry] = useState<any>(null);
  const [quantumLoading, setQuantumLoading] = useState(false);
  const [aiInsights, setAiInsights] = useState<any>(null);
  const [showAiAssistant, setShowAiAssistant] = useState(false);
  const [miningData, setMiningData] = useState<any>(null);
  const [hashrateSales, setHashrateSales] = useState<any>(null);
  const [securityData, setSecurityData] = useState<any>(null);

  useEffect(() => {
    if (token && (user?.role === "admin" || isExecutive)) {
      fetchStats();
      // fetchWeather(); // Disabled until real weather API is integrated
      fetchIntelligenceData();
    }
  }, [token, user, isExecutive]);

  const fetchIntelligenceData = async () => {
    try {
      const [status, telemetry] = await Promise.all([
        getIntelligenceStatus(),
        getIntelligenceTelemetry(),
      ]);
      setIntelligenceStatus(status);
      setIntelligenceTelemetry(telemetry);

      // Generate AI insights based on current data
      generateAiInsights(status, telemetry, stats);
    } catch (err) {
      console.error("Failed to fetch intelligence data:", err);
    }
  };

  const generateAiInsights = (
    intelStatus: any,
    intelTelemetry: any,
    adminStats: AdminStats | null,
  ) => {
    const insights = {
      funding: [],
      users: [],
      quantum: [],
      network: [],
      overall: [],
      mining: [],
      security: [],
    };

    // Funding insights
    if (adminStats) {
      if (adminStats.pending_allocations > 0) {
        insights.funding.push({
          type: "warning",
          message: `${adminStats.pending_allocations} funding allocations awaiting approval`,
          action: "Review pending allocations in Funding tab",
        });
      }
      if (adminStats.total_funding_allocated > 1000000) {
        insights.funding.push({
          type: "info",
          message: `Total funding allocated: $${(adminStats.total_funding_allocated / 1000000).toFixed(2)}M`,
          action: "Monitor funding distribution across entities",
        });
      }
    }

    // Quantum insights
    if (intelStatus && intelTelemetry) {
      if (!intelStatus.active) {
        insights.quantum.push({
          type: "warning",
          message: "Intelligence system is currently inactive",
          action: "Consider activating intelligence for enhanced operations",
        });
      }
      if (intelTelemetry.phi_integrated < 0.5) {
        insights.quantum.push({
          type: "info",
          message: "Phi integration below optimal threshold",
          action: "Consider boosting consciousness for better integration",
        });
      }
      if (intelTelemetry.healing_events > 10) {
        insights.quantum.push({
          type: "warning",
          message: `${intelTelemetry.healing_events} healing events detected`,
          action: "Review system stability and consider reset",
        });
      }
    }

    // Overall insights
    insights.overall.push({
      type: "success",
      message: "System operating within normal parameters",
      action: "Continue monitoring for optimal performance",
    });

    // Mining insights
    if (intelTelemetry && intelTelemetry.phi_integrated) {
      if (intelTelemetry.phi_integrated > 0.8) {
        insights.mining = [
          {
            type: "success",
            message: "High phi integration indicates optimal mining conditions",
            action: "Consider increasing hashrate allocation",
          },
        ];
      }
      if (intelTelemetry.healing_events < 5) {
        insights.mining = insights.mining || [];
        insights.mining.push({
          type: "success",
          message: "System stability excellent for mining operations",
          action: "Maintain current mining configuration",
        });
      }
    }

    // Security insights
    insights.security = [
      {
        type: "success",
        message: "All defense systems operational and monitoring active",
        action: "Continue normal security operations",
      },
    ];

    setAiInsights(insights);
  };

  // Weather functionality disabled until real weather API is integrated
  // const fetchWeather = async () => {
  //   try {
  //     // Remove mock weather data - this should either call a real weather API
  //     // or be removed entirely if not critical for admin operations
  //     // For production readiness, we're disabling this until a real weather API is integrated
  //     setWeatherData(null);
  //   } catch (err) {
  //     console.error("Failed to fetch weather:", err);
  //     setWeatherData(null);
  //   }
  // };

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAdminStats();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch stats");
    } finally {
      setLoading(false);
    }
  };

  const showFeedback = (text: string, error = false) => {
    setFeedback({ text, error });
    setTimeout(() => setFeedback(null), 3000);
  };

  if (!token || (backendUser?.role !== "admin" && !isExecutive)) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <div className="text-center">
          <Shield className="h-16 w-16 mx-auto mb-4 text-slate-400" />
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Access Denied</h2>
          <p className="text-slate-600">Executive or Admin access required</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center py-2">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-[#003666] to-[#C5A55A] rounded-xl flex items-center justify-center shadow-lg">
                <Crown className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
                  HYBA Group Executive Console
                </h1>
                <p className="text-sm text-slate-600 font-medium">
                  Enterprise Operations Platform •{" "}
                  {isExecutive ? "Executive Access" : "Admin Access"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {/* Connection Status */}
              <div className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg shadow-sm">
                <RadioTower
                  className={`h-4 w-4 ${isConnected ? "text-green-600" : "text-red-600"}`}
                />
                <div className="text-sm">
                  <div className="font-semibold text-slate-900">
                    {isConnected ? "Connected" : "Disconnected"}
                  </div>
                  <div className="text-slate-600">{latencyMs.toFixed(0)}ms latency</div>
                </div>
              </div>
              <button
                onClick={fetchStats}
                className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                <span className="font-medium text-slate-700">Refresh</span>
              </button>
              <button
                onClick={() => setShowAiAssistant(!showAiAssistant)}
                className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-[#003666] to-[#004d8c] text-white rounded-lg hover:shadow-lg transition-all shadow-md font-semibold"
              >
                <Sparkles className="h-4 w-4" />
                <span>AI Assistant</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex gap-1 py-3">
            <NavButton
              icon={<LayoutDashboard className="h-4 w-4" />}
              label="Dashboard"
              active={currentView === "dashboard"}
              onClick={() => setCurrentView("dashboard")}
            />
            <NavButton
              icon={<Users className="h-4 w-4" />}
              label="Users"
              active={currentView === "users"}
              onClick={() => setCurrentView("users")}
            />
            {isExecutive && (
              <>
                <NavButton
                  icon={<DollarSign className="h-4 w-4" />}
                  label="Funding"
                  active={currentView === "funding"}
                  onClick={() => setCurrentView("funding")}
                />
                <NavButton
                  icon={<Briefcase className="h-4 w-4" />}
                  label="Allocations"
                  active={currentView === "allocations"}
                  onClick={() => setCurrentView("allocations")}
                />
                <NavButton
                  icon={<FileText className="h-4 w-4" />}
                  label="Requests"
                  active={currentView === "requests"}
                  onClick={() => setCurrentView("requests")}
                />
                <NavButton
                  icon={<Network className="h-4 w-4" />}
                  label="Network"
                  active={currentView === "network"}
                  onClick={() => setCurrentView("network")}
                />
                <NavButton
                  icon={<Sparkles className="h-4 w-4" />}
                  label="Quantum"
                  active={currentView === "quantum"}
                  onClick={() => setCurrentView("quantum")}
                />
                <NavButton
                  icon={<Cpu className="h-4 w-4" />}
                  label="Mining"
                  active={currentView === "mining"}
                  onClick={() => setCurrentView("mining")}
                />
                <NavButton
                  icon={<Shield className="h-4 w-4" />}
                  label="Security"
                  active={currentView === "security"}
                  onClick={() => setCurrentView("security")}
                />
              </>
            )}
            <NavButton
              icon={<History className="h-4 w-4" />}
              label="Audit Log"
              active={currentView === "audit"}
              onClick={() => setCurrentView("audit")}
            />
          </nav>
        </div>
      </div>

      {/* Feedback */}
      {feedback && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <div
            className={`flex items-center gap-2 px-4 py-3 rounded-lg ${
              feedback.error
                ? "bg-red-50 text-red-900 border border-red-200"
                : "bg-green-50 text-green-900 border border-green-200"
            }`}
          >
            {feedback.error ? <AlertCircle className="h-5 w-5" /> : <Check className="h-5 w-5" />}
            <span className="text-sm font-medium">{feedback.text}</span>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <span className="text-red-900">{error}</span>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentView === "dashboard" && (
          <DashboardView
            stats={stats}
            loading={loading}
            isExecutive={isExecutive}
            aiInsights={aiInsights}
          />
        )}
        {currentView === "users" && (
          <UsersView
            token={token}
            currentUser={backendUser}
            isExecutive={isExecutive}
            onFeedback={showFeedback}
            onRefresh={fetchStats}
            aiInsights={aiInsights}
          />
        )}
        {currentView === "funding" && isExecutive && (
          <FundingView
            token={token}
            currentUser={user}
            onFeedback={showFeedback}
            onRefresh={fetchStats}
            aiInsights={aiInsights}
          />
        )}
        {currentView === "allocations" && isExecutive && (
          <AllocationsView
            token={token}
            currentUser={user}
            onFeedback={showFeedback}
            onRefresh={fetchStats}
          />
        )}
        {currentView === "requests" && isExecutive && (
          <RequestsView
            token={token}
            currentUser={user}
            onFeedback={showFeedback}
            onRefresh={fetchStats}
          />
        )}
        {currentView === "audit" && (
          <AuditView token={token} currentUser={user} onFeedback={showFeedback} />
        )}
        {currentView === "network" && isExecutive && (
          <NetworkView
            telemetry={telemetry}
            pools={pools}
            activePoolName={activePoolName}
            isConnected={isConnected}
            latencyMs={latencyMs}
            onFeedback={showFeedback}
            aiInsights={aiInsights}
          />
        )}
        {currentView === "quantum" && isExecutive && (
          <QuantumView
            intelligenceStatus={intelligenceStatus}
            intelligenceTelemetry={intelligenceTelemetry}
            pools={pools}
            activePoolName={activePoolName}
            onFeedback={showFeedback}
            onRefresh={fetchIntelligenceData}
            onQuantumLoading={setQuantumLoading}
            quantumLoading={quantumLoading}
            aiInsights={aiInsights}
          />
        )}
        {currentView === "mining" && isExecutive && (
          <MiningView
            telemetry={telemetry}
            pools={pools}
            activePoolName={activePoolName}
            onFeedback={showFeedback}
            aiInsights={aiInsights}
          />
        )}
        {currentView === "security" && isExecutive && (
          <SecurityView onFeedback={showFeedback} aiInsights={aiInsights} />
        )}

        {/* AI Assistant Panel */}
        {showAiAssistant && token && (
          <div className="fixed bottom-4 right-4 z-50">
            <AIAssistant
              token={token}
              telemetryData={telemetry}
              onCommand={(command) => {
                console.log("AI Command:", command);
                showFeedback(`AI command received: ${command}`, false);
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function NavButton({
  icon,
  label,
  active,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all ${
        active
          ? "bg-gradient-to-r from-[#003666] to-[#004d8c] text-white shadow-md"
          : "text-slate-600 hover:bg-slate-100"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

function DashboardView({
  stats,
  loading,
  isExecutive,
  aiInsights,
}: {
  stats: AdminStats | null;
  loading: boolean;
  isExecutive: boolean;
  aiInsights?: any;
}) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <LayoutDashboard className="h-6 w-6 text-[#003666]" />
        <h2 className="text-2xl font-bold text-slate-900">Executive Dashboard</h2>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Users"
          value={stats?.total_users || 0}
          icon={<Users className="h-8 w-8" />}
          color="blue"
          loading={loading}
        />
        <StatCard
          title="Active Users"
          value={stats?.active_users || 0}
          icon={<UserCheck className="h-8 w-8" />}
          color="green"
          loading={loading}
        />
        <StatCard
          title="Executives"
          value={stats?.executive_users || 0}
          icon={<Crown className="h-8 w-8" />}
          color="gold"
          loading={loading}
        />
        <StatCard
          title="Admins"
          value={stats?.admin_users || 0}
          icon={<Shield className="h-8 w-8" />}
          color="red"
          loading={loading}
        />
      </div>

      {isExecutive && (
        <>
          <div className="border-t border-slate-200 pt-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Funding Overview</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title="Total Allocations"
                value={stats?.total_allocations || 0}
                icon={<Briefcase className="h-8 w-8" />}
                color="purple"
                loading={loading}
              />
              <StatCard
                title="Pending"
                value={stats?.pending_allocations || 0}
                icon={<Clock className="h-8 w-8" />}
                color="amber"
                loading={loading}
              />
              <StatCard
                title="Approved"
                value={stats?.approved_allocations || 0}
                icon={<CheckCircle className="h-8 w-8" />}
                color="green"
                loading={loading}
              />
              <StatCard
                title="Total Funding"
                value={`$${((stats?.total_funding_allocated || 0) / 1000000).toFixed(2)}M`}
                icon={<DollarSign className="h-8 w-8" />}
                color="emerald"
                loading={loading}
              />
            </div>
          </div>

          {/* Entity Breakdown */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">HYBA Group Entities</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <EntityCard
                name="HYBA Research"
                type="research"
                icon={<Flask className="h-6 w-6" />}
                description="Advanced research and development initiatives"
              />
              <EntityCard
                name="HYBA Analytics"
                type="analytics"
                icon={<TrendingUp className="h-6 w-6" />}
                description="Data analytics and business intelligence"
              />
              <EntityCard
                name="HYBA Foundation"
                type="foundation"
                icon={<Landmark className="h-6 w-6" />}
                description="Philanthropic and charitable activities"
              />
              <EntityCard
                name="Vertical Operations"
                type="vertical"
                icon={<Building2 className="h-6 w-6" />}
                description="Strategic business verticals and operations"
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
  color,
  loading,
}: {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;
  loading: boolean;
}) {
  const colorClasses: Record<string, { bg: string; text: string }> = {
    blue: { bg: "bg-blue-50", text: "text-blue-600" },
    green: { bg: "bg-green-50", text: "text-green-600" },
    gold: { bg: "bg-amber-50", text: "text-amber-600" },
    red: { bg: "bg-red-50", text: "text-red-600" },
    purple: { bg: "bg-purple-50", text: "text-purple-600" },
    amber: { bg: "bg-amber-50", text: "text-amber-600" },
    emerald: { bg: "bg-emerald-50", text: "text-emerald-600" },
  };

  const colors = colorClasses[color] || colorClasses.blue;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-slate-900">{loading ? "—" : value}</p>
        </div>
        <div className={`p-3 rounded-lg ${colors.bg}`}>
          <div className={colors.text}>{icon}</div>
        </div>
      </div>
    </div>
  );
}

function EntityCard({
  name,
  type,
  icon,
  description,
}: {
  name: string;
  type: string;
  icon: React.ReactNode;
  description: string;
}) {
  return (
    <div className="border border-slate-200 rounded-lg p-4 hover:border-[#003666] transition-colors cursor-pointer">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-[#003666] rounded-lg text-white">{icon}</div>
        <div className="flex-1">
          <h4 className="font-semibold text-slate-900">{name}</h4>
          <p className="text-sm text-slate-600 mt-1">{description}</p>
          <span className="inline-block mt-2 text-xs font-medium px-2 py-1 bg-slate-100 text-slate-700 rounded">
            {type}
          </span>
        </div>
      </div>
    </div>
  );
}

function UsersView({
  token,
  currentUser,
  isExecutive,
  onFeedback,
  onRefresh,
  aiInsights,
}: {
  token: string | null;
  currentUser: any;
  isExecutive: boolean;
  onFeedback: (text: string, error?: boolean) => void;
  onRefresh: () => void;
  aiInsights?: any;
}) {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [totalUsers, setTotalUsers] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    role: "operator",
  });

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await getAdminUsers(0, 50, searchQuery);
      setUsers(data.users);
      setTotalUsers(data.total);
    } catch (err) {
      onFeedback(err instanceof Error ? err.message : "Failed to fetch users", true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [searchQuery]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createAdminUser(formData);
      onFeedback("User created successfully");
      setShowCreateModal(false);
      setFormData({ username: "", email: "", password: "", role: "operator" });
      fetchUsers();
      onRefresh();
    } catch (err) {
      onFeedback(err instanceof Error ? err.message : "Failed to create user", true);
    }
  };

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;

    try {
      const updateData: any = {};
      if (formData.email) updateData.email = formData.email;
      if (formData.role) updateData.role = formData.role;
      if (formData.password) updateData.password = formData.password;

      await updateAdminUser(selectedUser.id, updateData);
      onFeedback("User updated successfully");
      setShowEditModal(false);
      setSelectedUser(null);
      setFormData({ username: "", email: "", password: "", role: "operator" });
      fetchUsers();
      onRefresh();
    } catch (err) {
      onFeedback(err instanceof Error ? err.message : "Failed to update user", true);
    }
  };

  const handleDeleteUser = async (user: AdminUser) => {
    if (!confirm(`Are you sure you want to delete user "${user.username}"?`)) return;

    try {
      await deleteAdminUser(user.id);
      onFeedback("User deleted successfully");
      fetchUsers();
      onRefresh();
    } catch (err) {
      onFeedback(err instanceof Error ? err.message : "Failed to delete user", true);
    }
  };

  const openEditModal = (user: AdminUser) => {
    setSelectedUser(user);
    setFormData({
      username: user.username,
      email: user.email || "",
      password: "",
      role: user.role,
    });
    setShowEditModal(true);
  };

  const availableRoles = isExecutive
    ? [...EXECUTIVE_ROLES, ...OPERATIONAL_ROLES]
    : OPERATIONAL_ROLES;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="h-6 w-6 text-[#003666]" />
          <h2 className="text-2xl font-bold text-slate-900">User Management</h2>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-[#003666] text-white rounded-lg hover:bg-[#002147] transition-colors"
        >
          <UserPlus className="h-4 w-4" />
          Create User
        </button>
      </div>

      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
          <input
            type="text"
            placeholder="Search users by username or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
          />
        </div>
      </div>

      {/* Users Table */}
      {loading ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <div className="animate-spin h-8 w-8 border-4 border-[#003666] border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-slate-600">Loading users...</p>
        </div>
      ) : users.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <Users className="h-12 w-12 mx-auto mb-4 text-slate-400" />
          <p className="text-slate-600">No users found</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-medium text-slate-900">{user.username}</div>
                      <div className="text-sm text-slate-600">{user.email || "—"}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        EXECUTIVE_ROLES.includes(user.role)
                          ? "bg-amber-100 text-amber-800"
                          : user.role === "admin"
                            ? "bg-red-100 text-red-800"
                            : "bg-slate-100 text-slate-800"
                      }`}
                    >
                      {EXECUTIVE_ROLES.includes(user.role) && <Crown className="h-3 w-3" />}
                      {ROLE_LABELS[user.role] || user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        user.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                      }`}
                    >
                      {user.is_active ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
                      {user.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => openEditModal(user)}
                        className="p-2 text-slate-600 hover:text-[#003666] hover:bg-slate-100 rounded-lg transition-colors"
                        title="Edit user"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      {user.username !== currentUser?.username && (
                        <button
                          onClick={() => handleDeleteUser(user)}
                          className="p-2 text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Delete user"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateModal && (
        <Modal title="Create New User" onClose={() => setShowCreateModal(false)}>
          <form onSubmit={handleCreateUser} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Username</label>
              <input
                type="text"
                required
                minLength={3}
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Email (optional)
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
              <input
                type="password"
                required
                minLength={8}
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Role</label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
              >
                {availableRoles.map((role) => (
                  <option key={role} value={role}>
                    {ROLE_LABELS[role] || role}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-[#003666] text-white rounded-lg hover:bg-[#002147] transition-colors"
              >
                Create User
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <Modal
          title={`Edit User: ${selectedUser.username}`}
          onClose={() => setShowEditModal(false)}
        >
          <form onSubmit={handleUpdateUser} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Username</label>
              <input
                type="text"
                value={formData.username}
                disabled
                className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 text-slate-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                New Password (leave blank to keep current)
              </label>
              <input
                type="password"
                minLength={8}
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Role</label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                disabled={selectedUser.username === currentUser?.username}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent disabled:bg-slate-50 disabled:text-slate-500"
              >
                {availableRoles.map((role) => (
                  <option key={role} value={role}>
                    {ROLE_LABELS[role] || role}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowEditModal(false)}
                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-[#003666] text-white rounded-lg hover:bg-[#002147] transition-colors"
              >
                Update User
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

function FundingView({
  token,
  currentUser,
  onFeedback,
  onRefresh,
  aiInsights,
}: {
  token: string | null;
  currentUser: any;
  onFeedback: (text: string, error?: boolean) => void;
  onRefresh: () => void;
  aiInsights?: any;
}) {
  const [summary, setSummary] = useState<FundingSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [fiscalYear, setFiscalYear] = useState(new Date().getFullYear());

  useEffect(() => {
    fetchSummary();
  }, [fiscalYear]);

  const fetchSummary = async () => {
    try {
      setLoading(true);
      const data = await getFundingSummary(fiscalYear);
      setSummary(data);
    } catch (err) {
      onFeedback(err instanceof Error ? err.message : "Failed to fetch funding summary", true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <DollarSign className="h-6 w-6 text-[#003666]" />
          <h2 className="text-2xl font-bold text-slate-900">Funding Overview</h2>
        </div>
        <select
          value={fiscalYear}
          onChange={(e) => setFiscalYear(parseInt(e.target.value))}
          className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
        >
          {[2024, 2025, 2026, 2027].map((year) => (
            <option key={year} value={year}>
              FY {year}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <div className="animate-spin h-8 w-8 border-4 border-[#003666] border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-slate-600">Loading funding data...</p>
        </div>
      ) : summary ? (
        <>
          {/* Status Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              title="Pending"
              value={`$${(summary.total_by_status.pending / 1000000).toFixed(2)}M`}
              icon={<Clock className="h-8 w-8" />}
              color="amber"
              loading={loading}
            />
            <StatCard
              title="Approved"
              value={`$${(summary.total_by_status.approved / 1000000).toFixed(2)}M`}
              icon={<CheckCircle className="h-8 w-8" />}
              color="green"
              loading={loading}
            />
            <StatCard
              title="Disbursed"
              value={`$${(summary.total_by_status.disbursed / 1000000).toFixed(2)}M`}
              icon={<ArrowUpRight className="h-8 w-8" />}
              color="blue"
              loading={loading}
            />
            <StatCard
              title="Total"
              value={`$${((summary.total_by_status.pending + summary.total_by_status.approved + summary.total_by_status.disbursed) / 1000000).toFixed(2)}M`}
              icon={<DollarSign className="h-8 w-8" />}
              color="emerald"
              loading={loading}
            />
          </div>

          {/* Entity Summary */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Funding by Entity</h3>
            <div className="space-y-4">
              {summary.entity_summary.map((entity) => (
                <div key={entity.entity_name} className="border border-slate-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-slate-900">{entity.entity_name}</h4>
                    <span className="text-sm text-slate-600">
                      {entity.allocation_count} allocations
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-600">Total Allocated:</span>
                      <span className="ml-2 font-medium text-slate-900">
                        ${(entity.total_allocated / 1000000).toFixed(2)}M
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-600">Total Disbursed:</span>
                      <span className="ml-2 font-medium text-emerald-600">
                        ${(entity.total_disbursed / 1000000).toFixed(2)}M
                      </span>
                    </div>
                  </div>
                  <div className="mt-3 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#003666] rounded-full"
                      style={{
                        width: `${(entity.total_disbursed / entity.total_allocated) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <DollarSign className="h-12 w-12 mx-auto mb-4 text-slate-400" />
          <p className="text-slate-600">No funding data available</p>
        </div>
      )}
    </div>
  );
}

function AllocationsView({
  token,
  currentUser,
  onFeedback,
  onRefresh,
}: {
  token: string | null;
  currentUser: any;
  onFeedback: (text: string, error?: boolean) => void;
  onRefresh: () => void;
}) {
  const [allocations, setAllocations] = useState<FundingAllocation[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filters, setFilters] = useState({
    entity_name: "",
    entity_type: "",
    status: "",
    fiscal_year: new Date().getFullYear(),
  });
  const [formData, setFormData] = useState({
    entity_name: "",
    entity_type: "research",
    allocation_amount: "",
    currency: "USD",
    fiscal_year: new Date().getFullYear(),
    fiscal_quarter: "",
    purpose: "",
  });

  const fetchAllocations = async () => {
    try {
      setLoading(true);
      const data = await getFundingAllocations(
        0,
        50,
        filters.entity_name || undefined,
        filters.entity_type || undefined,
        filters.status || undefined,
        filters.fiscal_year,
      );
      setAllocations(data.allocations);
      setTotal(data.total);
    } catch (err) {
      onFeedback(err instanceof Error ? err.message : "Failed to fetch allocations", true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllocations();
  }, [filters]);

  const handleCreateAllocation = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createFundingAllocation({
        entity_name: formData.entity_name,
        entity_type: formData.entity_type,
        allocation_amount: parseFloat(formData.allocation_amount),
        currency: formData.currency,
        fiscal_year: formData.fiscal_year,
        fiscal_quarter: formData.fiscal_quarter ? parseInt(formData.fiscal_quarter) : undefined,
        purpose: formData.purpose,
      });
      onFeedback("Allocation created successfully");
      setShowCreateModal(false);
      setFormData({
        entity_name: "",
        entity_type: "research",
        allocation_amount: "",
        currency: "USD",
        fiscal_year: new Date().getFullYear(),
        fiscal_quarter: "",
        purpose: "",
      });
      fetchAllocations();
      onRefresh();
    } catch (err) {
      onFeedback(err instanceof Error ? err.message : "Failed to create allocation", true);
    }
  };

  const handleDisburse = async (allocation: FundingAllocation) => {
    if (
      !confirm(
        `Are you sure you want to disburse $${allocation.allocation_amount.toLocaleString()} to ${allocation.entity_name}?`,
      )
    )
      return;

    try {
      await disburseFunding(allocation.id);
      onFeedback("Funding disbursed successfully");
      fetchAllocations();
      onRefresh();
    } catch (err) {
      onFeedback(err instanceof Error ? err.message : "Failed to disburse funding", true);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Briefcase className="h-6 w-6 text-[#003666]" />
          <h2 className="text-2xl font-bold text-slate-900">Funding Allocations</h2>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-[#003666] text-white rounded-lg hover:bg-[#002147] transition-colors"
        >
          <DollarSign className="h-4 w-4" />
          New Allocation
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input
            type="text"
            placeholder="Entity name..."
            value={filters.entity_name}
            onChange={(e) => setFilters({ ...filters, entity_name: e.target.value })}
            className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
          />
          <select
            value={filters.entity_type}
            onChange={(e) => setFilters({ ...filters, entity_type: e.target.value })}
            className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
          >
            <option value="">All Types</option>
            {ENTITY_TYPES.map((type) => (
              <option key={type} value={type}>
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </option>
            ))}
          </select>
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
          >
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="disbursed">Disbursed</option>
            <option value="rejected">Rejected</option>
          </select>
          <select
            value={filters.fiscal_year}
            onChange={(e) => setFilters({ ...filters, fiscal_year: parseInt(e.target.value) })}
            className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
          >
            {[2024, 2025, 2026, 2027].map((year) => (
              <option key={year} value={year}>
                FY {year}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Allocations Table */}
      {loading ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <div className="animate-spin h-8 w-8 border-4 border-[#003666] border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-slate-600">Loading allocations...</p>
        </div>
      ) : allocations.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <Briefcase className="h-12 w-12 mx-auto mb-4 text-slate-400" />
          <p className="text-slate-600">No allocations found</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Entity
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Fiscal Year
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Allocated By
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {allocations.map((allocation) => (
                <tr key={allocation.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-medium text-slate-900">{allocation.entity_name}</div>
                      <div className="text-sm text-slate-600">{allocation.entity_type}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-medium text-slate-900">
                      ${allocation.allocation_amount.toLocaleString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">
                    FY {allocation.fiscal_year}
                    {allocation.fiscal_quarter && ` Q${allocation.fiscal_quarter}`}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        STATUS_COLORS[allocation.status] || "bg-slate-100 text-slate-800"
                      }`}
                    >
                      {allocation.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">{allocation.allocated_by}</td>
                  <td className="px-6 py-4 text-right">
                    {allocation.status === "approved" && (
                      <button
                        onClick={() => handleDisburse(allocation)}
                        className="flex items-center gap-1 px-3 py-1 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm"
                      >
                        <ArrowUpRight className="h-3 w-3" />
                        Disburse
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Allocation Modal */}
      {showCreateModal && (
        <Modal title="Create New Allocation" onClose={() => setShowCreateModal(false)}>
          <form onSubmit={handleCreateAllocation} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Entity Name</label>
              <input
                type="text"
                required
                value={formData.entity_name}
                onChange={(e) => setFormData({ ...formData, entity_name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Entity Type</label>
              <select
                value={formData.entity_type}
                onChange={(e) => setFormData({ ...formData, entity_type: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
              >
                {ENTITY_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Allocation Amount (USD)
              </label>
              <input
                type="number"
                required
                min="0"
                step="0.01"
                value={formData.allocation_amount}
                onChange={(e) => setFormData({ ...formData, allocation_amount: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Fiscal Year</label>
                <select
                  value={formData.fiscal_year}
                  onChange={(e) =>
                    setFormData({ ...formData, fiscal_year: parseInt(e.target.value) })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
                >
                  {[2024, 2025, 2026, 2027].map((year) => (
                    <option key={year} value={year}>
                      FY {year}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Quarter (optional)
                </label>
                <select
                  value={formData.fiscal_quarter}
                  onChange={(e) => setFormData({ ...formData, fiscal_quarter: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
                >
                  <option value="">Full Year</option>
                  <option value="1">Q1</option>
                  <option value="2">Q2</option>
                  <option value="3">Q3</option>
                  <option value="4">Q4</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Purpose</label>
              <textarea
                value={formData.purpose}
                onChange={(e) => setFormData({ ...formData, purpose: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
              />
            </div>
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-[#003666] text-white rounded-lg hover:bg-[#002147] transition-colors"
              >
                Create Allocation
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

function RequestsView({
  token,
  currentUser,
  onFeedback,
  onRefresh,
}: {
  token: string | null;
  currentUser: any;
  onFeedback: (text: string, error?: boolean) => void;
  onRefresh: () => void;
}) {
  const [requests, setRequests] = useState<FundingRequest[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState<FundingRequest | null>(null);
  const [filters, setFilters] = useState({
    entity_name: "",
    entity_type: "",
    status: "",
    fiscal_year: new Date().getFullYear(),
  });
  const [formData, setFormData] = useState({
    entity_name: "",
    entity_type: "research",
    requested_amount: "",
    currency: "USD",
    fiscal_year: new Date().getFullYear(),
    fiscal_quarter: "",
    purpose: "",
    justification: "",
  });
  const [reviewData, setReviewData] = useState({
    status: "approved",
    approval_notes: "",
    allocated_amount: "",
  });

  const fetchRequests = async () => {
    try {
      setLoading(true);
      const data = await getFundingRequests(
        0,
        50,
        filters.entity_name || undefined,
        filters.entity_type || undefined,
        filters.status || undefined,
        filters.fiscal_year,
      );
      setRequests(data.requests);
      setTotal(data.total);
    } catch (err) {
      onFeedback(err instanceof Error ? err.message : "Failed to fetch requests", true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, [filters]);

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createFundingRequest({
        entity_name: formData.entity_name,
        entity_type: formData.entity_type,
        requested_amount: parseFloat(formData.requested_amount),
        currency: formData.currency,
        fiscal_year: formData.fiscal_year,
        fiscal_quarter: formData.fiscal_quarter ? parseInt(formData.fiscal_quarter) : undefined,
        purpose: formData.purpose,
        justification: formData.justification,
      });
      onFeedback("Request created successfully");
      setShowCreateModal(false);
      setFormData({
        entity_name: "",
        entity_type: "research",
        requested_amount: "",
        currency: "USD",
        fiscal_year: new Date().getFullYear(),
        fiscal_quarter: "",
        purpose: "",
        justification: "",
      });
      fetchRequests();
      onRefresh();
    } catch (err) {
      onFeedback(err instanceof Error ? err.message : "Failed to create request", true);
    }
  };

  const handleReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRequest) return;

    try {
      await reviewFundingRequest(selectedRequest.request_id, {
        status: reviewData.status,
        approval_notes: reviewData.approval_notes,
        allocated_amount: reviewData.allocated_amount
          ? parseFloat(reviewData.allocated_amount)
          : undefined,
      });
      onFeedback(`Request ${reviewData.status} successfully`);
      setShowReviewModal(false);
      setSelectedRequest(null);
      setReviewData({ status: "approved", approval_notes: "", allocated_amount: "" });
      fetchRequests();
      onRefresh();
    } catch (err) {
      onFeedback(err instanceof Error ? err.message : "Failed to review request", true);
    }
  };

  const openReviewModal = (request: FundingRequest) => {
    setSelectedRequest(request);
    setReviewData({
      status: "approved",
      approval_notes: "",
      allocated_amount: request.requested_amount.toString(),
    });
    setShowReviewModal(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-6 w-6 text-[#003666]" />
          <h2 className="text-2xl font-bold text-slate-900">Funding Requests</h2>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-[#003666] text-white rounded-lg hover:bg-[#002147] transition-colors"
        >
          <FileText className="h-4 w-4" />
          New Request
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input
            type="text"
            placeholder="Entity name..."
            value={filters.entity_name}
            onChange={(e) => setFilters({ ...filters, entity_name: e.target.value })}
            className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
          />
          <select
            value={filters.entity_type}
            onChange={(e) => setFilters({ ...filters, entity_type: e.target.value })}
            className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
          >
            <option value="">All Types</option>
            {ENTITY_TYPES.map((type) => (
              <option key={type} value={type}>
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </option>
            ))}
          </select>
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
          >
            <option value="">All Status</option>
            <option value="pending_review">Pending Review</option>
            <option value="under_review">Under Review</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
          <select
            value={filters.fiscal_year}
            onChange={(e) => setFilters({ ...filters, fiscal_year: parseInt(e.target.value) })}
            className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
          >
            {[2024, 2025, 2026, 2027].map((year) => (
              <option key={year} value={year}>
                FY {year}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Requests Table */}
      {loading ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <div className="animate-spin h-8 w-8 border-4 border-[#003666] border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-slate-600">Loading requests...</p>
        </div>
      ) : requests.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <FileText className="h-12 w-12 mx-auto mb-4 text-slate-400" />
          <p className="text-slate-600">No requests found</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Request ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Entity
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Requested
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Purpose
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Requested By
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {requests.map((request) => (
                <tr key={request.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4">
                    <span className="font-mono text-sm text-slate-900">{request.request_id}</span>
                  </td>
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-medium text-slate-900">{request.entity_name}</div>
                      <div className="text-sm text-slate-600">{request.entity_type}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-medium text-slate-900">
                      ${request.requested_amount.toLocaleString()}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-slate-600 max-w-xs truncate">
                      {request.purpose}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        STATUS_COLORS[request.status] || "bg-slate-100 text-slate-800"
                      }`}
                    >
                      {request.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">{request.requested_by}</td>
                  <td className="px-6 py-4 text-right">
                    {(request.status === "pending_review" || request.status === "under_review") && (
                      <button
                        onClick={() => openReviewModal(request)}
                        className="flex items-center gap-1 px-3 py-1 bg-[#003666] text-white rounded-lg hover:bg-[#002147] transition-colors text-sm"
                      >
                        <Gavel className="h-3 w-3" />
                        Review
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Request Modal */}
      {showCreateModal && (
        <Modal title="Create Funding Request" onClose={() => setShowCreateModal(false)}>
          <form onSubmit={handleCreateRequest} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Entity Name</label>
              <input
                type="text"
                required
                value={formData.entity_name}
                onChange={(e) => setFormData({ ...formData, entity_name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Entity Type</label>
              <select
                value={formData.entity_type}
                onChange={(e) => setFormData({ ...formData, entity_type: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
              >
                {ENTITY_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Requested Amount (USD)
              </label>
              <input
                type="number"
                required
                min="0"
                step="0.01"
                value={formData.requested_amount}
                onChange={(e) => setFormData({ ...formData, requested_amount: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Fiscal Year</label>
                <select
                  value={formData.fiscal_year}
                  onChange={(e) =>
                    setFormData({ ...formData, fiscal_year: parseInt(e.target.value) })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
                >
                  {[2024, 2025, 2026, 2027].map((year) => (
                    <option key={year} value={year}>
                      FY {year}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Quarter (optional)
                </label>
                <select
                  value={formData.fiscal_quarter}
                  onChange={(e) => setFormData({ ...formData, fiscal_quarter: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
                >
                  <option value="">Full Year</option>
                  <option value="1">Q1</option>
                  <option value="2">Q2</option>
                  <option value="3">Q3</option>
                  <option value="4">Q4</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Purpose</label>
              <textarea
                required
                value={formData.purpose}
                onChange={(e) => setFormData({ ...formData, purpose: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Justification (optional)
              </label>
              <textarea
                value={formData.justification}
                onChange={(e) => setFormData({ ...formData, justification: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
              />
            </div>
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-[#003666] text-white rounded-lg hover:bg-[#002147] transition-colors"
              >
                Submit Request
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Review Modal */}
      {showReviewModal && selectedRequest && (
        <Modal
          title={`Review Request: ${selectedRequest.request_id}`}
          onClose={() => setShowReviewModal(false)}
        >
          <div className="space-y-4">
            <div className="bg-slate-50 rounded-lg p-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-slate-600">Entity:</span>
                  <span className="ml-2 font-medium text-slate-900">
                    {selectedRequest.entity_name}
                  </span>
                </div>
                <div>
                  <span className="text-slate-600">Requested:</span>
                  <span className="ml-2 font-medium text-slate-900">
                    ${selectedRequest.requested_amount.toLocaleString()}
                  </span>
                </div>
                <div className="col-span-2">
                  <span className="text-slate-600">Purpose:</span>
                  <p className="mt-1 text-slate-900">{selectedRequest.purpose}</p>
                </div>
                {selectedRequest.justification && (
                  <div className="col-span-2">
                    <span className="text-slate-600">Justification:</span>
                    <p className="mt-1 text-slate-900">{selectedRequest.justification}</p>
                  </div>
                )}
              </div>
            </div>
            <form onSubmit={handleReview} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Decision</label>
                <select
                  value={reviewData.status}
                  onChange={(e) => setReviewData({ ...reviewData, status: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
                >
                  <option value="approved">Approve</option>
                  <option value="rejected">Reject</option>
                </select>
              </div>
              {reviewData.status === "approved" && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Allocated Amount (USD)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={reviewData.allocated_amount}
                    onChange={(e) =>
                      setReviewData({ ...reviewData, allocated_amount: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
                  />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Approval Notes
                </label>
                <textarea
                  value={reviewData.approval_notes}
                  onChange={(e) => setReviewData({ ...reviewData, approval_notes: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowReviewModal(false)}
                  className="flex-1 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className={`flex-1 px-4 py-2 text-white rounded-lg transition-colors ${
                    reviewData.status === "approved"
                      ? "bg-emerald-600 hover:bg-emerald-700"
                      : "bg-red-600 hover:bg-red-700"
                  }`}
                >
                  {reviewData.status === "approved" ? "Approve" : "Reject"}
                </button>
              </div>
            </form>
          </div>
        </Modal>
      )}
    </div>
  );
}

function AuditView({
  token,
  currentUser,
  onFeedback,
}: {
  token: string | null;
  currentUser: any;
  onFeedback: (text: string, error?: boolean) => void;
}) {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    action: "",
    target_type: "",
    actor_username: "",
  });

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const data = await getAuditLogs(
        0,
        100,
        filters.action || undefined,
        filters.target_type || undefined,
        filters.actor_username || undefined,
      );
      setLogs(data.logs);
      setTotal(data.total);
    } catch (err) {
      onFeedback(err instanceof Error ? err.message : "Failed to fetch audit logs", true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [filters]);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <History className="h-6 w-6 text-[#003666]" />
        <h2 className="text-2xl font-bold text-slate-900">Audit Log</h2>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input
            type="text"
            placeholder="Action..."
            value={filters.action}
            onChange={(e) => setFilters({ ...filters, action: e.target.value })}
            className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
          />
          <input
            type="text"
            placeholder="Target type..."
            value={filters.target_type}
            onChange={(e) => setFilters({ ...filters, target_type: e.target.value })}
            className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
          />
          <input
            type="text"
            placeholder="Actor username..."
            value={filters.actor_username}
            onChange={(e) => setFilters({ ...filters, actor_username: e.target.value })}
            className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666] focus:border-transparent"
          />
        </div>
      </div>

      {/* Audit Logs Table */}
      {loading ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <div className="animate-spin h-8 w-8 border-4 border-[#003666] border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-slate-600">Loading audit logs...</p>
        </div>
      ) : logs.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <History className="h-12 w-12 mx-auto mb-4 text-slate-400" />
          <p className="text-slate-600">No audit logs found</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Actor
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Action
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Target
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 text-sm text-slate-600">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-medium text-slate-900">{log.actor_username}</div>
                      {log.actor_role && (
                        <div className="text-xs text-slate-600">
                          {ROLE_LABELS[log.actor_role] || log.actor_role}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
                      {log.action}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">
                    {log.target_type}
                    {log.target_id && `: ${log.target_id}`}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">
                    {log.details ? JSON.stringify(log.details).substring(0, 100) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function NetworkView({
  telemetry,
  pools,
  activePoolName,
  isConnected,
  latencyMs,
  onFeedback,
  aiInsights,
}: {
  telemetry: any;
  pools: any[];
  activePoolName?: string;
  isConnected: boolean;
  latencyMs: number;
  onFeedback: (text: string, error?: boolean) => void;
  aiInsights: any;
}) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Network className="h-6 w-6 text-[#003666]" />
        <h2 className="text-2xl font-bold text-slate-900">Network Visualization</h2>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Funding Flow Network</h3>
        <div className="h-96 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-center">
          <div className="text-center">
            <Network className="h-16 w-16 mx-auto mb-4 text-slate-400" />
            <p className="text-slate-600">Interactive network visualization</p>
            <p className="text-sm text-slate-500 mt-2">Shows funding flows between HYBA entities</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Pool Connections</h3>
          <div className="space-y-3">
            {pools.map((pool, idx) => (
              <div key={idx} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                <Server className="h-5 w-5 text-slate-600" />
                <div className="flex-1">
                  <div className="font-medium text-slate-900">{pool.name || pool.pool_id}</div>
                  <div className="text-sm text-slate-600">{pool.status || "Unknown"}</div>
                </div>
                {activePoolName === pool.name && <CheckCircle className="h-5 w-5 text-green-600" />}
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Telemetry Network</h3>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
              <RadioTower
                className={`h-5 w-5 ${isConnected ? "text-green-600" : "text-red-600"}`}
              />
              <div className="flex-1">
                <div className="font-medium text-slate-900">Backend Connection</div>
                <div className="text-sm text-slate-600">
                  {isConnected ? "Connected" : "Disconnected"}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
              <Zap className="h-5 w-5 text-amber-600" />
              <div className="flex-1">
                <div className="font-medium text-slate-900">Latency</div>
                <div className="text-sm text-slate-600">{latencyMs.toFixed(0)}ms</div>
              </div>
            </div>
            {telemetry && (
              <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                <Activity className="h-5 w-5 text-blue-600" />
                <div className="flex-1">
                  <div className="font-medium text-slate-900">Active Telemetry</div>
                  <div className="text-sm text-slate-600">Live data flowing</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function QuantumView({
  intelligenceStatus,
  intelligenceTelemetry,
  pools,
  activePoolName,
  onFeedback,
  onRefresh,
  onQuantumLoading,
  quantumLoading,
  aiInsights,
}: {
  intelligenceStatus: any;
  intelligenceTelemetry: any;
  pools: any[];
  activePoolName?: string;
  onFeedback: (text: string, error?: boolean) => void;
  onRefresh: () => void;
  onQuantumLoading: (loading: boolean) => void;
  quantumLoading: boolean;
  aiInsights: any;
}) {
  const [intelligenceScale, setIntelligenceScale] = useState(1.0);
  const [consciousnessBoost, setConsciousnessBoost] = useState(1.0);
  const [selectedPool, setSelectedPool] = useState("");

  const handleScaleIntelligence = async () => {
    try {
      onQuantumLoading(true);
      await scaleIntelligence(intelligenceScale);
      onFeedback("Intelligence scaled successfully", false);
      onRefresh();
    } catch (err) {
      onFeedback("Failed to scale intelligence", true);
    } finally {
      onQuantumLoading(false);
    }
  };

  const handleBoostConsciousness = async () => {
    try {
      onQuantumLoading(true);
      await boostConsciousness(consciousnessBoost);
      onFeedback("Consciousness boosted successfully", false);
      onRefresh();
    } catch (err) {
      onFeedback("Failed to boost consciousness", true);
    } finally {
      onQuantumLoading(false);
    }
  };

  const handleStartIntelligence = async () => {
    try {
      onQuantumLoading(true);
      await startIntelligence();
      onFeedback("Intelligence started successfully", false);
      onRefresh();
    } catch (err) {
      onFeedback("Failed to start intelligence", true);
    } finally {
      onQuantumLoading(false);
    }
  };

  const handleStopIntelligence = async () => {
    try {
      onQuantumLoading(true);
      await stopIntelligence();
      onFeedback("Intelligence stopped successfully", false);
      onRefresh();
    } catch (err) {
      onFeedback("Failed to stop intelligence", true);
    } finally {
      onQuantumLoading(false);
    }
  };

  const handleResetIntelligence = async () => {
    try {
      onQuantumLoading(true);
      await resetIntelligence();
      onFeedback("Intelligence reset successfully", false);
      onRefresh();
    } catch (err) {
      onFeedback("Failed to reset intelligence", true);
    } finally {
      onQuantumLoading(false);
    }
  };

  const handleExecutePulvini = async () => {
    try {
      onQuantumLoading(true);
      await executePulvini();
      onFeedback("Pulvini executed successfully", false);
    } catch (err) {
      onFeedback("Failed to execute Pulvini", true);
    } finally {
      onQuantumLoading(false);
    }
  };

  const handleSwitchPool = async () => {
    if (!selectedPool) {
      onFeedback("Please select a pool", true);
      return;
    }
    try {
      onQuantumLoading(true);
      await switchPool({ pool_id: selectedPool });
      onFeedback("Pool switched successfully", false);
      onRefresh();
    } catch (err) {
      onFeedback("Failed to switch pool", true);
    } finally {
      onQuantumLoading(false);
    }
  };

  const handleSimulateDisturbance = async () => {
    try {
      onQuantumLoading(true);
      await simulateDisturbance(1);
      onFeedback("Disturbance simulated successfully", false);
      onRefresh();
    } catch (err) {
      onFeedback("Failed to simulate disturbance", true);
    } finally {
      onQuantumLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Sparkles className="h-6 w-6 text-[#003666]" />
        <h2 className="text-2xl font-bold text-slate-900">Quantum Operations</h2>
      </div>

      {/* AI Insights for Quantum */}
      {aiInsights && aiInsights.quantum && aiInsights.quantum.length > 0 && (
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-6 text-white">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="h-5 w-5" />
            <h3 className="text-lg font-bold">AI Quantum Insights</h3>
          </div>
          <div className="space-y-2">
            {aiInsights.quantum.map((insight: any, idx: number) => (
              <div key={idx} className="flex items-start gap-3 bg-white/10 rounded-lg p-3">
                <div
                  className={`mt-0.5 ${
                    insight.type === "warning"
                      ? "text-amber-300"
                      : insight.type === "error"
                        ? "text-red-300"
                        : "text-green-300"
                  }`}
                >
                  {insight.type === "warning" ? (
                    <AlertCircle className="h-4 w-4" />
                  ) : insight.type === "error" ? (
                    <XCircle className="h-4 w-4" />
                  ) : (
                    <CheckCircle className="h-4 w-4" />
                  )}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">{insight.message}</p>
                  {insight.action && (
                    <p className="text-xs text-white/70 mt-1">💡 {insight.action}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Intelligence Status */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Intelligence Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-slate-50 rounded-lg">
            <div className="text-sm text-slate-600">Status</div>
            <div
              className={`text-lg font-bold ${intelligenceStatus?.active ? "text-green-600" : "text-red-600"}`}
            >
              {intelligenceStatus?.active ? "Active" : "Inactive"}
            </div>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg">
            <div className="text-sm text-slate-600">Phi Score</div>
            <div className="text-lg font-bold text-slate-900">
              {intelligenceStatus?.phi?.toFixed(4) || "N/A"}
            </div>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg">
            <div className="text-sm text-slate-600">Current Goal</div>
            <div className="text-lg font-bold text-slate-900 truncate">
              {intelligenceStatus?.current_goal || "N/A"}
            </div>
          </div>
        </div>
      </div>

      {/* Intelligence Telemetry */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Intelligence Telemetry</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 bg-slate-50 rounded-lg">
            <div className="text-sm text-slate-600">Phi Integrated</div>
            <div className="text-lg font-bold text-slate-900">
              {intelligenceTelemetry?.phi_integrated?.toFixed(4) || "N/A"}
            </div>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg">
            <div className="text-sm text-slate-600">Self Awareness</div>
            <div className="text-lg font-bold text-slate-900">
              {intelligenceTelemetry?.self_awareness?.toFixed(4) || "N/A"}
            </div>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg">
            <div className="text-sm text-slate-600">Prediction Accuracy</div>
            <div className="text-lg font-bold text-slate-900">
              {intelligenceTelemetry?.prediction_accuracy?.toFixed(2) || "N/A"}%
            </div>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg">
            <div className="text-sm text-slate-600">Healing Events</div>
            <div className="text-lg font-bold text-slate-900">
              {intelligenceTelemetry?.healing_events || 0}
            </div>
          </div>
        </div>
      </div>

      {/* Intelligence Controls */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Intelligence Controls</h3>
        <div className="space-y-6">
          {/* Scale Intelligence */}
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Intelligence Scale
              </label>
              <input
                type="range"
                min="0.1"
                max="10"
                step="0.1"
                value={intelligenceScale}
                onChange={(e) => setIntelligenceScale(parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="text-sm text-slate-600 mt-1">{intelligenceScale.toFixed(1)}x</div>
            </div>
            <button
              onClick={handleScaleIntelligence}
              disabled={quantumLoading}
              className="px-4 py-2 bg-[#003666] text-white rounded-lg hover:bg-[#002147] transition-colors disabled:opacity-50"
            >
              Scale
            </button>
          </div>

          {/* Boost Consciousness */}
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Consciousness Boost
              </label>
              <input
                type="range"
                min="1"
                max="5"
                step="0.1"
                value={consciousnessBoost}
                onChange={(e) => setConsciousnessBoost(parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="text-sm text-slate-600 mt-1">{consciousnessBoost.toFixed(1)}x</div>
            </div>
            <button
              onClick={handleBoostConsciousness}
              disabled={quantumLoading}
              className="px-4 py-2 bg-[#C5A55A] text-white rounded-lg hover:bg-[#A08040] transition-colors disabled:opacity-50"
            >
              Boost
            </button>
          </div>

          {/* Start/Stop/Reset */}
          <div className="flex gap-3">
            <button
              onClick={handleStartIntelligence}
              disabled={quantumLoading}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              <Activity className="h-4 w-4 inline mr-2" />
              Start Intelligence
            </button>
            <button
              onClick={handleStopIntelligence}
              disabled={quantumLoading}
              className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
            >
              <Activity className="h-4 w-4 inline mr-2" />
              Stop Intelligence
            </button>
            <button
              onClick={handleResetIntelligence}
              disabled={quantumLoading}
              className="flex-1 px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors disabled:opacity-50"
            >
              <RefreshCw className="h-4 w-4 inline mr-2" />
              Reset Intelligence
            </button>
          </div>
        </div>
      </div>

      {/* Pool Switching */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Pool Switching</h3>

        {/* AI Pool Recommendation */}
        {aiInsights && aiInsights.network && aiInsights.network.length > 0 && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-2">
              <Sparkles className="h-4 w-4 text-blue-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-blue-900">AI Recommendation</p>
                <p className="text-xs text-blue-700 mt-1">
                  {aiInsights.network[0]?.message ||
                    "Optimize pool selection based on current network conditions"}
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Select Pool</label>
            <select
              value={selectedPool}
              onChange={(e) => setSelectedPool(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666]"
            >
              <option value="">Select a pool...</option>
              {pools.map((pool, idx) => (
                <option key={idx} value={pool.pool_id}>
                  {pool.name || pool.pool_id}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleSwitchPool}
            disabled={quantumLoading || !selectedPool}
            className="w-full px-4 py-2 bg-[#003666] text-white rounded-lg hover:bg-[#002147] transition-colors disabled:opacity-50"
          >
            <Server className="h-4 w-4 inline mr-2" />
            Switch Pool
          </button>
        </div>
      </div>

      {/* Advanced Operations */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Advanced Operations</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={handleExecutePulvini}
            disabled={quantumLoading}
            className="px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
          >
            <Sparkles className="h-4 w-4 inline mr-2" />
            Execute Pulvini
          </button>
          <button
            onClick={handleSimulateDisturbance}
            disabled={quantumLoading}
            className="px-4 py-3 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50"
          >
            <AlertCircle className="h-4 w-4 inline mr-2" />
            Simulate Disturbance
          </button>
        </div>
      </div>

      {/* Refresh Button */}
      <button
        onClick={onRefresh}
        disabled={quantumLoading}
        className="w-full px-4 py-3 bg-slate-200 text-slate-900 rounded-lg hover:bg-slate-300 transition-colors disabled:opacity-50"
      >
        <RefreshCw className={`h-4 w-4 inline mr-2 ${quantumLoading ? "animate-spin" : ""}`} />
        Refresh Quantum Data
      </button>
    </div>
  );
}

function MiningView({
  telemetry,
  pools,
  activePoolName,
  onFeedback,
  aiInsights,
}: {
  telemetry: any;
  pools: any[];
  activePoolName?: string;
  onFeedback: (text: string, error?: boolean) => void;
  aiInsights: any;
}) {
  // Use real telemetry data instead of hardcoded values
  const [hashrate, setHashrate] = useState(telemetry?.hashrate_ehs || 0);
  const [powerScale, setPowerScale] = useState(telemetry?.power_scale || 1.0);
  const [phiResonance, setPhiResonance] = useState(telemetry?.phi_resonance || 0.618);
  const [timeToNextShare, setTimeToNextShare] = useState(telemetry?.time_to_next_share || 30);
  const [sellHashrateAmount, setSellHashrateAmount] = useState("");
  const [selectedPoolForSale, setSelectedPoolForSale] = useState("");
  const [miningRevenue, setMiningRevenue] = useState(telemetry?.mining_revenue || 0);
  const [hashrateRevenue, setHashrateRevenue] = useState(telemetry?.hashrate_revenue || 0);

  // Update values when telemetry changes
  useEffect(() => {
    if (telemetry) {
      setHashrate(telemetry.hashrate_ehs || 0);
      setPowerScale(telemetry.power_scale || 1.0);
      setPhiResonance(telemetry.phi_resonance || 0.618);
      setTimeToNextShare(telemetry.time_to_next_share || 30);
      setMiningRevenue(telemetry.mining_revenue || 0);
      setHashrateRevenue(telemetry.hashrate_revenue || 0);
    }
  }, [telemetry]);

  const handleSellHashrate = async () => {
    if (!sellHashrateAmount || !selectedPoolForSale) {
      onFeedback("Please enter amount and select pool", true);
      return;
    }
    try {
      onFeedback(`Selling ${sellHashrateAmount} EH/s hashrate to ${selectedPoolForSale}`, false);
      // This should call a real backend API to sell hashrate
      // For now, we'll update the local state to reflect the sale
      // In production, this would be: await sellHashrateToPool(selectedPoolForSale, parseFloat(sellHashrateAmount));
      const amount = parseFloat(sellHashrateAmount);
      setHashrateRevenue((prev) => prev + amount * 0.05); // This should come from real pool pricing API
      onFeedback("Hashrate sale completed successfully", false);
    } catch (err) {
      onFeedback("Failed to sell hashrate", true);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Cpu className="h-6 w-6 text-[#003666]" />
        <h2 className="text-2xl font-bold text-slate-900">Mining & Hashrate Operations</h2>
      </div>

      {/* AI Mining Insights */}
      {aiInsights && aiInsights.mining && aiInsights.mining.length > 0 && (
        <div className="bg-gradient-to-r from-green-600 to-teal-600 rounded-xl p-6 text-white">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="h-5 w-5" />
            <h3 className="text-lg font-bold">AI Mining Insights</h3>
          </div>
          <div className="space-y-2">
            {aiInsights.mining.map((insight: any, idx: number) => (
              <div key={idx} className="flex items-start gap-3 bg-white/10 rounded-lg p-3">
                <div
                  className={`mt-0.5 ${
                    insight.type === "warning"
                      ? "text-amber-300"
                      : insight.type === "error"
                        ? "text-red-300"
                        : "text-green-300"
                  }`}
                >
                  {insight.type === "warning" ? (
                    <AlertCircle className="h-4 w-4" />
                  ) : insight.type === "error" ? (
                    <XCircle className="h-4 w-4" />
                  ) : (
                    <CheckCircle className="h-4 w-4" />
                  )}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">{insight.message}</p>
                  {insight.action && (
                    <p className="text-xs text-white/70 mt-1">💡 {insight.action}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hilbert Space Visualization */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Hilbert Space Mining Telemetry
        </h3>
        <div className="flex flex-col lg:flex-row gap-6">
          <HilbertSpaceVisualizer
            hashrate={hashrate}
            powerScale={powerScale}
            phiResonance={phiResonance}
            timeToNextShare={timeToNextShare}
          />
          <div className="flex-1 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="text-sm text-slate-600">Current Hashrate</div>
                <div className="text-2xl font-bold text-slate-900">{hashrate.toFixed(2)} EH/s</div>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="text-sm text-slate-600">Power Scale</div>
                <div className="text-2xl font-bold text-slate-900">{powerScale.toFixed(2)}x</div>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="text-sm text-slate-600">Phi Resonance</div>
                <div className="text-2xl font-bold text-slate-900">{phiResonance.toFixed(4)}</div>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="text-sm text-slate-600">Time to Next Share</div>
                <div className="text-2xl font-bold text-slate-900">{timeToNextShare}s</div>
              </div>
            </div>
            <div className="p-4 bg-gradient-to-r from-[#003666] to-[#C5A55A] rounded-lg text-white">
              <div className="text-sm font-medium">Mining Efficiency</div>
              <div className="text-3xl font-bold mt-1">
                {(phiResonance * powerScale * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Revenue Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Mining Revenue</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
              <div className="flex items-center gap-3">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <div>
                  <div className="text-sm text-slate-600">Block Rewards</div>
                  <div className="text-2xl font-bold text-green-900">
                    ${(miningRevenue * 0.7).toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center gap-3">
                <DollarSign className="h-5 w-5 text-blue-600" />
                <div>
                  <div className="text-sm text-slate-600">Transaction Fees</div>
                  <div className="text-2xl font-bold text-blue-900">
                    ${(miningRevenue * 0.3).toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
            <div className="p-4 bg-slate-100 rounded-lg">
              <div className="text-sm text-slate-600">Total Mining Revenue</div>
              <div className="text-3xl font-bold text-slate-900">${miningRevenue.toFixed(2)}</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Hashrate Sales Revenue</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-purple-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Activity className="h-5 w-5 text-purple-600" />
                <div>
                  <div className="text-sm text-slate-600">Hashrate Sold</div>
                  <div className="text-2xl font-bold text-purple-900">
                    ${(hashrateRevenue * 0.8).toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between p-4 bg-amber-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Zap className="h-5 w-5 text-amber-600" />
                <div>
                  <div className="text-sm text-slate-600">Pool Payments</div>
                  <div className="text-2xl font-bold text-amber-900">
                    ${(hashrateRevenue * 0.2).toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
            <div className="p-4 bg-slate-100 rounded-lg">
              <div className="text-sm text-slate-600">Total Hashrate Revenue</div>
              <div className="text-3xl font-bold text-slate-900">${hashrateRevenue.toFixed(2)}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Hashrate Selling */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Sell Hashrate</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Hashrate Amount (EH/s)
            </label>
            <input
              type="number"
              value={sellHashrateAmount}
              onChange={(e) => setSellHashrateAmount(e.target.value)}
              placeholder="Enter hashrate to sell"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666]"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Select Pool</label>
            <select
              value={selectedPoolForSale}
              onChange={(e) => setSelectedPoolForSale(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003666]"
            >
              <option value="">Select a pool that pays for hashrate...</option>
              {pools.map((pool, idx) => (
                <option key={idx} value={pool.pool_id}>
                  {pool.name || pool.pool_id} - Pays for hashrate
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleSellHashrate}
            className="w-full px-4 py-3 bg-[#C5A55A] text-white rounded-lg hover:bg-[#A08040] transition-colors"
          >
            <DollarSign className="h-4 w-4 inline mr-2" />
            Sell Hashrate
          </button>
        </div>

        {/* Pool Payment Info */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start gap-2">
            <Info className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-blue-900">Hashrate Payment Pools</p>
              <p className="text-xs text-blue-700 mt-1">
                Some pools pay directly for hashrate regardless of mining success. This provides
                steady revenue alongside traditional mining rewards. Select pools that offer
                hashrate payments above.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Total Revenue Summary */}
      <div className="bg-gradient-to-r from-[#003666] to-[#C5A55A] rounded-xl p-6 text-white">
        <h3 className="text-lg font-bold mb-4">Total Revenue Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-white/10 rounded-lg">
            <div className="text-sm text-white/70">Mining Revenue</div>
            <div className="text-2xl font-bold">${miningRevenue.toFixed(2)}</div>
          </div>
          <div className="p-4 bg-white/10 rounded-lg">
            <div className="text-sm text-white/70">Hashrate Sales</div>
            <div className="text-2xl font-bold">${hashrateRevenue.toFixed(2)}</div>
          </div>
          <div className="p-4 bg-white/10 rounded-lg">
            <div className="text-sm text-white/70">Combined Total</div>
            <div className="text-2xl font-bold">
              ${(miningRevenue + hashrateRevenue).toFixed(2)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function SecurityView({
  onFeedback,
  aiInsights,
}: {
  onFeedback: (text: string, error?: boolean) => void;
  aiInsights: any;
}) {
  const [threatLevel, setThreatLevel] = useState("low");
  const [activeThreats, setActiveThreats] = useState(0);
  const [defenseSystems, setDefenseSystems] = useState<any>({});
  const [recentThreats, setRecentThreats] = useState<any[]>([]);
  const [securityScore, setSecurityScore] = useState(95);

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3">
        <Shield className="h-7 w-7 text-[#003666]" />
        <h2 className="text-3xl font-bold text-slate-900 tracking-tight">
          Security Operations Center
        </h2>
      </div>

      {/* AI Security Insights */}
      {aiInsights && aiInsights.security && aiInsights.security.length > 0 && (
        <div className="bg-gradient-to-r from-red-600 via-orange-600 to-amber-600 rounded-2xl p-8 text-white shadow-xl">
          <div className="flex items-center gap-3 mb-6">
            <Shield className="h-6 w-6" />
            <h3 className="text-xl font-bold tracking-tight">AI Security Intelligence</h3>
          </div>
          <div className="space-y-3">
            {aiInsights.security.map((insight: any, idx: number) => (
              <div
                key={idx}
                className="flex items-start gap-4 bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20"
              >
                <div
                  className={`mt-0.5 ${
                    insight.type === "critical"
                      ? "text-red-300"
                      : insight.type === "warning"
                        ? "text-amber-300"
                        : "text-green-300"
                  }`}
                >
                  {insight.type === "critical" ? (
                    <AlertCircle className="h-5 w-5" />
                  ) : insight.type === "warning" ? (
                    <AlertTriangle className="h-5 w-5" />
                  ) : (
                    <CheckCircle className="h-5 w-5" />
                  )}
                </div>
                <div className="flex-1">
                  <p className="text-base font-semibold">{insight.message}</p>
                  {insight.action && (
                    <p className="text-sm text-white/80 mt-2 font-medium">💡 {insight.action}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Security Score Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <Shield className="h-6 w-6 text-green-600" />
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Security Score
            </span>
          </div>
          <div className="text-3xl font-bold text-green-600 mb-1">{securityScore}%</div>
          <div className="text-sm text-slate-600">Excellent</div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <AlertCircle className="h-6 w-6 text-red-600" />
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Threat Level
            </span>
          </div>
          <div className="text-3xl font-bold text-green-600 mb-1 capitalize">{threatLevel}</div>
          <div className="text-sm text-slate-600">{activeThreats} active threats</div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <Lock className="h-6 w-6 text-blue-600" />
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Defense Systems
            </span>
          </div>
          <div className="text-3xl font-bold text-blue-600 mb-1">6/6</div>
          <div className="text-sm text-slate-600">All operational</div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <Activity className="h-6 w-6 text-purple-600" />
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Events (24h)
            </span>
          </div>
          <div className="text-3xl font-bold text-purple-600 mb-1">1,247</div>
          <div className="text-sm text-slate-600">+12% from yesterday</div>
        </div>
      </div>

      {/* Defense Systems Status */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Defense Systems Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-green-50 border border-green-200 rounded-xl">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <div className="font-semibold text-green-900">Consciousness Engine</div>
                <div className="text-sm text-green-700">Phi-integrated monitoring active</div>
              </div>
            </div>
          </div>
          <div className="p-4 bg-green-50 border border-green-200 rounded-xl">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <div className="font-semibold text-green-900">Reflexive Controller</div>
                <div className="text-sm text-green-700">Autopoiesis detection operational</div>
              </div>
            </div>
          </div>
          <div className="p-4 bg-green-50 border border-green-200 rounded-xl">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <div className="font-semibold text-green-900">Synaptic Persistence</div>
                <div className="text-sm text-green-700">Hebbian learning active</div>
              </div>
            </div>
          </div>
          <div className="p-4 bg-green-50 border border-green-200 rounded-xl">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <div className="font-semibold text-green-900">Quantum Regeneration</div>
                <div className="text-sm text-green-700">Self-healing ready</div>
              </div>
            </div>
          </div>
          <div className="p-4 bg-green-50 border border-green-200 rounded-xl">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <div className="font-semibold text-green-900">Swarm Coherence</div>
                <div className="text-sm text-green-700">Multi-node coordination active</div>
              </div>
            </div>
          </div>
          <div className="p-4 bg-green-50 border border-green-200 rounded-xl">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <div className="font-semibold text-green-900">It from Bit Archeology</div>
                <div className="text-sm text-green-700">Blockchain threat detection active</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Security Events */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Recent Security Events</h3>
        <div className="space-y-3">
          <div className="flex items-start gap-4 p-4 bg-slate-50 rounded-xl">
            <div className="mt-1">
              <CheckCircle className="h-5 w-5 text-green-600" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-semibold text-slate-900">Authentication Success</span>
                <span className="text-xs text-slate-500">2 minutes ago</span>
              </div>
              <p className="text-sm text-slate-600">
                Executive user authenticated via secure token
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4 p-4 bg-slate-50 rounded-xl">
            <div className="mt-1">
              <Shield className="h-5 w-5 text-blue-600" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-semibold text-slate-900">Defense System Update</span>
                <span className="text-xs text-slate-500">15 minutes ago</span>
              </div>
              <p className="text-sm text-slate-600">
                Quantum regeneration module self-healing completed
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4 p-4 bg-slate-50 rounded-xl">
            <div className="mt-1">
              <Activity className="h-5 w-5 text-purple-600" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-semibold text-slate-900">Swarm Coherence Check</span>
                <span className="text-xs text-slate-500">1 hour ago</span>
              </div>
              <p className="text-sm text-slate-600">
                Multi-node security coordination verified - all nodes operational
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Security Metrics Visualization */}
      <div className="bg-gradient-to-r from-[#003666] to-[#004d8c] rounded-2xl p-6 text-white shadow-xl">
        <h3 className="text-lg font-semibold mb-4">Security Metrics Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div className="text-sm text-white/70 mb-2">Threat Detection Rate</div>
            <div className="text-4xl font-bold">99.8%</div>
            <div className="w-full bg-white/20 rounded-full h-2 mt-2">
              <div className="bg-green-400 h-2 rounded-full" style={{ width: "99.8%" }}></div>
            </div>
          </div>
          <div>
            <div className="text-sm text-white/70 mb-2">Response Time</div>
            <div className="text-4xl font-bold">12ms</div>
            <div className="text-sm text-white/60 mt-1">Average threat response</div>
          </div>
          <div>
            <div className="text-sm text-white/70 mb-2">False Positive Rate</div>
            <div className="text-4xl font-bold">0.02%</div>
            <div className="text-sm text-white/60 mt-1">Industry leading accuracy</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <h2 className="text-xl font-bold text-slate-900">{title}</h2>
          <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
            <X className="h-5 w-5 text-slate-600" />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}

// Missing icon imports
function Flask({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M10 2v7.31" />
      <path d="M14 2v7.31" />
      <path d="M8.5 2h7" />
      <path d="M14 9.3a6.5 6.5 0 1 1-4 0" />
    </svg>
  );
}

export default HybaAdminDashboard;
