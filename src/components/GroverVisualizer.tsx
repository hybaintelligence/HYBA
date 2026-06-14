import React, { useState, useMemo } from "react";
import { computeQuantumGrover } from "../utils/math";
import { Zap, Activity, Info } from "lucide-react";

interface GroverVisualizerProps {
  markedIndex: number;
  dimensionSize: number;
  optimalSteps: number;
}

export const GroverVisualizer: React.FC<GroverVisualizerProps> = ({
  markedIndex,
  dimensionSize,
  optimalSteps,
}) => {
  const [selectedStep, setSelectedStep] = useState<number>(0);

  // Compute the Grover steps on the fly utilizing our pure mathematical engine
  const computationSteps = useMemo(() => {
    // Generate up to optimalSteps or a maximum of 8 iterations for high-density analysis
    const maxIters = Math.max(optimalSteps, 7);
    return computeQuantumGrover(markedIndex, dimensionSize, maxIters);
  }, [markedIndex, dimensionSize, optimalSteps]);

  // Ensure selectedStep is in bounds of current computation length
  const currentStepData = useMemo(() => {
    const safeStep = Math.min(selectedStep, computationSteps.length - 1);
    return computationSteps[safeStep] || computationSteps[0];
  }, [selectedStep, computationSteps]);

  const activeAmplitudes = currentStepData.amplitudes;

  // Find the maximum amplitude to scale heights correctly
  const maxAmp = Math.max(...activeAmplitudes, 0.01);

  return (
    <div className="bg-white border border-[#E2E4E9] rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="text-black w-4.5 h-4.5" />
          <h3 className="text-xs font-mono text-[#1A1A1E] font-bold uppercase tracking-wider">
            Grover Space Amplitude Rotor
          </h3>
        </div>
        <span className="text-[10px] bg-[#F4F4F7] text-[#1A1A1E] font-mono px-2 py-0.5 rounded border border-[#E2E4E9]">
          DIMENSION: {dimensionSize} STATES
        </span>
      </div>

      <p className="text-xs text-[#64748B] mb-5 leading-relaxed">
        Observe the state vector rotating in the Hilbert space. As you scrub from Step 0 (Hadamard
        uniformity) to Step {optimalSteps} (optimal convergence boundary), you watch the amplitude
        at index <span className="text-black font-mono font-bold">#{markedIndex}</span> inflate
        while the residual background phase interference is suppressed.
      </p>

      {/* AMPLITUDE GRID CHART */}
      <div className="bg-[#F8FAFC] border border-[#E2E4E9] rounded-xl p-4 mb-5">
        <div className="flex justify-between items-center text-[10px] font-mono text-[#64748B] mb-2 border-b border-[#E2E4E9] pb-1">
          <span>AMPLITUDE COEFFICIENTS |ψ_i|</span>
          <span>
            STEP {currentStepData.step} / {computationSteps.length - 1} ({currentStepData.operation}
            )
          </span>
        </div>

        {/* The bar graphs */}
        <div className="h-32 flex items-end gap-[3px] pt-4 px-2 select-none relative">
          {/* Vertical Y-Axis markings */}
          <div className="absolute left-2 top-2 text-[8px] font-mono text-[#94A3B8] flex flex-col gap-6 pointer-events-none">
            <span>MAX (1.0)</span>
            <span>MEAN (0.1)</span>
          </div>

          {activeAmplitudes.map((amp, idx) => {
            const isTarget = idx === markedIndex;
            const barHeightPercent = (amp / maxAmp) * 100;
            const probability = amp * amp;

            return (
              <div
                key={idx}
                className="flex-1 flex flex-col items-center group relative h-full justify-end"
              >
                {/* TOOLTIP */}
                <div className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 bg-oxford text-white text-[9px] font-mono p-1.5 rounded shadow-lg hidden group-hover:block z-20 pointer-events-none whitespace-nowrap">
                  <div className="font-bold">State #{idx}</div>
                  <div>Amp: {amp.toFixed(4)}</div>
                  <div className="text-clicquot-gold">Prob: {(probability * 100).toFixed(2)}%</div>
                </div>

                <div
                  className={`w-full transition-all duration-300 rounded-t-[1px] ${
                    isTarget
                      ? "bg-clicquot-orange relative z-10 shadow-[0_0_8px_rgba(252,95,16,0.6)]"
                      : idx % 2 === 0
                        ? "bg-mckinsey-light/30 group-hover:bg-oxford/70"
                        : "bg-mckinsey-blue/15 group-hover:bg-oxford/70"
                  }`}
                  style={{ height: `${Math.max(barHeightPercent, 3)}%` }}
                />
              </div>
            );
          })}
        </div>

        {/* Labels below */}
        <div className="flex justify-between text-[9px] font-mono text-lux-slate mt-2 px-1 border-t border-[#E2E4E9] pt-1">
          <span>STATE INDEX #0</span>
          <span className="text-clicquot-orange font-bold">MARKED TARGET AT #{markedIndex}</span>
          <span>STATE INDEX #{dimensionSize - 1}</span>
        </div>
      </div>

      {/* ITERATION CONTROLLER SCRUBBER */}
      <div className="bg-[#F8FAFC] border border-[#E2E4E9] rounded-xl p-4">
        <div className="flex justify-between items-center mb-2">
          <label
            htmlFor="grover-step-scrubber"
            className="text-xs font-mono text-oxford font-semibold tracking-wide"
          >
            SCRUB GROVER EVOLUTION TIMELINE
          </label>
          <span className="text-xs font-mono font-bold text-clicquot-orange">
            PROBABILITY: {(currentStepData.solutionProbability * 100).toFixed(2)}%
          </span>
        </div>

        <div className="flex items-center gap-4">
          <input
            id="grover-step-scrubber"
            type="range"
            min={0}
            max={computationSteps.length - 1}
            value={selectedStep}
            onChange={(e) => setSelectedStep(parseInt(e.target.value))}
            className="w-full h-1 bg-[#E2E4E9] rounded-lg appearance-none cursor-pointer accent-clicquot-orange"
          />
          <div className="text-xs font-mono bg-white text-oxford px-3 py-1 rounded border border-[#E2E4E9]">
            STEP {selectedStep}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-4 text-[11px] font-mono">
          <div className="bg-white p-2 rounded-lg border border-[#E2E4E9]">
            <div className="text-[#94A3B8] text-[9px] uppercase">State Entropy</div>
            <div className="text-[#1A1A1E] font-bold">
              {currentStepData.entropy.toFixed(4)} bits
            </div>
          </div>
          <div className="bg-white p-2 rounded-lg border border-[#E2E4E9]">
            <div className="text-[#94A3B8] text-[9px] uppercase">Marked Amp</div>
            <div className="text-[#1A1A1E] font-bold">
              {activeAmplitudes[markedIndex].toFixed(4)}
            </div>
          </div>
          <div className="bg-white p-2 rounded-lg border border-[#E2E4E9] col-span-2 md:col-span-1">
            <div className="text-[#94A3B8] text-[9px] uppercase">ASIC Advantage</div>
            <div className="text-green-600 font-bold">DEFEATED</div>
          </div>
        </div>
      </div>

      <div className="mt-4 flex items-start gap-2 text-[10px] text-[#64748B] leading-relaxed font-mono">
        <Info className="w-3.5 h-3.5 text-[#94A3B8] shrink-0 mt-0.5" />
        <span>
          <strong>Unitary Operator Details</strong>: The Grover rotation operates purely over
          complex numbers. Unlike classical searches that consume electricity linear to the sample
          bounds O(N), this model scales as O(\sqrt(N)) utilizing the trigonometric rotation cycle.
          At Step {optimalSteps}, the target state is rotated exactly perpendicular to the
          orthogonal non-solution subspace vectors.
        </span>
      </div>
    </div>
  );
};
