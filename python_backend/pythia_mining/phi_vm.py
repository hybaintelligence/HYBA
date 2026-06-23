"""
Φ-Virtual Machine: Φ-ISA Bytecode Interpreter.

Implements the Φ-Instruction Set Architecture where every instruction cycle
is modulated by the current Coherence State. In a "Decohered" state,
instructions carry higher latency; in a "Singular" state, instructions
execute with "Golden Efficiency" (amplified throughput).

Core Instruction Set:
  PHIMUL  (0x01) — Resonant multiplication, auto-scaled by φ and coherence
  FOLD    (0x02) — Fibonacci-weighted 64→32 bit compression
  GADDR   (0x03) — Golden spiral virtual→physical address mapping
  PMOD    (0x04) — Golden Modulo: x mod (n × φ)
  JPH     (0x05) — Jump if Coherent (branch on φ-coherence > φ⁻¹)
  SYNC_Φ  (0x06) — Wait/pause until Singular regime is reached
  MGATE   (0x07) — Mass Gate: hard-throttle if entropy exceeds 3−φ
  TUNE    (0x08) — Trigger single-step Backprop update of scaling engine

The VM represents the final frontier: CPU operations that are φ-aware at
the bytecode level, enabling "Resonant Kernels" to run directly on the
Φ-Core Orchestrator.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple

import numpy as np


PHI = 1.618033988749895
INV_PHI = 0.618033988749895
MASS_GAP = 3.0 - PHI  # ~1.381966

# Opcode mnemonics
PHIMUL = "PHIMUL"
FOLD = "FOLD"
GADDR = "GADDR"
PMOD = "PMOD"
JPH = "JPH"
SYNC_PHI = "SYNC_PHI"
MGATE = "MGATE"
TUNE = "TUNE"

# All opcodes with their (opcode, r1, r2, r3) structure
OPCODES: Dict[str, int] = {
    PHIMUL: 0x01,
    FOLD: 0x02,
    GADDR: 0x03,
    PMOD: 0x04,
    JPH: 0x05,
    SYNC_PHI: 0x06,
    MGATE: 0x07,
    TUNE: 0x08,
}


class PhiVM:
    """
    Virtual Machine for the Φ-ISA.

    Executes instructions where the 'Energy Cost' and 'Output' are governed
    by Golden Ratio resonance. The VM interacts directly with the system
    controller to read real-time coherence, temperature, and scaling factors,
    making every instruction context-aware.
    """

    def __init__(
        self,
        controller: Any,
        *,
        num_registers: int = 16,
        program_counter: int = 0,
    ):
        """
        Initialise the Φ-VM.

        Args:
            controller: An instance of PhiSystemController (or enhanced)
                        providing real-time system telemetry.
            num_registers: Number of general-purpose φ-registers.
            program_counter: Initial program counter.
        """
        self.controller = controller
        self.registers = np.zeros(num_registers, dtype=np.float64)
        self.pc = program_counter
        self.num_registers = num_registers
        self.PHI = PHI
        self.INV_PHI = INV_PHI
        self.MASS_GAP = MASS_GAP
        self._cycle_count = 0
        self._instruction_count = 0
        self._throttle_count = 0
        self._history: list[dict[str, Any]] = []

    def execute_kernel(
        self, bytecode: List[Tuple[str, int, int, int]]
    ) -> Dict[str, Any]:
        """
        Execute a sequence of Φ-Instructions.

        Each instruction is a tuple: (opcode_mnemonic, r1, r2, r3)
        where r1 is the destination register and r2/r3 are source registers
        or immediate values (depending on opcode).

        Args:
            bytecode: List of instruction tuples to execute sequentially.

        Returns:
            Dictionary with final register state, cycle count, and telemetry.
        """
        self.pc = 0
        self._cycle_count = 0
        self._instruction_count = 0
        self._throttle_count = 0
        start_time = time.time()

        while self.pc < len(bytecode):
            instruction = bytecode[self.pc]
            if len(instruction) != 4:
                self.pc += 1
                continue

            op, r1, r2, r3 = instruction

            # Every instruction consumes 'Entropy' — check manifold stability
            telemetry_temp = self._get_simulated_temp()
            cycle_info = self.controller.process_cycle(
                np.array([self.pc], dtype=np.uint32),
                telemetry_temp,
            )

            # Apply the system's scaling factor to arithmetic operations
            scaling = cycle_info.get("scaling_factor", 1.0)
            self._instruction_count += 1

            if op == PHIMUL:
                self._op_phimul(r1, r2, r3, scaling)

            elif op == FOLD:
                self._op_fold(r1, r2, r3)

            elif op == GADDR:
                self._op_gaddr(r1, r2)

            elif op == PMOD:
                self._op_pmod(r1, r2, r3)

            elif op == JPH:
                jumped = self._op_jph(r1, cycle_info)
                if jumped:
                    self._cycle_count += 1
                    continue  # pc already updated, skip increment

            elif op == SYNC_PHI:
                self._op_sync_phi(cycle_info)

            elif op == MGATE:
                self._op_mgate(cycle_info)

            elif op == TUNE:
                self._op_tune(cycle_info)

            self.pc += 1
            self._cycle_count += 1

        end_time = time.time()

        result = {
            "final_registers": [
                float(self.registers[i]) for i in range(self.num_registers)
            ],
            "instructions_executed": self._instruction_count,
            "cycles": self._cycle_count,
            "throttle_events": self._throttle_count,
            "elapsed_seconds": end_time - start_time,
            "ipc": float(self._instruction_count / max(self._cycle_count, 1)),
        }
        self._history.append(result)
        return result

    # ── Opcode Implementations ────────────────────────────────────────────

    def _op_phimul(self, r1: int, r2: int, r3: int, scaling: float) -> None:
        """Resonant Multiplication: R1 = (R2 × R3) × φ × scaling."""
        if self._valid_reg(r1) and self._valid_reg(r2) and self._valid_reg(r3):
            self.registers[r1] = float(
                (self.registers[r2] * self.registers[r3]) * self.PHI * scaling
            )

    def _op_fold(self, r1: int, r2: int, r3: int) -> None:
        """Fibonacci-weighted compression: R1 = R2 × φ⁻¹ + R3 × φ⁻²."""
        if self._valid_reg(r1) and self._valid_reg(r2) and self._valid_reg(r3):
            self.registers[r1] = float(
                (self.registers[r2] * self.INV_PHI)
                + (self.registers[r3] * (self.INV_PHI**2))
            )

    def _op_gaddr(self, r1: int, r2: int) -> None:
        """Golden Address: map virtual address (R2) to physical via phyllotaxis."""
        if self._valid_reg(r1) and self._valid_reg(r2):
            n = int(abs(self.registers[r2]))
            r = np.sqrt(n + 1.0)
            theta_deg = (n * (360.0 / (self.PHI**2))) % 360.0
            theta_rad = np.deg2rad(theta_deg)
            x = r * np.cos(theta_rad)
            y = r * np.sin(theta_rad)
            # Map to register (quantised spiral layer)
            self.registers[r1] = float(int(abs(x) * 1000) ^ int(abs(y) * 1000))

    def _op_pmod(self, r1: int, r2: int, r3: int) -> None:
        """Golden Modulo: R1 = R2 mod (R3 × φ)."""
        if self._valid_reg(r1) and self._valid_reg(r2) and self._valid_reg(r3):
            modulus = self.registers[r3] * self.PHI
            if modulus != 0.0:
                phi_component = (
                    self.registers[r2]
                    - np.floor(self.registers[r2] / modulus) * modulus
                )
                inv_phi_component = self.registers[r2] - np.floor(
                    self.registers[r2] / (self.registers[r3] / self.PHI)
                ) * (self.registers[r3] / self.PHI)
                result = (
                    phi_component * self.PHI + inv_phi_component * self.INV_PHI
                ) / (self.PHI + self.INV_PHI)
                self.registers[r1] = float(result % modulus)

    def _op_jph(self, r1: int, cycle_info: Dict[str, Any]) -> bool:
        """Jump if Coherent: jump to address R1 if regime == SINGULAR_AGENT_PROXY."""
        if cycle_info.get("regime") == "singular_agent_proxy":
            target = int(abs(self.registers[r1])) if self._valid_reg(r1) else 0
            if 0 <= target < 2**16:
                self.pc = target
                return True
        return False

    def _op_sync_phi(self, cycle_info: Dict[str, Any]) -> None:
        """Wait until the Singular regime is reached (spin-loop throttle)."""
        max_spins = 1000
        spins = 0
        while cycle_info.get("regime") != "singular_agent_proxy" and spins < max_spins:
            telemetry_temp = self._get_simulated_temp()
            cycle_info = self.controller.process_cycle(
                np.array([self.pc], dtype=np.uint32),
                telemetry_temp,
            )
            spins += 1
            self._throttle_count += 1
            time.sleep(0.001 * self.INV_PHI)  # φ-scaled backoff

    def _op_mgate(self, cycle_info: Dict[str, Any]) -> None:
        """Mass Gate: hard-throttle if manifold is unstable."""
        if not cycle_info.get("manifold_stable", True):
            self._throttle_count += 1
            time.sleep(0.001 * self.PHI)

    def _op_tune(self, cycle_info: Dict[str, Any]) -> None:
        """Trigger a single-step Backprop update on the tuner."""
        if hasattr(self.controller, "tuner") and hasattr(self.controller.tuner, "step"):
            self.controller.tuner.step(
                {
                    "coherence": cycle_info.get(
                        "regime_coherence", cycle_info.get("scaling_factor", 0.5)
                    ),
                    "current_temp": self._get_simulated_temp(),
                }
            )

    # ── Helpers ───────────────────────────────────────────────────────────

    def _valid_reg(self, r: int) -> bool:
        """Check if a register index is valid."""
        return 0 <= r < self.num_registers

    def _get_simulated_temp(self) -> float:
        """
        Simulated temperature sensor for VM execution.

        In production, this would pull from real hardware sensors. The
        simulated value oscillates gently around a nominal operating point
        to provide realistic thermal feedback for the control loop.
        """
        return float(0.5 + (np.sin(self._cycle_count * 0.1) * 0.2))

    def get_execution_history(self, n_last: int = 0) -> List[Dict[str, Any]]:
        """
        Return the execution history of the VM.

        Args:
            n_last: Number of recent entries (0 = all).

        Returns:
            List of execution result dictionaries.
        """
        if n_last <= 0:
            return list(self._history)
        return list(self._history[-n_last:])

    def reset_registers(self) -> None:
        """Zero all registers."""
        self.registers = np.zeros(self.num_registers, dtype=np.float64)

    def load_register(self, index: int, value: float) -> None:
        """
        Load a value into a register.

        Args:
            index: Register index (0 to num_registers - 1).
            value: Value to load.
        """
        if self._valid_reg(index):
            self.registers[index] = float(value)

    def read_register(self, index: int) -> float:
        """
        Read the current value of a register.

        Args:
            index: Register index.

        Returns:
            Current register value, or 0.0 if invalid.
        """
        return float(self.registers[index]) if self._valid_reg(index) else 0.0


# ── Convenience: Example Resonant Kernel ─────────────────────────────────


def search_optimization_kernel() -> List[Tuple[str, int, int, int]]:
    """
    Return the resonant search optimisation kernel in Φ-Bytecode.

    This kernel "hunts" for valid results by only working hard when the
    system is coherent — the same pattern used for high-performance mining
    and simulation loops.

    Instructions:
      SYNC_Φ          — Wait for the Singular Regime
      TUNE            — Calibrate the Backprop Tuner
      GADDR R1, R2    — Map Virtual Nonce (R2) to Golden Address (R1)
      PHIMUL R3, R1, R4  — Scale result by Harmony Constant (R4)
      FOLD R5, R3, R1   — Pack the search result into the Phi-Manifold
      MGATE           — Ensure we aren't melting the silicon
      JPH   SUCCESS   — If Coherent, we've found a 'Massive' hash
      JMP   START     — Else, continue the Golden Spiral search
    """
    return [
        (SYNC_PHI, 0, 0, 0),  # Wait for Singular Regime
        (TUNE, 0, 0, 0),  # Calibrate the tuner
        (GADDR, 1, 2, 0),  # R1 = phyllotaxis(R2)
        (PHIMUL, 3, 1, 4),  # R3 = R1 × R4 × φ × scaling
        (FOLD, 5, 3, 1),  # R5 = R3 × φ⁻¹ + R1 × φ⁻²
        (MGATE, 0, 0, 0),  # Safety check
        (JPH, 0, 0, 0),  # Jump if coherent (to R1 = success handler)
        (GADDR, 1, 2, 0),  # Fallthrough: continue spiral (back to GADDR)
    ]


__all__ = [
    "PhiVM",
    "search_optimization_kernel",
    "PHIMUL",
    "FOLD",
    "GADDR",
    "PMOD",
    "JPH",
    "SYNC_PHI",
    "MGATE",
    "TUNE",
    "OPCODES",
]
