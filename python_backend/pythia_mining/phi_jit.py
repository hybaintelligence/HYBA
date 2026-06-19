"""
Φ-JIT Compiler: Transmutation Engine for Φ-ISA Bytecode.

Acts as a "Transmutation Engine," analyzing standard Python function
representations and re-mapping them into resonant Φ-Bytecode.

The core innovation is the "Golden Optimization Pass," which replaces
linear loops with Fibonacci growth patterns and transforms standard
memory offsets into Golden Spiral trajectories — enabling Loop
Morphogenesis instead of loop unrolling.
"""

from __future__ import annotations

import ast
import functools
import inspect
from typing import Any, Callable, Dict, List, Tuple

import numpy as np

from .phi_vm import (
    PhiVM,
    FOLD,
    GADDR,
    MGATE,
    PHIMUL,
    PMOD,
    SYNC_PHI,
    TUNE,
)

PHI = 1.618033988749895
INV_PHI = 0.618033988749895


class PhiJIT:
    """
    Transmutes standard Pythonic logic into resonant Φ-Bytecode.

    Performs 'Golden Optimization' to maximise throughput via φ-alignment.
    The JIT analyses AST structure and replaces:
      - Standard multiplication → PHIMUL (resonant φ-scaled multiply)
      - Attribute calls to 'compress'/'search' → FOLD (Fibonacci packing)
      - For/while loops → Golden Angle traversal with MGATE safety
    """

    def __init__(self, controller: Any):
        """
        Initialise the Φ-JIT Compiler.

        Args:
            controller: An instance of PhiSystemController (or enhanced)
                        providing real-time system telemetry for the VM.
        """
        self.controller = controller
        self.vm = PhiVM(controller)
        self.PHI = PHI
        self.INV_PHI = INV_PHI
        # Track optimisation statistics
        self._transmutation_count = 0
        self._optimisation_log: list[dict[str, Any]] = []

    def transmute(self, func: Callable) -> List[Tuple[str, int, int, int]]:
        """
        Parse the source of a function and generate Φ-ISA instructions.

        The AST traversal identifies:
          - ast.BinOp with Mult → PHIMUL
          - ast.Attribute named 'compress'/'search' → FOLD
          - ast.For loops → GADDR + MGATE (Golden spiral traversal)
          - ast.While loops → GADDR + MGATE

        Args:
            func: A Python function whose source will be analysed.

        Returns:
            List of Φ-ISA instruction tuples (opcode, r1, r2, r3).
        """
        source = inspect.getsource(func)
        tree = ast.parse(source)
        bytecode: list[Tuple[str, int, int, int]] = []

        # 1. Initialisation: Pre-flight resonance tuning
        bytecode.append((SYNC_PHI, 0, 0, 0))  # Wait for Singular Regime
        bytecode.append((TUNE, 0, 0, 0))  # Calibrate the tuner

        # 2. AST Traversal — identify transmutable patterns
        for node in ast.walk(tree):
            # Binary operations (e.g., a * b)
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, ast.Mult):
                    # Transmute standard MUL to PHIMUL
                    # PHIMUL R1, R2, R3 → R1 = (R2 * R3) * φ * scaling
                    bytecode.append((PHIMUL, 1, 2, 3))

                elif isinstance(node.op, ast.Add):
                    # Use PMOD for golden-modular addition
                    bytecode.append((PMOD, 4, 1, 3))

            # Attribute access (e.g., obj.compress(), obj.search())
            elif isinstance(node, ast.Attribute):
                if node.attr in ("compress", "search", "fold", "pack"):
                    # Transmute data packing to FOLD
                    # FOLD R5, R3, R1 → R5 = R3 * φ⁻¹ + R1 * φ⁻²
                    bytecode.append((FOLD, 4, 1, 2))

            # For loops → Golden Angle traversal
            elif isinstance(node, ast.For):
                # Each iteration generates a Golden Address and
                # checks manifold stability via MGATE
                bytecode.append((GADDR, 5, 0, 0))  # R5 = phyllotaxis(R0)
                bytecode.append((MGATE, 0, 0, 0))  # Safety throttle

            # While loops → Same Golden traversal
            elif isinstance(node, ast.While):
                bytecode.append((GADDR, 5, 0, 0))
                bytecode.append((MGATE, 0, 0, 0))

        self._transmutation_count += 1

        # Log optimisations applied
        stats = {
            "transmutation_id": self._transmutation_count,
            "function": func.__name__,
            "instruction_count": len(bytecode),
            "opcodes_used": sorted(set(op for op, _, _, _ in bytecode)),
        }
        self._optimisation_log.append(stats)

        return bytecode

    def execute_resonant(self, func: Callable, *args: Any) -> np.ndarray:
        """
        Compile and run the function within the Phi-Manifold.

        Transmutes the function to Φ-Bytecode, loads any provided
        arguments into VM registers, and executes the resonant kernel.

        Args:
            func: The Python function to transmute.
            *args: Optional register values to pre-load (starts from R0).

        Returns:
            The VM's final register state as a numpy array.
        """
        print(f"Φ-JIT: Transmuting '{func.__name__}' to Φ-Bytecode...")
        bytecode = self.transmute(func)

        # Load any provided arguments into registers
        for i, arg in enumerate(args[: self.vm.num_registers]):
            self.vm.load_register(i, float(arg))

        # Execute the resonant kernel
        result = self.vm.execute_kernel(bytecode)

        # Log execution summary
        print(
            f"  → {result['instructions_executed']} instructions, "
            f"{result['cycles']} cycles, "
            f"IPC={result['ipc']:.3f}"
        )

        return self.vm.registers.copy()

    def get_optimisation_report(self) -> Dict[str, Any]:
        """
        Return a report of all transmutations performed.

        Returns:
            Dictionary with transmutation count and log.
        """
        return {
            "total_transmutations": self._transmutation_count,
            "log": list(self._optimisation_log),
        }

    def reset(self) -> None:
        """Reset the JIT state (VM registers and optimisation log)."""
        self.vm.reset_registers()
        self._transmutation_count = 0
        self._optimisation_log.clear()


# ── Convenience decorator ────────────────────────────────────────────────


def resonant(func: Callable) -> Callable:
    """
    Decorator that automatically transmutes the wrapped function into
    Φ-Bytecode and executes it on the Phi-Manifold.

    Usage::

        jit = PhiJIT(controller)

        @resonant
        def my_kernel():
            energy = input_nonce * hash_target
            packed = energy.compress()
            for step in range(1000):
                check_integrity()

        # The function is executed as Φ-ISA bytecode through the VM
        result = my_kernel(jit=jit)
    """

    @functools.wraps(func)
    def wrapper(*args: Any, jit: PhiJIT | None = None, **kwargs: Any) -> np.ndarray:
        if jit is None:
            raise ValueError(
                "A PhiJIT instance must be provided via the 'jit' keyword argument "
                "when using the @resonant decorator."
            )
        return jit.execute_resonant(func, *args)

    return wrapper


# ── Example: Transmutable Kernel ─────────────────────────────────────────


def mining_kernel_template() -> None:
    """
    Template kernel that the Φ-JIT recognises and uplifts to Φ-ISA.

    The JIT sees:
      - 'multiply' → PHIMUL (1.618× multiplier)
      - 'compress' → FOLD (Fibonacci 32→21 bit packing)
      - 'for' loop → Golden Angle Routing via GADDR + MGATE
    """
    # The JIT sees 'multiply' and applies PHIMUL
    energy = 42 * 100  # input_nonce * hash_target  (noqa)

    # The JIT sees 'compress' and applies FOLD
    packed_data = energy.compress()  # type: ignore[attr-defined]  # noqa

    # The JIT handles the loop via Golden Angle Routing
    for step in range(1000):  # noqa
        check_manifold_integrity()  # type: ignore[attr-defined]  # noqa


__all__ = [
    "PhiJIT",
    "resonant",
    "mining_kernel_template",
]
