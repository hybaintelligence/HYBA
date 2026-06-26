"""
Adversarial stress test for HYBA's quantum-substrate-invariance hypothesis.

The hypothesis under test (per QUANTUM_SUBSTRATE_INVARIANCE_LEDGER.md):
    same formal state + same formal operator -> same invariant, regardless
    of execution surface.

The existing harness (python_backend/pythia_self_healing/quantum_substrate_invariance.py)
currently cannot be imported in its own test file due to a sys.modules
registration bug (see agent brief). This script patches the loader locally
ONLY to run the stress battery below -- it does not modify the shipped module.

What this stress suite actually checks, that the original 3-surface harness
does not:

  1. SENSITIVITY: does assert_invariant_equivalence() actually detect a
     real injected substrate leak, or would it pass even if a surface were
     silently wrong? (mutation testing on the test itself)
  2. STRUCTURAL: are the three existing "surfaces" doing independent
     arithmetic, or are they the same scalar ops in the same order wearing
     three different syntaxes (comprehension / loop / map)? If the latter,
     IEEE-754 guarantees bit-identical output and the test proves nothing
     about substrate independence -- only that Python loops are equivalent
     to Python comprehensions.
  3. PRECISION DIVERGENCE: does the invariant survive a genuine change in
     numeric path -- float32 vs float64, and reduction order (sequential
     vs pairwise/tree sum)? This is where real CPU vs GPU/Metal divergence
     actually shows up, and the current harness never exercises it.
  4. SCALE: does the invariant hold under larger, more extreme, and
     near-degenerate states (very large amplitudes, near-zero norm,
     longer vectors) rather than only the single 5-element hand-picked
     standard_test_state().
"""
from __future__ import annotations

import importlib.util
import math
import random
import struct
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "python_backend" / "pythia_self_healing" / "quantum_substrate_invariance.py"


def load_module():
    spec = importlib.util.spec_from_file_location("quantum_substrate_invariance", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # the fix the shipped test file is missing
    spec.loader.exec_module(module)
    return module


m = load_module()

results_log = []


def report(name, passed, detail=""):
    results_log.append((name, passed, detail))
    flag = "PASS" if passed else "FAIL"
    print(f"[{flag}] {name}" + (f" -- {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# 1. SENSITIVITY: mutation testing on the invariance checker itself.
#    If we inject a deliberately WRONG result for one "surface", does
#    assert_invariant_equivalence() actually catch it?
# ---------------------------------------------------------------------------
state = m.standard_test_state()
real_results = m.run_all_surfaces(state)

raw_pp = m.execute_pure_python(state)
raw_cpu = m.execute_cpu_surface(state)
raw_acc = m.execute_accelerator_shadow_surface(state)

mutated = dict(real_results)
bad_vec = tuple(v * 1.0000001 for v in raw_pp)  # tiny deliberate leak, > tolerance
mutated["accelerator_shadow"] = m.invariant_signature(bad_vec)

caught = False
try:
    m.assert_invariant_equivalence(mutated)
except AssertionError:
    caught = True
report(
    "1a. detects a real injected substrate leak (1e-7 relative perturbation)",
    caught,
)

# Check the boundary: a leak just UNDER tolerance must NOT be flagged.
# NOTE: assert_invariant_equivalence also checks signature_hash, which will
# mismatch for ANY change in values (hash is based on round(...,15) values).
# We therefore rebuild the mutated entry via invariant_signature so the hash
# is consistent with the perturbed values -- matching what a real surface
# returning slightly-off results would produce.
bad_vec_tiny = tuple(v * (1.0 + 1e-14) for v in raw_pp)
mutated_tiny = dict(real_results)
mutated_tiny["accelerator_shadow"] = m.invariant_signature(bad_vec_tiny)
try:
    ok = m.assert_invariant_equivalence(mutated_tiny, tolerance=1e-12)
    report("1b. sub-tolerance noise correctly passes (tolerance isn't vacuous)", ok)
except AssertionError as e:
    report("1b. sub-tolerance noise correctly passes (tolerance isn't vacuous)", False, str(e))


# ---------------------------------------------------------------------------
# 2. STRUCTURAL: are the three surfaces actually independent execution
#    paths, or syntactic sugar over identical operation order?
# ---------------------------------------------------------------------------
bit_identical = (raw_pp == raw_cpu == raw_acc)
report(
    "2. surfaces are bit-identical (not just invariant-equivalent)",
    bit_identical,
    "TRUE means all 3 'surfaces' execute the identical scalar op in the "
    "identical order -- comprehension/loop/map are not independent numeric "
    "paths, so this triple never had a chance to disagree. The harness "
    "currently tests 'Python syntax is consistent', not 'substrate is "
    "invariant'. A real stress test needs a surface with a genuinely "
    "different reduction/precision path (see section 3).",
)


# ---------------------------------------------------------------------------
# 3. PRECISION DIVERGENCE: float32 truncation and summation-order changes,
#    which are the actual mechanisms by which CPU vs GPU/Metal results
#    diverge in real hardware. Does the invariant survive these?
# ---------------------------------------------------------------------------
def execute_float32_surface(state):
    out = []
    for index, value in enumerate(state.amplitudes):
        v32 = struct.unpack("f", struct.pack("f", value))[0]
        result = m.phi_resonance_operator(v32, index)
        result32 = struct.unpack("f", struct.pack("f", result))[0]
        out.append(result32)
    return tuple(out)


def execute_pairwise_sum_signature(values):
    """Same invariant formula as invariant_signature, but accumulate the
    'expectation' and 'signed_phase' sums in reverse / pairwise-tree order
    instead of left-to-right. Mathematically identical sums; floating point
    addition is not associative, so this is what a real parallel reduction
    on GPU would do differently from a sequential CPU accumulate."""
    vector = tuple(float(v) for v in values)
    n = len(vector)
    norm = math.sqrt(sum(v * v for v in reversed(vector)))
    exp_terms = [(i + 1) * vector[i] * vector[i] for i in range(n)]

    def tree_sum(xs):
        if len(xs) == 1:
            return xs[0]
        mid = len(xs) // 2
        return tree_sum(xs[:mid]) + tree_sum(xs[mid:])

    expectation = tree_sum(exp_terms) if exp_terms else 0.0
    phase_terms = [((-1) ** i) * vector[i] for i in range(n)]
    signed_phase = tree_sum(phase_terms) if phase_terms else 0.0
    return {"norm": norm, "expectation": expectation, "signed_phase": signed_phase}


float32_vec = execute_float32_surface(state)
ref_sig = m.invariant_signature(raw_pp)
f32_sig = m.invariant_signature(float32_vec)

delta_norm = abs(ref_sig["norm"] - f32_sig["norm"])
delta_exp = abs(ref_sig["expectation"] - f32_sig["expectation"])
report(
    "3a. invariant survives float32-precision execution surface",
    delta_norm < m.TOLERANCE_FLOAT32 and delta_exp < m.TOLERANCE_FLOAT32,
    f"delta_norm={delta_norm:.3e} delta_expectation={delta_exp:.3e} "
    f"vs float32_tolerance={m.TOLERANCE_FLOAT32:.0e} -- this is the first surface in this "
    f"whole exercise that does genuinely different arithmetic.",
)

tree_sig = execute_pairwise_sum_signature(raw_pp)
delta_exp_order = abs(ref_sig["expectation"] - tree_sig["expectation"])
delta_phase_order = abs(ref_sig["signed_phase"] - tree_sig["signed_phase"])
report(
    "3b. invariant survives reordered (tree-sum) floating-point reduction",
    delta_exp_order < m.TOLERANCE and delta_phase_order < m.TOLERANCE,
    f"delta_expectation={delta_exp_order:.3e} delta_signed_phase={delta_phase_order:.3e}",
)


# ---------------------------------------------------------------------------
# 4. SCALE: larger / more extreme states than the single hand-picked
#    5-element standard_test_state().
# ---------------------------------------------------------------------------
random.seed(20260626)
scale_failures = []
for trial in range(200):
    n = random.choice([2, 5, 8, 16, 64])
    magnitude = random.choice([1e-6, 1.0, 1e3, 1e8])
    amps = tuple((random.uniform(-1, 1)) * magnitude for _ in range(n))
    try:
        st = m.FormalQuantumState(amps).normalised()
    except ValueError:
        continue  # zero-norm degenerate case, expected to be rejected
    res = m.run_all_surfaces(st)
    try:
        m.assert_invariant_equivalence(res)
    except AssertionError as e:
        scale_failures.append((n, magnitude, str(e)))

report(
    "4. invariant holds across 200 randomized states (sizes 2-64, magnitudes 1e-6 to 1e8)",
    len(scale_failures) == 0,
    f"{len(scale_failures)}/200 failed" + (f"; first failure: {scale_failures[0]}" if scale_failures else ""),
)

# Degenerate edge case: does zero-norm rejection actually trigger as designed?
zero_rejected = False
try:
    m.FormalQuantumState((0.0, 0.0, 0.0)).normalised()
except ValueError:
    zero_rejected = True
report("4b. zero-norm state is correctly rejected rather than silently producing NaN/inf", zero_rejected)


print("\n--- SUMMARY ---")
for name, passed, detail in results_log:
    print(("PASS" if passed else "FAIL"), "-", name)
n_fail = sum(1 for _, p, _ in results_log if not p)
print(f"\n{len(results_log) - n_fail}/{len(results_log)} stress checks passed.")
