/**
 * ActionGuard Component - Agentic Safety & Governance
 *
 * Provides a consistent approval UI for proposed AI actions with blast radius assessment.
 * Implements proposal-first workflow with role-aware approval requirements.
 */

import React from "react";
import { ShieldAlert, CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import { calculateBlastRadius, type BlastRadiusAssessment, type ProposedAction } from "../utils/blastRadius";

interface ActionGuardProps {
  action: ProposedAction;
  blastRadius?: BlastRadiusAssessment;
  onApprove: () => void;
  onReject: () => void;
  evidenceSeal?: string;
  invariantStatus?: string;
  userRole?: string;
}

export function ActionGuard({
  action,
  blastRadius,
  onApprove,
  onReject,
  evidenceSeal,
  invariantStatus = "must pass",
  userRole,
}: ActionGuardProps) {
  const assessment = blastRadius || calculateBlastRadius(action);

  const levelColors: Record<string, string> = {
    "read-only": "border-green-200 bg-green-50 text-green-900",
    "low": "border-blue-200 bg-blue-50 text-blue-900",
    "medium": "border-yellow-200 bg-yellow-50 text-yellow-900",
    "high": "border-orange-200 bg-orange-50 text-orange-900",
    "critical": "border-red-200 bg-red-50 text-red-900",
  };

  const approvalBadge: Record<string, string> = {
    "none": "bg-green-100 text-green-800",
    "operator": "bg-blue-100 text-blue-800",
    "admin": "bg-purple-100 text-purple-800",
    "executive": "bg-orange-100 text-orange-800",
    "board": "bg-red-100 text-red-800",
  };

  return (
    <div className={`rounded-xl border-2 p-6 ${levelColors[assessment.level]}`}>
      <div className="flex items-center gap-3 mb-4">
        <ShieldAlert className="h-6 w-6" />
        <div>
          <h3 className="font-black text-lg">Intelligence Proposal: Approval Required</h3>
          <p className="text-sm opacity-90">
            Blast Radius: <span className="font-bold uppercase">{assessment.level}</span>
          </p>
        </div>
      </div>

      <div className="bg-white/80 rounded-lg p-4 mb-4 border border-current/20">
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="font-semibold text-sm">Proposed Action:</p>
            <code className="text-sm font-mono bg-black/5 px-2 py-1 rounded mt-1 inline-block">
              {action.command}
            </code>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${approvalBadge[assessment.approvalLevel]}`}>
            {assessment.approvalLevel} approval
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm mt-4">
          <div className="bg-black/5 p-3 rounded">
            <p className="font-semibold text-xs uppercase opacity-70">Blast Radius</p>
            <p className="font-mono font-bold">{assessment.description}</p>
          </div>
          <div className="bg-black/5 p-3 rounded">
            <p className="font-semibold text-xs uppercase opacity-70">Evidence</p>
            <p className="font-mono font-bold">{evidenceSeal ? "Sealed" : "Pending"}</p>
          </div>
          <div className="bg-black/5 p-3 rounded">
            <p className="font-semibold text-xs uppercase opacity-70">Affected Systems</p>
            <p className="font-mono text-xs">{assessment.affectedSystems.join(", ")}</p>
          </div>
          <div className="bg-black/5 p-3 rounded">
            <p className="font-semibold text-xs uppercase opacity-70">Rollback Complexity</p>
            <p className="font-mono font-bold capitalize">{assessment.rollbackComplexity}</p>
          </div>
        </div>

        {(evidenceSeal || invariantStatus) && (
          <div className="mt-3 pt-3 border-t border-current/20 text-xs">
            <div className="flex gap-4">
              {evidenceSeal && (
                <div>
                  <span className="font-semibold">Evidence Seal:</span>{" "}
                  <span className="font-mono">{evidenceSeal}</span>
                </div>
              )}
              {invariantStatus && (
                <div>
                  <span className="font-semibold">Invariants:</span>{" "}
                  <span className="font-mono">{invariantStatus}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="flex items-start gap-2 mb-4 p-3 bg-black/5 rounded-lg">
        <AlertTriangle className="h-5 w-5 flex-shrink-0 mt-0.5" />
        <p className="text-sm">
          <strong>Claim Boundary:</strong> This is a proposal-only action. Human approval is required
          before execution. The action will not execute until explicitly approved.
        </p>
      </div>

      <div className="flex gap-3">
        <button
          onClick={onApprove}
          className="flex-1 flex items-center justify-center gap-2 bg-black text-white py-3 rounded-lg font-bold hover:bg-black/80 transition-colors"
        >
          <CheckCircle className="h-5 w-5" />
          Approve & Execute
        </button>
        <button
          onClick={onReject}
          className="flex-1 flex items-center justify-center gap-2 bg-white/50 border-2 border-current py-3 rounded-lg font-bold hover:bg-white/70 transition-colors"
        >
          <XCircle className="h-5 w-5" />
          Reject Proposal
        </button>
      </div>

      {userRole && (
        <p className="mt-3 text-xs text-center opacity-70">
          Current role: <span className="font-mono font-bold">{userRole}</span> · Required:{" "}
          <span className="font-mono font-bold">{assessment.approvalLevel}</span>
        </p>
      )}
    </div>
  );
}

/**
 * Compact version for inline use in chat interfaces
 */
export function CompactActionGuard({
  action,
  onApprove,
  onReject,
}: {
  action: ProposedAction;
  onApprove: () => void;
  onReject: () => void;
}) {
  const assessment = calculateBlastRadius(action);

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm">
      <div className="flex items-center gap-2 text-amber-900 font-bold mb-2">
        <ShieldAlert className="h-4 w-4" />
        Action Requires Approval
      </div>
      <code className="block bg-white p-2 rounded mb-3 text-xs">{action.command}</code>
      <div className="flex gap-2">
        <button
          onClick={onApprove}
          className="flex-1 bg-amber-600 text-white py-2 rounded font-bold hover:bg-amber-700"
        >
          Approve
        </button>
        <button
          onClick={onReject}
          className="flex-1 bg-white border border-amber-300 py-2 rounded font-bold hover:bg-amber-100"
        >
          Reject
        </button>
      </div>
    </div>
  );
}
