/**
 * PresetSelector Component - Intent-First Provisioning
 *
 * Provides a consistent UI for selecting provisioning presets across CIaaS and QIaaS.
 * Implements the plan's design for governance-aware preset selection.
 */

import React from "react";
import { Sparkles, Shield, Zap } from "lucide-react";

export type GovernanceLevel = "strict" | "balanced" | "relaxed";

export interface ProvisioningPreset {
  id: string;
  name: string;
  description: string;
  governance: GovernanceLevel;
  config: Record<string, any>;
}

interface PresetSelectorProps {
  presets: ProvisioningPreset[];
  selectedPreset: string;
  onSelect: (preset: ProvisioningPreset) => void;
  disabled?: boolean;
}

const governanceColors: Record<GovernanceLevel, string> = {
  strict: "bg-red-100 text-red-800 border-red-200",
  balanced: "bg-blue-100 text-blue-800 border-blue-200",
  relaxed: "bg-green-100 text-green-800 border-green-200",
};

const governanceIcons: Record<GovernanceLevel, React.ReactNode> = {
  strict: <Shield className="h-3.5 w-3.5" />,
  balanced: <Zap className="h-3.5 w-3.5" />,
  relaxed: <Sparkles className="h-3.5 w-3.5" />,
};

export function PresetSelector({ presets, selectedPreset, onSelect, disabled }: PresetSelectorProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {presets.map((preset) => {
        const isSelected = preset.id === selectedPreset;
        const GovernanceIcon = governanceIcons[preset.governance];

        return (
          <button
            key={preset.id}
            onClick={() => onSelect(preset)}
            disabled={disabled}
            className={`
              text-left p-5 border-2 rounded-xl transition-all group
              ${isSelected ? "border-primary bg-primary/5" : "border-transparent hover:border-primary/50 bg-card"}
              ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
            `}
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <h3 className={`text-base font-bold ${isSelected ? "text-primary" : "group-hover:text-primary"}`}>
                {preset.name}
              </h3>
              <span
                className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase border flex items-center gap-1 ${governanceColors[preset.governance]}`}
              >
                {GovernanceIcon}
                {preset.governance}
              </span>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed">{preset.description}</p>
            {isSelected && (
              <div className="mt-3 pt-3 border-t border-primary/20">
                <span className="text-xs font-semibold text-primary">Selected</span>
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}

/**
 * Compact version for inline use
 */
export function CompactPresetSelector({
  presets,
  selectedPreset,
  onSelect,
}: {
  presets: ProvisioningPreset[];
  selectedPreset: string;
  onSelect: (preset: ProvisioningPreset) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {presets.map((preset) => {
        const isSelected = preset.id === selectedPreset;
        return (
          <button
            key={preset.id}
            onClick={() => onSelect(preset)}
            className={`
              px-3 py-1.5 rounded-lg text-sm font-medium transition-all
              ${isSelected ? "bg-primary text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"}
            `}
          >
            {preset.name}
          </button>
        );
      })}
    </div>
  );
}
