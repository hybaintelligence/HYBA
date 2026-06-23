import React, { useMemo } from "react";
import { motion } from "motion/react";
import { PHI } from "../core/constants";

interface HilbertSpaceVisualizerProps {
  hashrate: number;
  powerScale: number;
  phiResonance: number;
  timeToNextShare: number; // in seconds
}

export const HilbertSpaceVisualizer: React.FC<HilbertSpaceVisualizerProps> = ({
  hashrate,
  powerScale,
  phiResonance,
  timeToNextShare,
}) => {
  // Generate dodecahedron vertices in 2D projection
  // Vertices of dodecahedron normalized and projected
  const vertices = useMemo(() => {
    const v: [number, number][] = [];
    const scale = 60;

    // (±1, ±1, ±1)
    for (const x of [-1, 1]) {
      for (const y of [-1, 1]) {
        for (const z of [-1, 1]) {
          // Simple perspective projection
          const px = (x + z * 0.5) * scale;
          const py = (y + z * 0.5) * scale;
          v.push([px, py]);
        }
      }
    }

    // (0, ±1/Φ, ±Φ)
    const invPhi = 1 / PHI;
    for (const y of [-invPhi, invPhi]) {
      for (const z of [-PHI, PHI]) {
        const px = (0 + z * 0.5) * scale;
        const py = (y + z * 0.5) * scale;
        v.push([px, py]);
      }
    }

    // (±1/Φ, ±Φ, 0)
    for (const x of [-invPhi, invPhi]) {
      for (const y of [-PHI, PHI]) {
        const px = (x + 0 * 0.5) * scale;
        const py = (y + 0 * 0.5) * scale;
        v.push([px, py]);
      }
    }

    // (±Φ, 0, ±1/Φ)
    for (const x of [-PHI, PHI]) {
      for (const z of [-invPhi, invPhi]) {
        const px = (x + z * 0.5) * scale;
        const py = (z + 0 * 0.5) * scale;
        v.push([px, py]);
      }
    }

    return v;
  }, []);

  return (
    <div className="bg-oxford border border-clicquot-gold/30 rounded-xl p-6 shadow-2xl overflow-hidden relative min-h-[340px]">
      <div className="absolute top-4 left-6 flex items-center gap-2">
        <div className="w-2 h-2 bg-clicquot-gold rounded-full animate-pulse" />
        <h3 className="text-[10px] font-mono text-clicquot-gold font-bold uppercase tracking-widest">
          Hilbert Space Telemetry | Φ-Resonant Dodecahedron
        </h3>
      </div>

      <div className="flex flex-col md:flex-row items-center justify-between mt-8 gap-8">
        {/* Galloping Dodecahedron Visual */}
        <div className="relative w-48 h-48 flex items-center justify-center">
          {/* Background Hilbert Curves Concept (Animated Rings) */}
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="absolute w-full h-full border border-lux-slate/20 rounded-full"
          />
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
            className="absolute w-4/5 h-4/5 border border-clicquot-gold/10 rounded-full"
          />

          {/* Dodecahedron */}
          <motion.div
            animate={{
              rotateX: [0, 360],
              rotateY: [0, 360],
              y: [-10, 10, -10], // "Galloping" vertical bounce
            }}
            transition={{
              rotateX: { duration: 10, repeat: Infinity, ease: "linear" },
              rotateY: { duration: 12, repeat: Infinity, ease: "linear" },
              y: { duration: 2, repeat: Infinity, ease: "easeInOut" },
            }}
            style={{ transformStyle: "preserve-3d" }}
            className="relative"
          >
            <svg width="150" height="150" viewBox="-100 -100 200 200" className="overflow-visible">
              <g className="stroke-clicquot-gold stroke-[1px] fill-clicquot-gold/10">
                {/* We'll just draw some edges for a wireframe look */}
                {vertices.map(([x, y], i) => (
                  <circle key={i} cx={x} cy={y} r="2" />
                ))}
                {/* Some lines to connect them (simplified for visual effect) */}
                {vertices.slice(0, 10).map(([x, y], i) => (
                  <line
                    key={i}
                    x1={x}
                    y1={y}
                    x2={vertices[(i + 2) % vertices.length][0]}
                    y2={vertices[(i + 2) % vertices.length][1]}
                  />
                ))}
              </g>
            </svg>
          </motion.div>
        </div>

        {/* Telemetry Readout */}
        <div className="flex-1 space-y-4 font-mono">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#001c3d] p-3 rounded border border-[#0A5C91]">
              <div className="text-[9px] text-[#94A3B8] uppercase">Sweep Velocity</div>
              <div className="text-sm font-bold text-white">{hashrate.toFixed(1)} EHS</div>
            </div>
            <div className="bg-[#001c3d] p-3 rounded border border-[#0A5C91]">
              <div className="text-[9px] text-[#94A3B8] uppercase">Energy Scale</div>
              <div className="text-sm font-bold text-white">
                10^{Math.log10(powerScale * 1e18).toFixed(0)}
              </div>
            </div>
          </div>

          <div className="bg-[#001c3d] p-4 rounded border border-[#0A5C91] relative overflow-hidden">
            <div className="absolute top-0 right-0 p-2 opacity-10">
              <span className="text-4xl text-clicquot-gold font-bold">Φ</span>
            </div>
            <div className="text-[9px] text-[#94A3B8] uppercase mb-1">
              Time to Next Share (Resonance Estimate)
            </div>
            <div className="text-2xl font-bold text-clicquot-gold">
              {timeToNextShare.toFixed(2)}s
            </div>
            <div className="mt-2 w-full bg-lux-slate/20 h-1 rounded-full overflow-hidden">
              <motion.div
                animate={{ width: ["0%", "100%"] }}
                transition={{ duration: timeToNextShare, repeat: Infinity, ease: "linear" }}
                className="bg-clicquot-gold h-full"
              />
            </div>
          </div>

          <div className="text-[10px] text-gray-400 italic">
            *Hilbert space projection stabilized at Φ-resonance {phiResonance.toFixed(4)}. Quantum
            tunneling detected in subspace vertices.
          </div>
        </div>
      </div>
    </div>
  );
};
