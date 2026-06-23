/**
 * AdaptiveMetric Component - Mode-Aware Metric Display
 *
 * Displays technical metrics with skill-mode-appropriate translations.
 * Implements the plan's pattern for mode-specific labels and recommendations.
 */

import React from "react";
import { useSkillMode } from "../skillMode";
import { metricTranslations, type MetricTranslationKey } from "../intelligenceTranslations";

interface AdaptiveMetricProps {
  metricKey: MetricTranslationKey;
  value: React.ReactNode;
  unit?: string;
  technicalDetails?: React.ReactNode;
  showRecommendation?: boolean;
  className?: string;
}

export function AdaptiveMetric({
  metricKey,
  value,
  unit,
  technicalDetails,
  showRecommendation = true,
  className = "",
}: AdaptiveMetricProps) {
  const { mode, config } = useSkillMode();
  const translation = metricTranslations[metricKey]?.[mode] || metricTranslations[metricKey]?.["business"];

  if (!translation) {
    return null;
  }

  const modeColors: Record<string, string> = {
    executive: "border-purple-200 bg-purple-50",
    business: "border-blue-200 bg-blue-50",
    operator: "border-emerald-200 bg-emerald-50",
    analyst: "border-cyan-200 bg-cyan-50",
    engineer: "border-slate-200 bg-slate-50",
    auditor: "border-amber-200 bg-amber-50",
    expert: "border-violet-200 bg-violet-50",
  };

  return (
    <div className={`rounded-xl border p-4 ${modeColors[mode] || modeColors.business} ${className}`}>
      <div className="flex justify-between items-start mb-2">
        <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">
          {translation.label}
        </h4>
        <span className="text-xs font-mono bg-white/50 px-2 py-0.5 rounded">
          {mode}
        </span>
      </div>

      <div className="text-2xl font-bold text-slate-900">
        {value}
        {unit && <span className="text-lg font-normal text-slate-600 ml-1">{unit}</span>}
      </div>

      <p className="mt-2 text-sm text-slate-700 leading-relaxed">
        {translation.plainEnglish}
      </p>

      {showRecommendation && translation.recommendation && (
        <div className="mt-3 p-2 bg-white/50 rounded border-l-4 border-current">
          <p className="text-xs font-medium uppercase text-slate-900">Recommendation</p>
          <p className="text-sm italic text-slate-700">{translation.recommendation}</p>
        </div>
      )}

      {config.showTechnicalDefaults && (
        <div className="mt-3 pt-3 border-t border-current/20">
          <p className="text-xs font-semibold text-slate-900 mb-1">Operational Implication</p>
          <p className="text-xs text-slate-700">{translation.operationalImplication}</p>
          <p className="text-xs font-semibold text-slate-900 mt-2 mb-1">Evidence View</p>
          <p className="text-xs text-slate-700">{translation.evidenceView}</p>
          {technicalDetails && <div className="mt-2">{technicalDetails}</div>}
        </div>
      )}
    </div>
  );
}

/**
 * Compact version for dashboard use
 */
export function CompactAdaptiveMetric({
  metricKey,
  value,
  unit,
  className = "",
}: {
  metricKey: MetricTranslationKey;
  value: React.ReactNode;
  unit?: string;
  className?: string;
}) {
  const { mode } = useSkillMode();
  const translation = metricTranslations[metricKey]?.[mode] || metricTranslations[metricKey]?.["business"];

  if (!translation) {
    return null;
  }

  const modeColors: Record<string, string> = {
    executive: "border-purple-200 bg-purple-50",
    business: "border-blue-200 bg-blue-50",
    operator: "border-emerald-200 bg-emerald-50",
    analyst: "border-cyan-200 bg-cyan-50",
    engineer: "border-slate-200 bg-slate-50",
    auditor: "border-amber-200 bg-amber-50",
    expert: "border-violet-200 bg-violet-50",
  };

  return (
    <div className={`rounded-lg border bg-white p-3 ${modeColors[mode] || modeColors.business} ${className}`}>
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
        {translation.label}
      </p>
      <p className="text-lg font-bold text-slate-900 mt-1">
        {value}
        {unit && <span className="text-sm font-normal text-slate-600 ml-1">{unit}</span>}
      </p>
    </div>
  );
}

/**
 * Inline version for text-heavy contexts
 */
export function InlineAdaptiveMetric({
  metricKey,
  value,
  className = "",
}: {
  metricKey: MetricTranslationKey;
  value: React.ReactNode;
  className?: string;
}) {
  const { mode } = useSkillMode();
  const translation = metricTranslations[metricKey]?.[mode] || metricTranslations[metricKey]?.["business"];

  if (!translation) {
    return <span className={className}>{value}</span>;
  }

  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <span className="text-xs font-semibold text-slate-600">{translation.label}:</span>
      <span className="font-mono font-bold text-slate-900">{value}</span>
    </span>
  );
}
