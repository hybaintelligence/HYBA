import React, { useEffect, useState } from "react";
import { Shield, CheckCircle2, XCircle, FileCheck, Lock, Fingerprint, AlertTriangle } from "lucide-react";

interface ManifestData {
  version: string;
  manifest_hash: string;
  certificate_ledger_root_hash: string;
  runtime_manifest_hash: string;
  quantum_speedup_claimed: boolean;
  phi_tier_composition: Array<{
    label: string;
    phi_exponent: number;
    base10_exponent: number;
    phi_multiplier: number;
    scale_factor: number;
  }>;
  phi_stability_diagnostic: {
    stable: boolean;
    severity: string;
    recommendation: string;
    phi_ratio_error: number;
  };
  compliance: {
    jurisdictions: string[];
    guarantees: string[];
  };
  capability_manifest: {
    capability_flags: Record<string, boolean>;
  };
}

const UNAVAILABLE = "—";

function fmtHash(hash: string): string {
  if (!hash || hash.length < 16) return UNAVAILABLE;
  return `${hash.slice(0, 8)}...${hash.slice(-8)}`;
}

export function SovereignGenesisPanel() {
  const [manifest, setManifest] = useState<ManifestData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/manifest.json")
      .then(res => {
        if (!res.ok) throw new Error("Manifest not found");
        return res.json();
      })
      .then((data: ManifestData) => {
        setManifest(data);
        setIsLoading(false);
      })
      .catch(err => {
        setError(err instanceof Error ? err.message : "Failed to load manifest");
        setIsLoading(false);
      });
  }, []);

  if (isLoading) {
    return (
      <div className="overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white/90 shadow-sm">
        <PanelHeader />
        <div className="p-4 space-y-3">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="animate-pulse h-6 bg-slate-200/50 rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !manifest) {
    return (
      <div className="overflow-hidden rounded-[1.5rem] border border-amber-200 bg-amber-50/90 shadow-sm">
        <PanelHeader />
        <div className="p-4">
          <div className="flex items-center gap-2 text-amber-800">
            <AlertTriangle className="h-5 w-5" />
            <span className="text-xs font-mono">Manifest not loaded: {error || "Unknown error"}</span>
          </div>
          <p className="mt-2 text-xs text-amber-600">
            Generate manifest with: <code className="bg-amber-100 px-2 py-1 rounded">python scripts/generate_pulvini_manifest.py --production-runtime</code>
          </p>
        </div>
      </div>
    );
  }

  const tierLabels = manifest.phi_tier_composition.map(t => t.label).join(", ");
  const capabilityCount = Object.values(manifest.capability_manifest.capability_flags).filter(Boolean).length;
  const totalCapabilities = Object.keys(manifest.capability_manifest.capability_flags).length;

  return (
    <div className="overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white/90 shadow-sm backdrop-blur">
      <PanelHeader />
      
      <div className="p-4 space-y-4">
        {/* Constitutional Signatures */}
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/80 p-4">
          <div className="flex items-center gap-2 mb-3">
            <Fingerprint className="h-4 w-4 text-emerald-700" />
            <h4 className="text-xs font-black uppercase tracking-[0.18em] text-emerald-900">Constitutional Signatures</h4>
          </div>
          <div className="space-y-2 font-mono text-[10px]">
            <SignatureRow label="Manifest Hash" value={fmtHash(manifest.manifest_hash)} full={manifest.manifest_hash} />
            <SignatureRow label="Certificate Ledger Root" value={fmtHash(manifest.certificate_ledger_root_hash)} full={manifest.certificate_ledger_root_hash} />
            <SignatureRow label="Runtime Hash" value={fmtHash(manifest.runtime_manifest_hash)} full={manifest.runtime_manifest_hash} />
          </div>
        </div>

        {/* φ-Tier Composition */}
        <div className="rounded-xl border border-blue-200 bg-blue-50/80 p-4">
          <div className="flex items-center gap-2 mb-3">
            <FileCheck className="h-4 w-4 text-blue-700" />
            <h4 className="text-xs font-black uppercase tracking-[0.18em] text-blue-900">φ-Tier Scaling</h4>
          </div>
          <div className="space-y-2">
            <MetricLine label="Tiers Available" value={`${manifest.phi_tier_composition.length}`} />
            <MetricLine label="Tier Range" value={tierLabels} />
            <MetricLine label="φ-Stability" value={manifest.phi_stability_diagnostic.stable ? "STABLE" : "UNSTABLE"} 
              positive={manifest.phi_stability_diagnostic.stable} />
            <MetricLine label="Ratio Error" value={manifest.phi_stability_diagnostic.phi_ratio_error.toFixed(6)} />
          </div>
        </div>

        {/* Compliance Boundaries */}
        <div className="rounded-xl border border-purple-200 bg-purple-50/80 p-4">
          <div className="flex items-center gap-2 mb-3">
            <Lock className="h-4 w-4 text-purple-700" />
            <h4 className="text-xs font-black uppercase tracking-[0.18em] text-purple-900">Compliance Boundaries</h4>
          </div>
          <div className="space-y-2">
            <MetricLine label="Quantum Speedup Claimed" value={manifest.quantum_speedup_claimed ? "YES" : "NO"} 
              positive={!manifest.quantum_speedup_claimed} />
            <MetricLine label="Jurisdictions" value={manifest.compliance.jurisdictions.join(", ")} />
            <div className="mt-2 pt-2 border-t border-purple-200">
              <p className="text-[9px] font-mono text-purple-600 mb-2">GUARANTEES:</p>
              <div className="flex flex-wrap gap-1">
                {manifest.compliance.guarantees.slice(0, 4).map(g => (
                  <span key={g} className="rounded px-2 py-0.5 bg-purple-100 text-[9px] font-mono text-purple-700">
                    {g.replace(/_/g, " ").toUpperCase()}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Capability Manifest */}
        <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-4">
          <div className="flex items-center gap-2 mb-3">
            <Shield className="h-4 w-4 text-slate-700" />
            <h4 className="text-xs font-black uppercase tracking-[0.18em] text-slate-900">Runtime Capabilities</h4>
          </div>
          <MetricLine label="Capabilities Enabled" value={`${capabilityCount}/${totalCapabilities}`} />
          <div className="mt-3 grid grid-cols-2 gap-1.5">
            {Object.entries(manifest.capability_manifest.capability_flags).slice(0, 6).map(([key, enabled]) => (
              <CapabilityBadge key={key} name={key} enabled={enabled} />
            ))}
          </div>
        </div>

        {/* Event Classification Warning */}
        <div className="rounded-xl border-2 border-amber-300 bg-amber-50/95 p-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
            <div className="text-[10px] leading-5">
              <p className="font-black uppercase tracking-[0.14em] text-amber-900 mb-1">Dashboard Handoff Event</p>
              <p className="text-amber-700">
                This is NOT an accepted-share or revenue event. No quantum speedup claimed. No proof-of-work bypass. 
                Manifest display only.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function PanelHeader() {
  return (
    <div className="flex items-center gap-3 border-b border-slate-100 bg-gradient-to-r from-emerald-50 to-white px-5 py-4">
      <div className="rounded-xl bg-emerald-600 p-2 text-white">
        <Shield className="h-4 w-4" />
      </div>
      <div>
        <p className="text-[9px] font-mono font-bold uppercase tracking-[0.24em] text-slate-400">
          Constitutional Integrity
        </p>
        <h3 className="text-sm font-black uppercase tracking-[0.12em] text-slate-950">
          Sovereign Genesis Manifest
        </h3>
      </div>
    </div>
  );
}

function SignatureRow({ label, value, full }: { label: string; value: string; full: string }) {
  const [showFull, setShowFull] = useState(false);
  
  return (
    <div className="flex items-center justify-between gap-2 text-emerald-900 py-1">
      <span className="text-emerald-600">{label}</span>
      <button
        onClick={() => setShowFull(!showFull)}
        className="text-right font-bold hover:text-emerald-700 transition cursor-pointer"
        title={full}
      >
        {showFull ? full : value}
      </button>
    </div>
  );
}

function MetricLine({ label, value, positive }: { label: string; value: string; positive?: boolean }) {
  const colorClass = positive !== undefined 
    ? positive 
      ? "text-emerald-700" 
      : "text-red-700"
    : "text-slate-700";

  return (
    <div className="flex items-center justify-between gap-2 text-[11px] font-mono">
      <span className="text-slate-600">{label}</span>
      <span className={`font-bold ${colorClass}`}>{value}</span>
    </div>
  );
}

function CapabilityBadge({ name, enabled }: { name: string; enabled: boolean }) {
  const displayName = name.replace(/^supports_/, "").replace(/_/g, " ");
  
  return (
    <div className={`flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-[9px] font-mono ${
      enabled 
        ? "bg-emerald-100 text-emerald-700 border border-emerald-200" 
        : "bg-slate-100 text-slate-500 border border-slate-200"
    }`}>
      {enabled ? <CheckCircle2 className="h-3 w-3 flex-shrink-0" /> : <XCircle className="h-3 w-3 flex-shrink-0" />}
      <span className="truncate" title={displayName}>{displayName}</span>
    </div>
  );
}
