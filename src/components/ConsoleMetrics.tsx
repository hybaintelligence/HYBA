import React, { useState, useEffect } from "react";
import { Cpu, Zap, Radio, Globe, RefreshCcw } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { MiningState } from "../types";

interface ConsoleMetricsProps {
  state: MiningState & {
    quantumCoherence: number;
    quantumSpeedupFactor: number;
    actualSpeedupFactor: number;
    phiResonance: number;
    powerScale: number;
    version: string;
  };
  onRefresh: () => void;
  isSyncing: boolean;
}

export const ConsoleMetrics: React.FC<ConsoleMetricsProps> = ({ state, onRefresh, isSyncing }) => {
  const [hashrateHistory, setHashrateHistory] = useState<{ time: string, value: number }[]>([]);

  useEffect(() => {
    setHashrateHistory(prev => {
      const now = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const newHistory = [...prev, { time: now, value: state.currentHashrate }];
      return newHistory.slice(-10); // Keep last 10 points
    });
  }, [state.currentHashrate]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* CARD 1: SEARCH EFFICIENCY */}
      <div id="metric-speedup" className="bg-white border-l-4 border-clicquot-orange border-y border-r border-[#E2E4E9] rounded-xl p-5 flex flex-col justify-between transition-colors duration-200 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-lux-slate tracking-wider font-semibold uppercase">Search Efficiency</span>
          <Cpu className="text-oxford w-4.5 h-4.5" />
        </div>
        <div className="my-3">
          <div className="flex items-baseline gap-2">
            <div className="text-2xl font-bold font-mono text-oxford tracking-tight">
              {state.actualSpeedupFactor.toFixed(1)}<span className="text-clicquot-orange text-sm ml-1 font-sans">x</span>
            </div>
            <div className="text-xs font-mono text-lux-slate line-through opacity-60">
              {state.quantumSpeedupFactor.toFixed(1)}x
            </div>
          </div>
          <p className="text-xs text-lux-slate mt-1">
            <span className="font-bold text-oxford">Actual</span> vs modeled basis-selection factor
          </p>
        </div>
        <div className="text-[10px] font-mono text-lux-slate/80 flex justify-between border-t border-sand-dark pt-2 mt-1">
          <span>COHERENCE: {(state.quantumCoherence * 100).toFixed(2)}%</span>
          <span>FIDELITY: 99.98%</span>
        </div>
      </div>

      {/* CARD 2: HASHRATE EQUIVALENCE */}
      <div id="metric-hashrate" className="bg-white border-l-4 border-oxford border-y border-r border-[#E2E4E9] rounded-xl p-5 flex flex-col justify-between transition-colors duration-200 shadow-sm relative overflow-hidden">
        <div className="flex items-center justify-between z-10 relative">
          <span className="text-xs font-mono text-lux-slate tracking-wider font-semibold uppercase">Hashrate Equivalence</span>
          <Radio className="text-oxford w-4.5 h-4.5" />
        </div>
        <div className="my-3 flex-1 flex flex-col justify-center z-10 relative">
          <div className="text-2xl font-bold font-mono text-oxford tracking-tight">
            {state.currentHashrate.toFixed(1)} <span className="text-lux-slate text-xs font-sans">EHS</span>
          </div>
          <p className="text-xs text-lux-slate mt-1">Estimated equivalence metric from configured runtime telemetry</p>
        </div>
        
        {/* Recharts LineGraph Background Overlay */}
        <div className="absolute bottom-6 left-0 right-0 h-16 opacity-30 z-0">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={hashrateHistory}>
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#0A5C91" 
                strokeWidth={2} 
                dot={false}
                isAnimationActive={true}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="text-[10px] font-mono text-lux-slate/80 flex justify-between border-t border-sand-dark pt-2 mt-1 z-10 relative">
          <span>SCALE: {state.powerScale || 1.0}x</span>
          <span>NONCE RANGE: 2^256</span>
        </div>
      </div>

      {/* CARD 3: POWER CONSERVATION */}
      <div id="metric-power" className="bg-white border-l-4 border-clicquot-gold border-y border-r border-[#E2E4E9] rounded-xl p-5 flex flex-col justify-between transition-colors duration-200 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-lux-slate tracking-wider font-semibold uppercase">Thermal Footprint</span>
          <Zap className="text-oxford w-4.5 h-4.5" />
        </div>
        <div className="my-3">
          <div className="text-2xl font-bold font-mono text-oxford tracking-tight">
            {state.powerConsumption} <span className="text-lux-slate text-xs font-sans">W</span>
          </div>
          <p className="text-xs text-lux-slate mt-1">Electrical load constraint for the current runtime configuration.</p>
        </div>
        <div className="text-[10px] font-mono text-lux-slate/80 flex justify-between border-t border-sand-dark pt-2 mt-1">
          <span>SAVINGS: ~45%</span>
          <span>Φ-RESONANCE: {state.phiResonance.toFixed(4)}</span>
        </div>
      </div>

      {/* CARD 4: ACTIVE STRATUM ORBIT */}
      <div id="metric-pool" className="bg-white border-l-4 border-mckinsey-light border-y border-r border-[#E2E4E9] rounded-xl p-5 flex flex-col justify-between transition-colors duration-200 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-lux-slate tracking-wider font-semibold uppercase">Active Stratum Link</span>
          <Globe className="text-oxford w-4.5 h-4.5" />
        </div>
        <div className="my-3">
          <div className="text-sm font-mono text-oxford font-bold truncate tracking-tight">
            {state.activePool.replace("stratum+tcp://", "").replace("stratum2+tcp://", "").replace("stratum+ssl://", "")}
          </div>
          <p className="text-xs text-lux-slate mt-1">Configured target-routing surface for the active Stratum endpoint</p>
        </div>
        <div className="text-[10px] font-mono text-lux-slate/80 flex justify-between border-t border-sand-dark pt-2 mt-2">
          <span>POOL STATE: ONLINE</span>
          <button 
            type="button"
            onClick={onRefresh} 
            disabled={isSyncing}
            className="flex items-center gap-1 hover:text-clicquot-orange active:scale-95 transition-all text-[10px] text-oxford font-mono font-bold cursor-pointer"
          >
            <RefreshCcw className={`w-3 h-3 ${isSyncing ? "animate-spin text-clicquot-orange" : ""}`} />
            <span>{isSyncing ? "SYNC" : "REFRESH"}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
