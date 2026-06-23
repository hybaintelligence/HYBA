import React, { useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  FileText,
  Layers3,
  Play,
  ShieldCheck,
  Upload,
} from "lucide-react";
import {
  executeCustomerCIAASWorkload,
  intelligenceExplain,
  intelligenceOrchestrate,
  listCustomerCIAASServices,
} from "../apiClient";
import { useSkillMode } from "../skillMode";

type WorkloadType =
  | "risk register"
  | "board decision memo"
  | "operational incident log"
  | "compliance/audit checklist";

type CognitiveLens = "executive" | "operator" | "analyst" | "engineer" | "auditor" | "expert";

type StudioResult = {
  traceId: string;
  workloadType: WorkloadType;
  lens: CognitiveLens;
  endpointInvoked: string;
  before: string;
  after: string;
  evidencePacket: Record<string, unknown>;
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
  "operator",
  "analyst",
  "engineer",
  "auditor",
  "expert",
];

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
  const focus = {
    executive: "decision posture, risk concentration, and approval path",
    operator: "next action, escalation boundary, and runbook fit",
    analyst: "drivers, gaps, and measurable deltas",
    engineer: "interfaces, invariants, failure modes, and traceability",
    auditor: "controls, evidence sufficiency, limitations, and reproducibility",
    expert: "causal structure, counterfactuals, and boundary conditions",
  }[lens];
  return [
    `Classified as ${type}.`,
    `Lens applied: ${lens}; focus is ${focus}.`,
    `Extracted workload atoms: ${lines.join(" | ") || "none supplied"}.`,
    "Transformation: convert the supplied artifact into a reproducible intelligence packet with assumptions, gaps, mitigations, confidence limits, and an evidence trail.",
    "Human approval remains required for consequential action.",
  ].join("\n");
}

function makeTraceId() {
  return `hyba-trace-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export function WorkloadStudio() {
  const { mode } = useSkillMode();
  const [selectedType, setSelectedType] = useState<WorkloadType>("risk register");
  const [lens, setLens] = useState<CognitiveLens>("executive");
  const [workload, setWorkload] = useState(sampleWorkloads["risk register"]);
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

  const runTransformation = async () => {
    const traceId = makeTraceId();
    setRunning(true);
    setError(null);
    try {
      const classification = classifyWorkload(workload);
      let ciaasEndpoint = "/api/v1/intelligence/explain";
      try {
        const services = await listCustomerCIAASServices();
        const service = services.find((item) => item.state === "running") || services[0];
        if (service?.service_id) {
          await executeCustomerCIAASWorkload(service.service_id, {
            workload_type: "explain",
            context: { trace_id: traceId, workload, lens, classification, customer_mode: true },
            idempotency_key: traceId,
          });
          ciaasEndpoint = `/api/v1/computational-intelligence-services/${service.service_id}/workloads`;
        }
      } catch {
        ciaasEndpoint = "/api/v1/intelligence/explain (CIaaS service workload unavailable)";
      }

      const explain = await intelligenceExplain({
        query: `Classify and transform this customer-provided ${classification} for CIaaS Workload Studio using the ${lens} cognitive lens. Return assumptions, gaps, confidence limits, and evidence needs.`,
        context: { trace_id: traceId, workload, lens, customer_mode: true, skill_mode: mode },
      });
      let planSummary = "No orchestration plan returned.";
      try {
        const plan = await intelligenceOrchestrate({
          goal: `Produce a reproducible evidence packet for a ${classification}`,
          priority: lens === "auditor" ? 9 : 7,
          constraints: { trace_id: traceId, lens, preserve_human_approval: true },
        });
        planSummary = plan.steps
          .map((step, index) => `${index + 1}. ${step.action} → ${step.expected_outcome}`)
          .join("\n");
      } catch {
        planSummary = "Orchestration endpoint unavailable; explanation endpoint completed.";
      }

      const after = `${explain.explanation}\n\nCIaaS plan:\n${planSummary}`;
      setResult({
        traceId,
        workloadType: classification,
        lens,
        endpointInvoked: `${ciaasEndpoint} + /api/v1/intelligence/orchestrate`,
        before: workload,
        after,
        evidencePacket: {
          trace_id: traceId,
          workload_classification: classification,
          cognitive_lens: lens,
          confidence: explain.confidence,
          sources: explain.sources,
          transformations: ["classification", "lens translation", "evidence packaging"],
          invariants: [
            "customer input preserved",
            "human approval boundary preserved",
            "claim boundary visible",
          ],
          limitations: [
            "Packet reflects supplied input and available API response",
            "Consequential action requires human review",
          ],
          evidence_seal: `seal-${traceId.slice(-8)}`,
        },
        boundary:
          "Capability boundary: HYBA reports the endpoint response and evidence packet; it does not ask the buyer to accept an unsupported claim.",
      });
    } catch (err) {
      const classification = classifyWorkload(workload);
      setError(err instanceof Error ? err.message : "CIaaS endpoint unavailable");
      setResult({
        traceId,
        workloadType: classification,
        lens,
        endpointInvoked: "/api/v1/intelligence/explain (attempted)",
        before: workload,
        after: buildFallbackTransformation(classification, lens, workload),
        evidencePacket: {
          trace_id: traceId,
          workload_classification: classification,
          cognitive_lens: lens,
          endpoint_status: "unavailable",
          transformations: ["local classification", "claim-boundary fallback packet"],
          invariants: [
            "customer input preserved",
            "no fabricated API result",
            "human approval boundary preserved",
          ],
          limitations: ["Live CIaaS endpoint did not complete in this browser session"],
          evidence_seal: `attempt-${traceId.slice(-8)}`,
        },
        boundary:
          "Claim boundary: the API call was attempted but did not complete, so this packet is marked as an unavailable-endpoint fallback rather than a live CIaaS result.",
      });
    } finally {
      setRunning(false);
    }
  };

  const exportPacket = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
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
            terms and marks the claim/capability boundary.
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
          {result ? (
            <>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 p-4">
                  <p className="mb-2 text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
                    Original workload
                  </p>
                  <pre className="whitespace-pre-wrap text-xs text-slate-700">{result.before}</pre>
                </div>
                <div className="rounded-2xl border border-blue-200 bg-blue-50/60 p-4">
                  <p className="mb-2 text-xs font-bold uppercase tracking-[0.2em] text-blue-700">
                    Transformed intelligence
                  </p>
                  <pre className="whitespace-pre-wrap text-xs text-blue-950">{result.after}</pre>
                </div>
              </div>
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-950">
                <CheckCircle2 className="mr-2 inline h-4 w-4" /> Trace ID:{" "}
                <strong>{result.traceId}</strong> · Endpoint: {result.endpointInvoked}
              </div>
              <pre className="max-h-80 overflow-auto rounded-2xl border border-slate-200 bg-slate-950 p-4 text-xs text-emerald-100">
                {JSON.stringify(result.evidencePacket, null, 2)}
              </pre>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                {result.boundary}
              </div>
              <button onClick={exportPacket} className="executive-button bg-emerald-600 text-white">
                <Download className="h-4 w-4" /> Export evidence packet
              </button>
            </>
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-300 p-10 text-center text-slate-500">
              Run a customer workload to generate the evidence packet.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
