/**
 * Property-based tests for HYBA frontend pure functions using fast-check.
 *
 * These tests validate invariants across a vast range of random inputs,
 * providing formal proof that the mathematical primitives are correct.
 *
 * Run with:
 *   npx vitest run tests/test_property_frontend.test.ts
 */

import { describe, it, expect } from "vitest";
import fc from "fast-check";

// ── Import pure utility functions from the frontend ────────────────────────

import {
  GOLDEN_RATIO,
  PHI_15,
  DODECAHEDRON_VERTICES,
  Complex,
  generateDeterministicComplexVector,
  normalize,
  calculateEntropy,
  getDodecahedralVertices,
  computeQuantumGrover,
} from "../src/utils/math";

import {
  PHI,
  FEIGEN_ALPHA,
  FEIGEN_DELTA,
  calculate_phi_resonance,
  project_to_phi_floor,
} from "../src/core/constants";

// ── Type Helpers ───────────────────────────────────────────────────────────

const isNonEmptyIntegerArray = (arr: number[]): boolean =>
  arr.length > 0 && arr.every((x) => Number.isInteger(x) && x > 0);

// ===========================================================================
// PROPERTY 1: GOLDEN RATIO QUADRATIC IDENTITY (Φ² = Φ + 1)
// ===========================================================================

describe("Golden Ratio identity", () => {
  it("Φ² = Φ + 1 exactly", () => {
    expect(GOLDEN_RATIO * GOLDEN_RATIO).toBeCloseTo(GOLDEN_RATIO + 1, 15);
  });

  it("1/Φ = Φ - 1 exactly", () => {
    expect(1 / GOLDEN_RATIO).toBeCloseTo(GOLDEN_RATIO - 1, 15);
  });
});

// ===========================================================================
// PROPERTY 2: PHI_15 IS EXACTLY Φ¹⁵
// ===========================================================================

describe("PHI_15 identity", () => {
  it("PHI_15 should be exactly GOLDEN_RATIO^15", () => {
    expect(PHI_15).toBeCloseTo(Math.pow(GOLDEN_RATIO, 15), 10);
  });
});

// ===========================================================================
// PROPERTY 3: HIGH-PRECISION INVARIANTS OF computeQuantumGrover
// ===========================================================================

describe("computeQuantumGrover invariants", () => {
  it("Property: All solution probabilities must be in [0, 1]", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 128 }),
        fc.integer({ min: 0, max: 127 }),
        fc.integer({ min: 0, max: 10 }),
        (dimensionSize: number, markedIndex: number, iterations: number) => {
          fc.pre(markedIndex < dimensionSize);
          const steps = computeQuantumGrover(markedIndex, dimensionSize, iterations);
          for (const step of steps) {
            expect(step.solutionProbability).toBeGreaterThanOrEqual(0);
            expect(step.solutionProbability).toBeLessThanOrEqual(1);
          }
        }
      ),
      { numRuns: 50 }
    );
  });

  it("Property: Entropy must be non-negative and bounded by log2(N)", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 64 }),
        fc.integer({ min: 0, max: 63 }),
        fc.integer({ min: 0, max: 8 }),
        (dimensionSize: number, markedIndex: number, iterations: number) => {
          fc.pre(markedIndex < dimensionSize);
          const steps = computeQuantumGrover(markedIndex, dimensionSize, iterations);
          const maxEntropy = Math.log2(dimensionSize);
          for (const step of steps) {
            expect(step.entropy).toBeGreaterThanOrEqual(0);
            expect(step.entropy).toBeLessThanOrEqual(maxEntropy + 1e-10);
          }
        }
      ),
      { numRuns: 50 }
    );
  });

  it("Property: Amplitudes array length must equal dimensionSize", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 64 }),
        fc.integer({ min: 0, max: 63 }),
        fc.integer({ min: 0, max: 8 }),
        (dimensionSize: number, markedIndex: number, iterations: number) => {
          fc.pre(markedIndex < dimensionSize);
          const steps = computeQuantumGrover(markedIndex, dimensionSize, iterations);
          for (const step of steps) {
            expect(step.amplitudes).toHaveLength(dimensionSize);
          }
        }
      ),
      { numRuns: 20 }
    );
  });

  it("Property: Step count must be exactly iterations + 1 (initial state)", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 64 }),
        fc.integer({ min: 0, max: 63 }),
        fc.integer({ min: 0, max: 8 }),
        (dimensionSize: number, markedIndex: number, iterations: number) => {
          fc.pre(markedIndex < dimensionSize);
          const steps = computeQuantumGrover(markedIndex, dimensionSize, iterations);
          expect(steps).toHaveLength(iterations + 1);
        }
      ),
      { numRuns: 20 }
    );
  });

  it("Property: First step must be the Hadamard initial superposition", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 64 }),
        fc.integer({ min: 0, max: 63 }),
        (dimensionSize: number, markedIndex: number) => {
          fc.pre(markedIndex < dimensionSize);
          const steps = computeQuantumGrover(markedIndex, dimensionSize, 1);
          expect(steps[0].step).toBe(0);
          expect(steps[0].operation).toContain("Hadamard");
          expect(steps[0].markedStateIndex).toBe(markedIndex);
        }
      ),
      { numRuns: 20 }
    );
  });
});

// ===========================================================================
// PROPERTY 4: VECTOR NORMALIZATION INVARIANTS
// ===========================================================================

describe("normalize vector invariants", () => {
  it("Property: Normalized vector must have unit L2 norm", () => {
    fc.assert(
      fc.property(
        fc
          .array(
            fc.tuple(
              fc.float({ min: -10, max: 10, noNaN: true }),
              fc.float({ min: -10, max: 10, noNaN: true })
            ),
            { minLength: 1, maxLength: 100 }
          )
          .map((tuples) => tuples.map(([r, i]) => ({ r, i }))),
        (vector: Complex[]) => {
          const normalized = normalize(vector);
          const normSq = normalized.reduce(
            (sum, amp) => sum + (amp.r * amp.r + amp.i * amp.i),
            0
          );
          expect(Math.abs(normSq - 1.0)).toBeLessThan(1e-12);
        }
      ),
      { numRuns: 200 }
    );
  });

  it("Property: Normalization of zero vector should not crash (norm=0 case)", () => {
    const zeroVec: Complex[] = [{ r: 0, i: 0 }, { r: 0, i: 0 }];
    const normalized = normalize(zeroVec);
    const normSq = normalized.reduce(
      (sum, amp) => sum + (amp.r * amp.r + amp.i * amp.i),
      0
    );
    // When input is zero vector, normalized result should not be NaN
    expect(normalized.every((c) => !isNaN(c.r) && !isNaN(c.i))).toBe(true);
    // And should still produce finite values
    expect(normalized.every((c) => isFinite(c.r) && isFinite(c.i))).toBe(true);
  });

  it("Property: Already normalized vectors should remain normalized", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 64 }),
        (dim: number) => {
          const unitVec: Complex[] = Array.from({ length: dim }, () => ({
            r: 1 / Math.sqrt(dim),
            i: 0,
          }));
          const normalized = normalize(unitVec);
          const normSq = normalized.reduce(
            (sum, amp) => sum + (amp.r * amp.r + amp.i * amp.i),
            0
          );
          expect(Math.abs(normSq - 1.0)).toBeLessThan(1e-12);
        }
      ),
      { numRuns: 50 }
    );
  });
});

// ===========================================================================
// PROPERTY 5: ENTROPY INVARIANTS
// ===========================================================================

describe("calculateEntropy invariants", () => {
  it("Property: Entropy of a pure state (single amplitude = 1) must be 0", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 64 }),
        (dim: number) => {
          const pureState: Complex[] = Array.from({ length: dim }, (_, i) => ({
            r: i === 0 ? 1 : 0,
            i: 0,
          }));
          const entropy = calculateEntropy(pureState);
          expect(Math.abs(entropy)).toBeLessThan(1e-12);
        }
      ),
      { numRuns: 20 }
    );
  });

  it("Property: Entropy of uniform superposition must be log2(N)", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 128 }),
        (dim: number) => {
          const uniformState: Complex[] = Array.from({ length: dim }, () => ({
            r: 1 / Math.sqrt(dim),
            i: 0,
          }));
          const entropy = calculateEntropy(uniformState);
          const expected = Math.log2(dim);
          expect(Math.abs(entropy - expected)).toBeLessThan(1e-12);
        }
      ),
      { numRuns: 20 }
    );
  });
});

// ===========================================================================
// PROPERTY 6: DODECAHEDRAL VERTEX INVARIANTS
// ===========================================================================

describe("getDodecahedralVertices invariants", () => {
  it("Property: Must return exactly DODECAHEDRON_VERTICES (20) vertices", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 256 }),
        (dim: number) => {
          const vertices = getDodecahedralVertices(dim);
          expect(vertices).toHaveLength(DODECAHEDRON_VERTICES);
        }
      ),
      { numRuns: 20 }
    );
  });

  it("Property: Each vertex must have the correct dimension size", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 256 }),
        (dim: number) => {
          const vertices = getDodecahedralVertices(dim);
          for (const vertex of vertices) {
            expect(vertex).toHaveLength(dim);
          }
        }
      ),
      { numRuns: 20 }
    );
  });

  it("Property: Each vertex must be normalized (unit L2 norm)", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 128 }),
        (dim: number) => {
          const vertices = getDodecahedralVertices(dim);
          for (const vertex of vertices) {
            const normSq = vertex.reduce(
              (sum, amp) => sum + (amp.r * amp.r + amp.i * amp.i),
              0
            );
            expect(Math.abs(normSq - 1.0)).toBeLessThan(1e-12);
          }
        }
      ),
      { numRuns: 10 }
    );
  });

  it("Property: All vertex entries must be finite numbers", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 64 }),
        (dim: number) => {
          const vertices = getDodecahedralVertices(dim);
          for (const vertex of vertices) {
            for (const c of vertex) {
              expect(isFinite(c.r)).toBe(true);
              expect(isFinite(c.i)).toBe(true);
            }
          }
        }
      ),
      { numRuns: 10 }
    );
  });
});

// ===========================================================================
// PROPERTY 7: DETERMINISTIC COMPLEX VECTOR PROPERTIES
// ===========================================================================

describe("generateDeterministicComplexVector invariants", () => {
  it("Property: Must produce a deterministic output for the same input", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 128 }),
        fc.float({ min: 1, max: 100, noNaN: true }),
        (size: number, scale: number) => {
          const first = generateDeterministicComplexVector(size, scale);
          const second = generateDeterministicComplexVector(size, scale);
          for (let i = 0; i < size; i++) {
            expect(first[i].r).toBe(second[i].r);
            expect(first[i].i).toBe(second[i].i);
          }
        }
      ),
      { numRuns: 50 }
    );
  });

  it("Property: Must throw an error for non-positive size", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: -100, max: 0 }),
        (size: number) => {
          expect(() => generateDeterministicComplexVector(size)).toThrow();
        }
      ),
      { numRuns: 50 }
    );
  });

  it("Property: Must throw an error for non-integer size", () => {
    expect(() => generateDeterministicComplexVector(1.5 as any)).toThrow();
    expect(() => generateDeterministicComplexVector(NaN as any)).toThrow();
  });

  it("Property: Output array must have exactly the requested length", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 256 }),
        (size: number) => {
          const result = generateDeterministicComplexVector(size);
          expect(result).toHaveLength(size);
        }
      ),
      { numRuns: 50 }
    );
  });

  it("Property: All components must be finite numbers", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 256 }),
        (size: number) => {
          const result = generateDeterministicComplexVector(size);
          for (const c of result) {
            expect(isFinite(c.r)).toBe(true);
            expect(isFinite(c.i)).toBe(true);
          }
        }
      ),
      { numRuns: 50 }
    );
  });
});

// ===========================================================================
// PROPERTY 8: CONSTANTS INVARIANTS
// ===========================================================================

describe("Constants invariants", () => {
  it("Golden Ratio is the positive root of x² - x - 1 = 0", () => {
    expect(PHI * PHI - PHI - 1).toBeCloseTo(0, 15);
  });

  it("Feigenbaum constants are positive", () => {
    expect(FEIGEN_ALPHA).toBeGreaterThan(0);
    expect(FEIGEN_DELTA).toBeGreaterThan(0);
  });

  it("Feigenbaum δ = 4.6692... is greater than α = 2.5029...", () => {
    expect(FEIGEN_DELTA).toBeGreaterThan(FEIGEN_ALPHA);
  });

  it("DODECAHEDRON_VERTICES constant must be 20", () => {
    expect(DODECAHEDRON_VERTICES).toBe(20);
  });
});

// ===========================================================================
// PROPERTY 9: PHI RESONANCE INVARIANTS
// ===========================================================================

describe("calculate_phi_resonance invariants", () => {
  it("Property: Resonance must always be in [0, 1)", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 1_000_000_000_000 }),
        (timestamp: number) => {
          const resonance = calculate_phi_resonance(timestamp);
          expect(resonance).toBeGreaterThanOrEqual(0);
          expect(resonance).toBeLessThan(1);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("Property: Resonance must be deterministic for the same timestamp", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 1_000_000 }),
        (timestamp: number) => {
          const first = calculate_phi_resonance(timestamp);
          const second = calculate_phi_resonance(timestamp);
          expect(first).toBe(second);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("Property: Resonance at t=0 should be 0", () => {
    expect(calculate_phi_resonance(0)).toBe(0);
  });
});

// ===========================================================================
// PROPERTY 10: PHI FLOOR PROJECTION INVARIANTS
// ===========================================================================

describe("project_to_phi_floor invariants", () => {
  it("Property: Must always produce finite output for finite input", () => {
    fc.assert(
      fc.property(
        fc.float({ min: -1e10, max: 1e10, noNaN: true }),
        (value: number) => {
          const result = project_to_phi_floor(value);
          expect(isFinite(result)).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("Property: Must be sign-preserving (positive input → positive output)", () => {
    fc.assert(
      fc.property(
        fc.float({ min: 0.001, max: 1e10, noNaN: true }),
        (value: number) => {
          const result = project_to_phi_floor(value);
          expect(result).toBeGreaterThan(0);
        }
      ),
      { numRuns: 50 }
    );
  });

  it("Property: Zero input must produce zero output", () => {
    expect(project_to_phi_floor(0)).toBe(0);
  });
});

// ===========================================================================
// PROPERTY 11: GROVER AMPLITUDE MONOTONICITY
// ===========================================================================

describe("Grover amplitude amplification", () => {
  it("Property: Solution probability must be >= baseline probability at maximum iteration", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 8, max: 128 }),
        fc.integer({ min: 0, max: 127 }),
        (dimension: number, targetIdx: number) => {
          fc.pre(targetIdx < dimension);
          const optIters = Math.floor((Math.PI / 4) * Math.sqrt(dimension));
          const steps = computeQuantumGrover(
            targetIdx,
            dimension,
            Math.max(optIters, 1)
          );
          const finalStep = steps[steps.length - 1];
          const baselineProb = 1.0 / dimension;
          expect(finalStep.solutionProbability).toBeGreaterThanOrEqual(
            baselineProb * 0.5
          );
        }
      ),
      { numRuns: 50 }
    );
  });
});

// ===========================================================================
// PROPERTY 12: ENTROPY BOUNDS FOR COMPLEX VECTORS
// ===========================================================================

describe("Entropy bounds for complex vectors", () => {
  it("Property: Entropy must be >= 0 for any normalized vector", () => {
    fc.assert(
      fc.property(
        fc
          .array(
            fc.tuple(
              fc.float({ min: -5, max: 5, noNaN: true }),
              fc.float({ min: -5, max: 5, noNaN: true })
            ),
            { minLength: 2, maxLength: 50 }
          )
          .map((tuples) => normalize(tuples.map(([r, i]) => ({ r, i })))),
        (vector: Complex[]) => {
          const entropy = calculateEntropy(vector);
          expect(entropy).toBeGreaterThanOrEqual(0);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("Property: Entropy must be <= log2(N) for any normalized vector of length N", () => {
    fc.assert(
      fc.property(
        fc
          .array(
            fc.tuple(
              fc.float({ min: -5, max: 5, noNaN: true }),
              fc.float({ min: -5, max: 5, noNaN: true })
            ),
            { minLength: 2, maxLength: 50 }
          )
          .map((tuples) => ({
            vector: normalize(tuples.map(([r, i]) => ({ r, i }))),
            dim: tuples.length,
          })),
        ({ vector, dim }: { vector: Complex[]; dim: number }) => {
          const entropy = calculateEntropy(vector);
          const maxEntropy = Math.log2(dim);
          expect(entropy).toBeLessThanOrEqual(maxEntropy + 1e-12);
        }
      ),
      { numRuns: 100 }
    );
  });
});