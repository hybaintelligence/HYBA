import React, { useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  FileText,
  KeyRound,
  Layers3,
  Play,
  ShieldCheck,
  Upload,
} from "lucide-react";
import { intelligenceExplain, intelligenceOrchestrate } from "../apiClient";
import {
  executeCustomerCIAASWorkloadForStudio,
  getStoredCustomerApiKey,
  listCustomerCIAASServicesForStudio,
  setStoredCustomerApiKey,
} from "../workloadStudioApi";
import { useSkillMode } from "../skillMode";

type WorkloadType =
  | "risk register"
  | "board decision memo"
  | "operational incident log"
  | "compliance/audit checklist";

type CognitiveLens =
  | "executive"
  | "business"
  | "operator"
  | "analyst"
  | "engineer"
  | "auditor"
  | "expert";

type TraceIdProvenance = "server_issued" | "client_generated";
type EndpointInvoked = "ciass_live" | "intelligence_explain" | "intelligence_orchestrate" | "none";

type InvocationMetadata = {
  endpoint_invoked: EndpointInvoked;
  endpoint_path: string;
  fallback: boolean;
  fallback_reason: string | null;
  trace_id: string;
  trace_id_provenance: TraceIdProvenance;
};

type EvidencePacket = {
  schema_version: "1.0";
  generated_at: string;
  workload: {
    id: string;
    type: WorkloadType;
    classification: WorkloadType;
    preview: string;
  };
  cognitive_lens: CognitiveLens;
  invocation: InvocationMetadata;
  response: Record<string, unknown>;
  evidence_packet: {
    invariants: string[];
    limitations: string[];
    claim_boundary: string;
    transformations: string[];
    evidence_seal: string;
  };
  claim_boundary: string;
  audit: {
    exported_by: "WorkloadStudio v1.0";
    export_triggered_at: string | null;
  };
};

type StudioResult = {
  traceId: string;
  workloadType: WorkloadType;
  lens: CognitiveLens;
  endpointInvoked: string;
  before: string;
  after: string;
  evidencePacket: EvidencePacket;
  boundary: string;
};

const sampleWorkloads: Record<WorkloadType, string> = {
  "risk register": `risk_id,title,impact,likelihood,owner,control\nR-17,Supplier concentration in payment processor,High,Medium,COO,Quarterly vendor review\nR-22,Unclear approval boundary for exception handling,Medium,High,Legal,Manual approval log`,
  "board decision memo": `Decision: approve a two-region customer data deployment.\nAssumptions: enterprise demand requires lower latency; legal review is complete; rollback can happen in one week.\nOpen question: whether the second region changes audit scope.`,
  "operational incident log": `2026-06-22T10:13Z API latency above threshold for cohort A\n2026-06-22T10:19Z retry pressure increased after queue saturation\n2026-06-22T10:27Z operator paused rollout and preserved approvals`,
  "compliance/audit checklist": `Control,Status,Evidence\nAccess review,Partial,Q2 export missing contractor attestations\nData retention,Pass,Policy HYBA-DR-9 attached\nException approval,Gap,No trace ID on two exceptions`,
};

const lenses: CognitiveLens[] = [
  "executive",
  "business",
  "operator",
  "analyst",
  "engineer",
  "auditor",
  "expert",
];

const CLAIM_BOUNDARY =
  "Capability boundary: HYBA reports the API response, transformation pathway, and evidence packet. The buyer can reproduce the call and inspect the trace rather than accept a narrative claim.";

// TODO(post-MVP): decompose this v1 demo surface into WorkloadSelector,
// LensSelector, InvocationEngine, EvidencePacketBuilder, and PacketExporter.
// Kept together for now so the CIaaS buyer journey can be reviewed as one flow.

function classifyWorkload(input: string): WorkloadType {
  const text = input.toLowerCase();
  if (text.includes("control") || text.includes("audit") || text.includes("compliance")) {
    return "compliance/audit checklist";
  }
  if (text.includes("incident") || text.includes("latency") || text.includes("failure")) {
    return "operational incident log";
  }
  if (text.includes("decision") || text.includes("assumption") || text.includes("approve")) {
    return "board decision memo";
  }
  return "risk register";
}

function buildFallbackTransformation(
  type: WorkloadType,
  lens: CognitiveLens,
  input: string,
): string {
  const lines = input.split(/\n+/).filter(Boolean).slice(0, 4);
  const focus: Record<CognitiveLens, string> = {
    executive: "decision posture, strategic risk concentration, and approval path",
    business: "commercial exposure, operating impact, cost/risk trade-off, and accountable owner",
    operator: "next action, escalation boundary, and runbook fit",
    analyst: "drivers, gaps, measurable deltas, and comparison structure",
    engineer: "interfaces, invariants, failure modes, and traceability",
    auditor: "controls, evidence sufficiency, limitations, and reproducibility",
    expert: "causal structure, counterfactuals, and boundary conditions",
  };
  return [
    `Classified as ${type}.`,
    `Lens applied: ${lens}; focus is ${focus[lens]}.`,
    `Extracted workload atoms: ${lines.join(" | ") || "none supplied"}.`,
    "Transformation: convert the supplied artifact into a reproducible intelligence packet with assumptions, gaps, mitigations, confidence limits, and an evidence trail.",
    "Human approval remains required for consequential action.",
  ].join("\n");
}

function makeTraceId() {
  return `hyba-trace-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function readTraceId(value: unknown): string | null {
  if (!value || typeof value !== "object") return null;
  const record = value as Record<string, unknown>;
  const direct = record.trace_id || record.traceId;
  if (typeof direct === "string" && direct.trim()) return direct.trim();
  const evidence = record.evidence_packet;
  if (evidence && typeof evidence === "object") {
    const nested = (evidence as Record<string, unknown>).trace_id;
    if (typeof nested === "string" && nested.trim()) return nested.trim();
  }
  return null;
}

function buildEvidencePacket(args: {
  traceId: string;
  traceIdProvenance: TraceIdProvenance;
  workload: string;
  workloadType: WorkloadType;
  lens: CognitiveLens;
  invocation: InvocationMetadata;
  response: Record<string, unknown>;
  liveCIAAS: boolean;
  serviceId: string | null;
}): EvidencePacket {
  return {
    schema_version: "1.0",
    generated_at: new Date().toISOString(),
    workload: {
      id: args.traceId,
      type: args.workloadType,
      classification: args.workloadType,
      preview: args.workload.slice(0, 500),
    },
    cognitive_lens: args.lens,
    invocation: {
      ...args.invocation,
      trace_id: args.traceId,
      trace_id_provenance: args.traceIdProvenance,
    },
    response: {
      live_ciaas_execution: args.liveCIAAS,
      ciaas_service_id: args.serviceId,
      ...args.response,
    },
    evidence_packet: {
      invariants: [
        "customer input preserved",
        "human approval boundary preserved",
        "capability boundary visible",
        "raw API-key material not exported",
      ],
      limitations: [
        "Packet reflects supplied input and available API response",
        "Consequential action requires human review",
        args.invocation.fallback
          ? args.invocation.fallback_reason || "Fallback path used"
          : "Live CIaaS route completed for this packet",
      ],
      claim_boundary: CLAIM_BOUNDARY,
      transformations: [
        "customer workload ingestion",
        "classification",
        "lens-conditioned invocation context",
        "CIaaS execution path selection",
        "evidence packaging",
      ],
      evidence_seal: `${args.invocation.fallback ? "fallback" : "seal"}-${args.traceId.slice(-8)}`,
    },
    claim_boundary: CLAIM_BOUNDARY,
    audit: {
      exported_by: "WorkloadStudio v1.0",
      export_triggered_at: null,
    },
  };
}

export function WorkloadStudio() {
  const { mode } = useSkillMode();
  const [selectedType, setSelectedType] = useState<WorkloadType>("risk register");
  const [lens, setLens] = useState<CognitiveLens>(
    lenses.includes(mode as CognitiveLens) ? (mode as CognitiveLens) : "executive",
  );
  const [workload, setWorkload] = useState(sampleWorkloads["risk register"]);
  const [apiKey, setApiKey] = useState(() => getStoredCustomerApiKey());
  const [apiKeySaved, setApiKeySaved] = useState(Boolean(getStoredCustomerApiKey()));
  const [result, setResult] = useState<StudioResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const classifiedType = useMemo(() => classifyWorkload(workload), [workload]);

  const loadSample = (type: WorkloadType) => {
    setSelectedType(type);
    setWorkload(sampleWorkloads[type]);
    setResult(null);
    setError(null);
  };

  const persistApiKey = () => {
    setStoredCustomerApiKey(apiKey);
    setApiKeySaved(Boolean(apiKey.trim()));
  };

  const runTransformation = async () => {
    const clientTraceId = makeTraceId();
    const customerApiKey = apiKey.trim();
    if (customerApiKey) setStoredCustomerApiKey(customerApiKey);
    setRunning(true);
    setError(null);
    try {
      const classification = classifyWorkload(workload);
      let invocation: InvocationMetadata = customerApiKey
        ? {
            endpoint_invoked: "none",
            endpoint_path: "/api/v1/computational-intelligence-services",
            fallback: true,
            fallback_reason: "No customer CIaaS service selected yet",
            trace_id: clientTraceId,
            trace_id_provenance: "client_generated",
          }
        : {
            endpoint_invoked: "none",
            endpoint_path: "/api/v1/computational-intelligence-services/{service_id}/execute",
            fallback: true,
            fallback_reason: "Customer API key not supplied at invocation time",
            trace_id: clientTraceId,
            trace_id_provenance: "client_generated",
          };
      let ciaasResult: Record<string, unknown> | null = null;
      let selectedServiceId: string | null = null;

      if (customerApiKey) {
        try {
          const services = await listCustomerCIAASServicesForStudio(customerApiKey);
          const service = services.find((item) => item.state === "running") || services[0];
          if (service?.service_id) {
            selectedServiceId = service.service_id;
            ciaasResult = await executeCustomerCIAASWorkloadForStudio(
              service.service_id,
              {
                workload_type: "explain",
                context: {
                  trace_id: clientTraceId,
                  workload,
                  cognitive_lens: lens,
                  lens,
                  classification,
                  customer_mode: true,
                  studio: "workload_transformation",
                },
                idempotency_key: clientTraceId,
              },
              customerApiKey,
            );
            const serverTrace = readTraceId(ciaasResult);
            invocation = {
              endpoint_invoked: "ciass_live",
              endpoint_path: `/api/v1/computational-intelligence-services/${service.service_id}/execute`,
              fallback: false,
              fallback_reason: null,
              trace_id: serverTrace || clientTraceId,
              trace_id_provenance: serverTrace ? "server_issued" : "client_generated",
            };
          } else {
            invocation = {
              endpoint_invoked: "none",
              endpoint_path: "/api/v1/computational-intelligence-services",
              fallback: true,
              fallback_reason: "No provisioned customer CIaaS rail returned at invocation time",
              trace_id: clientTraceId,
              trace_id_provenance: "client_generated",
            };
          }
        } catch (customerError) {
          invocation = {
            endpoint_invoked: "none",
            endpoint_path: "/api/v1/computational-intelligence-services/{service_id}/execute",
            fallback: true,
            fallback_reason:
              customerError instanceof Error
                ? customerError.message
                : "Customer CIaaS route unavailable",
            trace_id: clientTraceId,
            trace_id_provenance: "client_generated",
          };
          setError(invocation.fallback_reason);
        }
      }

      const explain = await intelligenceExplain({
        query: `Classify and transform this customer-provided ${classification} for CIaaS Workload Studio using the ${lens} cognitive lens. Return assumptions, gaps, confidence limits, evidence needs, decision boundary, and customer-safe next action.`,
        context: {
          trace_id: invocation.trace_id,
          workload,
          cognitive_lens: lens,
          lens,
          customer_mode: true,
          skill_mode: mode,
          ciaas_service_id: selectedServiceId,
          live_ciaas_execution: Boolean(ciaasResult),
        },
      });
      const explainTrace = readTraceId(explain);
      if (invocation.fallback && explainTrace) {
        invocation = {
          endpoint_invoked: "intelligence_explain",
          endpoint_path: "/api/v1/intelligence/explain",
          fallback: true,
          fallback_reason: invocation.fallback_reason,
          trace_id: explainTrace,
          trace_id_provenance: "server_issued",
        };
      }

      let planSummary = "No orchestration plan returned.";
      let orchestrateSucceeded = false;
      try {
        const plan = await intelligenceOrchestrate({
          goal: `Produce a reproducible evidence packet for a ${classification}`,
          priority: lens === "auditor" ? 9 : lens === "business" ? 8 : 7,
          constraints: {
            trace_id: invocation.trace_id,
            cognitive_lens: lens,
            preserve_human_approval: true,
          },
        });
        orchestrateSucceeded = true;
        planSummary = plan.steps
          .map((step, index) => `${index + 1}. ${step.action} → ${step.expected_outcome}`)
          .join("\n");
      } catch {
        planSummary = "Orchestration endpoint unavailable; explanation endpoint completed.";
      }

      const endpointInvoked = invocation.fallback
        ? orchestrateSucceeded
          ? `${invocation.endpoint_path} + /api/v1/intelligence/orchestrate`
          : invocation.endpoint_path
        : `${invocation.endpoint_path} + /api/v1/intelligence/explain + /api/v1/intelligence/orchestrate`;
      const after = `${explain.explanation}\n\nCIaaS plan:\n${planSummary}`;
      const traceId = invocation.trace_id;
      const evidencePacket = buildEvidencePacket({
        traceId,
        traceIdProvenance: invocation.trace_id_provenance,
        workload,
        workloadType: classification,
        lens,
        invocation,
        response: {
          explanation: explain.explanation,
          confidence: explain.confidence,
          sources: explain.sources,
          orchestration_plan: planSummary,
        },
        liveCIAAS: Boolean(ciaasResult),
        serviceId: selectedServiceId,
      });
      setResult({
        traceId,
        workloadType: classification,
        lens,
        endpointInvoked,
        before: workload,
        after,
        evidencePacket,
        boundary: CLAIM_BOUNDARY,
      });
    } catch (err) {
      const classification = classifyWorkload(workload);
      const traceId = clientTraceId;
      const fallbackReason = err instanceof Error ? err.message : "All endpoints unavailable";
      const invocation: InvocationMetadata = {
        endpoint_invoked: "none",
        endpoint_path: "none",
        fallback: true,
        fallback_reason: fallbackReason,
        trace_id: traceId,
        trace_id_provenance: "client_generated",
      };
      setError(fallbackReason);
      setResult({
        traceId,
        workloadType: classification,
        lens,
        endpointInvoked: "none",
        before: workload,
        after: buildFallbackTransformation(classification, lens, workload),
        evidencePacket: buildEvidencePacket({
          traceId,
          traceIdProvenance: "client_generated",
          workload,
          workloadType: classification,
          lens,
          invocation,
          response: { fallback_result: "local capability-boundary fallback packet" },
          liveCIAAS: false,
          serviceId: null,
        }),
        boundary:
          "Capability boundary: all API calls were unavailable, so this packet is marked as a client-generated fallback rather than a live CIaaS result.",
      });
    } finally {
      setRunning(false);
    }
  };

  const exportPacket = () => {
    if (!result) return;
    const packet: EvidencePacket = {
      ...result.evidencePacket,
      audit: { ...result.evidencePacket.audit, export_triggered_at: new Date().toISOString() },
    };
    const blob = new Blob([JSON.stringify(packet, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${result.traceId}-evidence-packet.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="space-y-6">
      <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-xl shadow-slate-900/5">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <span className="eyebrow">
              <Layers3 className="h-3.5 w-3.5" /> /workload-studio
            </span>
            <h2 className="mt-4 text-4xl font-black tracking-[-0.04em] text-slate-950 md:text-6xl">
              CIaaS Workload Studio
            </h2>
            <p className="mt-4 text-lg leading-8 text-slate-600">
              Do not believe HYBA. Bring your workload, run the API, inspect the transformation,
              read the evidence packet, and reproduce the result.
            </p>
          </div>
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-950">
            <ShieldCheck className="mb-2 h-5 w-5" /> The API speaks. Customer mode hides internal
            terms and marks the capability boundary.
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-lg shadow-slate-900/5">
          <h3 className="flex items-center gap-2 text-xl font-bold text-slate-950">
            <Upload className="h-5 w-5" /> Bring workload
          </h3>
          <div className="grid grid-cols-2 gap-2">
            {(Object.keys(sampleWorkloads) as WorkloadType[]).map((type) => (
              <button
                key={type}
                onClick={() => loadSample(type)}
                className={`rounded-xl border p-3 text-left text-sm font-semibold ${selectedType === type ? "border-blue-300 bg-blue-50 text-blue-950" : "border-slate-200 text-slate-700"}`}
              >
                {type}
              </button>
            ))}
          </div>
          <textarea
            value={workload}
            onChange={(event) => setWorkload(event.target.value)}
            className="min-h-72 w-full rounded-2xl border border-slate-200 p-4 font-mono text-sm outline-none focus:border-blue-400"
          />
          <div>
            <label className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
              Cognitive lens
            </label>
            <select
              value={lens}
              onChange={(event) => setLens(event.target.value as CognitiveLens)}
              className="mt-2 w-full rounded-xl border border-slate-200 p-3 font-semibold"
            >
              {lenses.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
              <KeyRound className="h-3.5 w-3.5" /> Customer API key for live CIaaS execution
            </label>
            <div className="mt-2 flex gap-2">
              <input
                value={apiKey}
                onChange={(event) => {
                  setApiKey(event.target.value);
                  setApiKeySaved(false);
                }}
                type="password"
                placeholder="hyba_..."
                className="flex-1 rounded-xl border border-slate-200 p-3 font-mono text-sm outline-none focus:border-blue-400"
              />
              <button
                onClick={persistApiKey}
                className="rounded-xl border border-slate-200 px-4 text-sm font-bold text-slate-700 hover:bg-slate-50"
              >
                {apiKeySaved ? "Saved" : "Save"}
              </button>
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Demo convenience only: the key is stored in this browser so the buyer can move from
              onboarding to workload transformation without DevTools. Production custody must move
              to HttpOnly cookies or server-side sessions.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
            HYBA classification: <strong>{classifiedType}</strong>
          </div>
          <button
            onClick={runTransformation}
            disabled={running || workload.trim().length === 0}
            className="executive-button w-full justify-center bg-[#06162D] text-white disabled:opacity-50"
          >
            <Play className="h-4 w-4" />{" "}
            {running ? "Running CIaaS transformation…" : "Run CIaaS transformation"}
          </button>
        </div>

        <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-lg shadow-slate-900/5">
          <h3 className="flex items-center gap-2 text-xl font-bold text-slate-950">
            <FileText className="h-5 w-5" /> Before / after intelligence packet
          </h3>
          {error && (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
              <AlertTriangle className="mr-2 inline h-4 w-4" />
              {error}
            </div>
          )}
          {!result ? (
            <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500">
              Run a workload to see the API transform it into a reproducible intelligence packet.
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 p-4">
                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
                    Before
                  </p>
                  <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap text-xs text-slate-700">
                    {result.before}
                  </pre>
                </div>
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-700">
                    After
                  </p>
                  <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap text-xs text-emerald-950">
                    {result.after}
                  </pre>
                </div>
              </div>
              <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-950">
                <CheckCircle2 className="mr-2 inline h-4 w-4" />
                Trace <strong>{result.traceId}</strong> · classified as{" "}
                <strong>{result.workloadType}</strong> · lens <strong>{result.lens}</strong>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
                  Endpoint path
                </p>
                <p className="mt-2 break-all font-mono text-xs text-slate-700">
                  {result.endpointInvoked}
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
                  Evidence packet
                </p>
                <pre className="mt-3 max-h-80 overflow-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-100">
                  {JSON.stringify(result.evidencePacket, null, 2)}
                </pre>
              </div>
              <div className="rounded-2xl border border-purple-200 bg-purple-50 p-4 text-sm text-purple-950">
                {result.boundary}
              </div>
              <button onClick={exportPacket} className="executive-button bg-slate-950 text-white">
                <Download className="h-4 w-4" /> Export evidence packet
              </button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
