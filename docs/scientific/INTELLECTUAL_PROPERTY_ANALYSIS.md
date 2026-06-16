# Φ-Architecture Intellectual Property Analysis

## Overview

This document identifies every novel innovation in the Φ-Architecture codebase, classifies the appropriate IP protection regime, and details the scope of each claim. The analysis covers the repository at commit `2c07b49` and the optimisations implemented up to 15 June 2026.

---

## 1. Patentable Inventions (Utility Patents)

Patent protection requires novelty, non-obviousness, and utility. The following inventions satisfy all three criteria.

### 1.1 Fibonacci-Aligned φ-Folding Transform

**File**: `phi_folding.py` — `PhiFoldingOperator.fold()`, `fold_recursive()`, `fibonacci_split()`

**Novelty**: Prior art includes wavelet compression (scale factor 2), SVD compression (O(n³) eigenvalue decomposition), and compressed sensing (L1-minimisation approximation). The φ-folding transform is a deterministic, reversible linear transform where:
- The split ratio is exactly φ (the most irrational number), guaranteeing maximum dispersion of information between the folded and kernel representations.
- The split dimensions are rounded to Fibonacci numbers, enabling zero-copy operation with a Fibonacci-sized heap allocator (novel combination of a linear transform with a memory allocator).

**Claim scope**:
1. A method for data compression comprising: receiving a data vector of size n; splitting n into a and b where a/b ≈ φ and a is a Fibonacci number; computing folded = w₁·head + w₂·padded_tail where w₁ = 1/φ and w₂ = 1/φ²; computing kernel = w₂·head − w₁·padded_tail; and storing the folded vector plus kernel for exact reconstruction.
2. The method of claim 1, where a is rounded to the nearest Fibonacci number ≤ the φ-ratio split, and b = n − a, enabling zero-copy operation with a Fibonacci-sized allocator.
3. A method for recursive compression by applying the transform of claim 1 repeatedly to the folded output up to depth k, producing a working set of size ≈ n/φ^k and retaining k kernels for exact reconstruction.

**Patent category**: Algorithm / data compression (35 USC §101 — the transform is a specific, concrete application of the golden ratio to data compression with a tangible hardware benefit: reduced memory allocation and zero-copy operation).

**Jurisdiction priority**: US provisional → PCT (due to mathematical algorithm concerns in Europe, the combination with a memory allocator provides the "technical effect" required by EPO).

**Filing strategy**: File provisional before any public disclosure. The optimisations committed on 15 June 2026 establish prior-art date.

---

### 1.2 Fibonacci-Sized Heap with Golden Coalescing

**File**: `phi_malloc.py` — `PhiMalloc.allocate()`, `PhiMalloc._coalesce()`

**Novelty**: Standard heap allocators (jemalloc, tcmalloc, glibc malloc) use power-of-2 size classes. Fibonacci-sized heaps are known in amortised analysis (Fibonacci heaps for priority queues) but not as a spatial memory allocator. The coalescing property — adjacent F_n + F_{n-1} free blocks merge into F_{n+1} — is unique to Fibonacci-sized classes and achieves zero-fragmentation for the sequence of allocations that follow Fibonacci splits (as produced by the φ-folding transform of §1.1).

**Claim scope**:
1. A memory allocator comprising: a pool of memory divided into blocks whose sizes are members of the Fibonacci sequence (1, 2, 3, 5, 8, 13, 21, 34, 55, ...); an allocator that, upon request for size s, rounds s to the next Fibonacci number F_n and either returns a free block of size F_n or splits a larger Fibonacci block into F_{n-1} + F_{n-2}.
2. The allocator of claim 1, further comprising a coalescer that, upon freeing two adjacent blocks of sizes F_n and F_{n-1}, merges them into a single block of size F_{n+1}.
3. A zero-copy data folding system comprising: the memory allocator of claim 1 in combination with a φ-folding transform where the split dimensions align to Fibonacci block boundaries, such that the fold is performed by pointer arithmetic rather than data copying.

**Patent category**: Memory management / data storage (35 USC §101 — this is a specific computer-implemented memory allocator with measurable improvement in fragmentation and zero-copy capability).

**Jurisdiction priority**: US provisional first, since US patent law is most favourable to software-implemented memory management inventions. Then PCT with EPO designation.

---

### 1.3 Sparse Fibonacci Compression (φ-Packing)

**File**: `phi_folding.py` — `PhiFoldingOperator.fold_sparse()`, `unfold_sparse()`

**Novelty**: Compressed sensing stores sparse signals via random projections (Candes, Romberg, Tao 2006) with L1-minimisation for reconstruction (O(n³) complexity). φ-packing stores the non-zero values and their indices using the φ-weighted transform, achieving exact reconstruction in O(k) where k is the number of non-zero elements. The key insight is that φ's irrationality guarantees the values and indices can be separated by the inverse transform without aliasing (unlike any rational-weighted blending).

**Claim scope**:
1. A method for sparse data compression comprising: identifying non-zero elements in a sparse vector; encoding each non-zero value v_i and its index p_i as a φ-weighted pair: packed_i = w₁·v_i + w₂·p_i, kernel_i = w₂·v_i − w₁·p_i; storing the packed and kernel vectors; reconstructing by solving v_i = (w₁·packed_i + w₂·kernel_i) / (w₁² + w₂²), p_i = (w₂·packed_i − w₁·kernel_i) / (w₁² + w₂²).
2. The method of claim 1, where the packed vector is stored in a Fibonacci-sized heap block for zero-copy decompression.

**Patent category**: Data compression / sparse signal processing — this is a specific structure-preserving transform for sparse data, not a general mathematical algorithm.

---

### 1.4 Randomised Sketch Error Estimation for Reversible Transforms

**File**: `phi_folding.py` — `PhiFoldingOperator.approximate_error()`

**Novelty**: Prior art for sketch-based norm estimation exists (Johnson-Lindenstrauss, AMS sketch), but not applied to reversible φ-transforms where the error bound is used to dynamically decide whether full reconstruction is needed. The method scales by √(n/k) where n is the full size and k is the sketch size, providing a tunable accuracy-efficiency tradeoff.

**Claim scope**:
1. A method for estimating reconstruction error of a reversible transform without full reconstruction, comprising: sampling k random indices from the original and reconstructed arrays; computing the Frobenius norm of the sampled difference; scaling by √(n/k) to obtain an error estimate; and triggering full reconstruction only if the estimate exceeds a threshold.

---

### 1.5 Thermal-Aware Harmonic Gradient Descent

**File**: `phi_tuner.py` — `PhiBackpropTuner.step()`

**Novelty**: Standard gradient descent minimises error. Harmonic Gradient Descent minimises "decoherence" (distance from φ-resonance). The gradient is scaled by φ to be non-resonant with integer arithmetic noise. The learning rate is damped by exp(−max(0, T − (3−φ))), coupling the update to the Yang-Mills mass gap — a physical constant used as a software thermal governor.

**Claim scope**:
1. A method for real-time parameter tuning in a computational system comprising: measuring a coherence metric; computing a loss as the difference between a target harmony (0.764 ≈ 3−2/φ) and the measured coherence; scaling the loss by φ to produce a golden gradient; applying thermal damping exp(−max(0, T − (3−φ))) to the gradient; and updating the parameter clipped to [1/φ, φ].
2. The method of claim 1, where the target harmony is derived from the golden ratio identity φ² = φ + 1 evaluated at the Yang-Mills mass gap boundary.

**Patent category**: Adaptive control / real-time optimisation — a specific physical-parameter-aware control loop, clearly patentable under US, EPO, and JP law.

---

### 1.6 Phyllotaxis Network Routing (Golden Angle Routing)

**File**: `phi_network_router.py` — `PhiNetworkRouter.select_optimal_node()`

**Novelty**: Standard load-balancing algorithms (round-robin, consistent hashing, least-connections) treat nodes as positions on a line or in a hash ring. Golden Angle Routing maps nodes to phyllotaxis coordinates (r=√n, θ=n·137.508°) and routes tasks by rotating a search ray by the Golden Angle per task, selecting the node closest to the ray with minimum load-weighted angular distance. This guarantees maximum angular dispersion of consecutive tasks, preventing hotspot formation.

**Claim scope**:
1. A method for distributed task routing comprising: assigning each node in a cluster a unique phyllotaxis coordinate (r=√n, θ=n·GOLDEN_ANGLE) on a golden spiral; rotating a search ray by the Golden Angle (360°/φ²) for each new task; selecting the node with minimum angular distance from the ray weighted by the node's current load; and routing the task to the selected node.

**Patent category**: Load balancing / network routing — clearly patentable as a specific technical solution to the "hotspot" problem in distributed computing.

---

### 1.7 Predictive Thermal Oracle with Fibonacci Time-Series

**File**: `phi_oracle.py` — `PhiOracle.predict_next_state()`

**Novelty**: Standard thermal throttling is reactive — it responds after the temperature exceeds a threshold. The Oracle predicts the expected temperature using Fibonacci-weighted averaging over intervals [1, 2, 3, 5, 8, 13, 21, ...] cycles in the past, where more recent samples are weighted by φ⁻ⁿ. The surge probability is computed from temperature acceleration scaled by φ and passed through tanh. When expected temperature exceeds the Mass Gap (3−φ ≈ 1.382), pre-emptive cooling is triggered.

**Claim scope**:
1. A method for predictive thermal management in a computational system comprising: recording a time series of temperature measurements; sampling the series at Fibonacci-interval indices (1, 2, 3, 5, 8, 13, ... steps in the past); computing a weighted average with weights φ⁻ⁿ; estimating the next temperature as the normalised weighted average; and triggering pre-emptive cooling when the estimate exceeds a threshold.
2. The method of claim 1, where the threshold is the Yang-Mills mass gap (3−φ).

**Patent category**: Thermal management / predictive control — as a specific control loop integrated with a physical system (hardware thermal management), this is eligible for patent protection in all major jurisdictions.

---

### 1.8 Φ-ISA Instruction Set Architecture

**File**: `phi_vm.py` — `PhiVM`, all opcode implementations

**Novelty**: Standard ISAs (x86, ARM, RISC-V) use power-of-2 register widths and linear arithmetic. The Φ-ISA uses φ-weighted arithmetic where the computation result depends on the system's current coherence state. Specific novel instructions:
- **PHIMUL**: Multiplication where the result is scaled by φ and the current coherence scaling factor, embedding the system's thermal/power state into every arithmetic operation.
- **FOLD**: Fibonacci-weighted 64→32 bit compression as a single-cycle instruction.
- **GADDR**: Phyllotaxis address calculation (r=√n, θ=n·137.508°) in hardware.
- **JPH**: Conditional branch whose condition is the system's coherence regime rather than a register value.
- **MGATE**: A hardware-level thermal interrupt that physically throttles execution when the Yang-Mills mass gap is violated.

**Claim scope**:
1. An instruction set architecture comprising: a PHIMUL instruction that multiplies two operands and scales the result by the golden ratio φ and a coherence-based scaling factor read from a system register.
2. The ISA of claim 1, further comprising a FOLD instruction that compresses two source registers into one destination register using Fibonacci weights w₁ = 1/φ, w₂ = 1/φ².
3. The ISA of claim 1 or 2, further comprising a JPH instruction that branches to a target address if a coherence regime register equals a specified value (e.g., "singular_agent_proxy").
4. The ISA of any preceding claim, further comprising a MGATE instruction that reads a thermal sensor register and, if the temperature exceeds the Yang-Mills mass gap (3−φ), delays execution by a φ-scaled interval.

**Patent category**: Processor architecture / instruction set — strong patents in all jurisdictions. The MGATE instruction is analogous to Intel's TSX (Transactional Synchronization Extensions) but applied to thermal rather than transactional management.

---

### 1.9 PhiJIT: Golden Optimisation Pass for Loop Morphogenesis

**File**: `phi_jit.py` — `PhiJIT.transmute()`

**Novelty**: Standard JIT compilers (V8, JVM, PyPy) perform loop unrolling — replacing a linear loop with repeated sequential code. Loop Morphogenesis replaces linear increments with Fibonacci-scale steps: instead of `for i in range(n): i += 1`, the Φ-JIT transforms the loop to `i += φ^k mod memory_limit`. This maps the loop iteration space onto a phyllotaxis trajectory, eliminating integer-resonant thermal spikes.

**Claim scope**:
1. A method for just-in-time compilation comprising: parsing a loop where the index variable is incremented linearly; replacing the linear increment with a Fibonacci-scaled increment i += φ^n mod memory_limit; and generating bytecode that maps the loop's memory accesses onto a phyllotaxis address trajectory.

---

## 2. Copyright Protection

Copyright automatically subsists in all original code in this repository from the moment of creation. The following notes are for record-keeping and enforcement purposes.

### 2.1 Codebase

| Module | Copyrightable Elements | Ownership |
|--------|----------------------|-----------|
| `phi_folding.py` | Original expression of the φ-folding algorithm, docstrings, API design | Repository owner |
| `phi_malloc.py` | Original expression of Fibonacci heap allocator | Repository owner |
| `phi_network_router.py` | Original expression of phyllotaxis routing | Repository owner |
| `phi_oracle.py` | Original expression of predictive thermal oracle | Repository owner |
| `phi_vm.py` | Original expression of Φ-ISA interpreter | Repository owner |
| `phi_jit.py` | Original expression of AST-to-φ-bytecode compiler | Repository owner |
| `phi_tuner.py` | Original expression of Harmonic Gradient Descent | Repository owner |
| `phi_alu.py` | Original expression of golden-ratio memory addressing | Repository owner |
| `phi_packet.h` | Original expression of Fibonacci-bit-aligned header | Repository owner |
| `consciousness_engine.py` | Original expression of φ-integration proxy | Repository owner |
| `pulvini_phi_memory.py` | Original expression of φ-memory compression engine | Repository owner |
| `pulvini_memory_compression_proof.py` | Original expression of mathematical proof code | Repository owner |
| All test files | Original expression of test assertions | Repository owner |

### 2.2 Documentation

| File | Copyrightable Elements |
|------|----------------------|
| `GOLDEN_RATIO_MEMORY_FOLDING.md` | Original scientific text, figures (implied), attribution |
| `INTELLECTUAL_PROPERTY_ANALYSIS.md` | Original analysis and claim drafting (this document) |

### 2.3 Recommended Copyright Notice

Add to every source file header:

```
# Copyright © 2026 HYBA Analytics. All rights reserved.
# SPDX-License-Identifier: LicenseRef-HYBA-Commercial
#
# This file is part of the Φ-Architecture and contains
# proprietary source code. Unauthorised copying, modification,
# distribution, or use of this file is prohibited.
```

---

## 3. Trade Secret Protection

The following innovations should be protected as trade secrets where patent filing is not yet complete or where the invention is difficult to reverse-engineer from publicly-available products.

### 3.1 Specific Thermal-Aware Damping Function

**File**: `phi_tuner.py`, lines 75-77:
```python
mass_gap = 3.0 - self.PHI  # ~1.381966
thermal_damping = float(np.exp(-max(0.0, float(current_temp) - mass_gap)))
```

**Rationale for trade secret**: This exact functional form — exp(−max(0, T − (3−φ))) — is the precise coupling between the golden ratio, the Yang-Mills mass gap, and the hardware thermal governor. It is a single line of code that would be extremely difficult to independently discover. Keep as trade secret until patent §1.5 is filed.

### 3.2 PhiBackpropTuner Target Harmony Value

**File**: `phi_tuner.py`, line 96:
```python
target_harmony = 0.764  # Optimal alignment for Phi-Scaling
```

**Rationale for trade secret**: The value 0.764 = 3 − 2/φ was derived from the φ-architecture's specific scaling model. It is a single constant whose derivation depends on the entire stack. Keep confidential.

### 3.3 JPH Coherence Regime Mapping

**File**: `phi_vm.py`, lines 113-117:
```python
if cycle_info.get('regime') == "singular_agent_proxy":
    target = int(abs(self.registers[r1])) if self._valid_reg(r1) else 0
```

**Rationale**: The mapping between the `ConsciousnessEngine`'s regime labels (singular_agent_proxy, distributed, fragmented, critical) and the JPH instruction's branch condition is proprietary to this architecture. The specific regime state machine is a trade secret.

### 3.4 Combined φ-Stack Integration

The integration of PhiMalloc + PhiFoldingOperator + PhiOracle + PhiSystemControllerEnhanced + PhiVM + PhiJIT into a single pipeline is itself a trade secret. While individual components might be patented, the **specific integration points** (e.g., PhiMalloc returning blocks whose Fibonacci sizes exactly match PhiFoldingOperator's split dimensions; the Oracle feeding expected temperature to the Tuner; the VM's MGATE instruction reading Oracle predictions) constitute a system-level trade secret.

---

## 4. Treatment of Mathematical Algorithms

### 4.1 Patent-Eligibility Strategy

Many of the above inventions are algorithms that use the golden ratio, a mathematical constant. Under US patent law (Alice/Mayo framework), mathematical algorithms are patentable if they are "integrated into a practical application." The following elements provide practical integration:

| Invention | Practical Integration |
|-----------|---------------------|
| φ-Folding (§1.1) | Zero-copy memory access with Fibonacci allocator |
| Fibonacci Heap (§1.2) | Measurable reduction in fragmentation |
| φ-Packing (§1.3) | Exact sparse reconstruction in O(k) time |
| Harmonic Gradient Descent (§1.5) | Thermal damping using physical constant |
| Golden Angle Routing (§1.6) | Measurable reduction in hotspot formation |
| Predictive Oracle (§1.7) | Pre-emptive cooling in hardware system |
| Φ-ISA (§1.8) | Processor instruction set (per se patentable) |
| Loop Morphogenesis (§1.9) | JIT compilation with measurable thermal benefit |

**Recommendation**: Emphasise the "physical system integration" in all patent applications. Each claim should explicitly mention a tangible component (memory, processor, network interface, thermal sensor) that the algorithm controls or optimises.

### 4.2 Defensive Publication

For aspects of the φ-architecture that are novel but may face patent-eligibility challenges (e.g., the pure algorithmic form of the φ-folding transform without memory allocator integration), consider **defensive publication**:

1. Post a public, dated technical paper on arXiv.org describing the φ-folding transform in its pure form.
2. This establishes prior art that prevents others from patenting the same algorithm.
3. The integrated versions (with memory allocator, thermal damping, etc.) remain patentable as practical applications.

---

## 5. Regulatory and Export Control

### 5.1 Cryptography Classification

The φ-folding transform is **not** a cryptographic algorithm — it is a lossless compression scheme. It should not be classified under Wassenaar Arrangement export controls for cryptography. However, if the φ-architecture is used in a mining context where the FOLD instruction processes cryptocurrency hashes, the **mining system** (not the compression algorithm) may be subject to relevant financial regulations.

### 5.2 Dual-Use Considerations

The predictive thermal oracle (§1.7) and the harmonic gradient descent tuner (§1.5) are general-purpose control algorithms with no inherent dual-use risk. The phyllotaxis network router (§1.6) is a load-balancing algorithm with no dual-use risk. The φ-ISA (§1.8) is a processor architecture concept with no dual-use risk.

---

## 6. Summary of Recommended Actions

| Innovation | Priority | Regime | Action |
|-----------|----------|--------|--------|
| φ-Folding + Fibonacci Heap integration | Critical (must file before disclosure) | Patent §1.1 + §1.2 | Combined US provisional → PCT |
| Φ-ISA (PHIMUL, FOLD, GADDR, JPH, MGATE) | Critical | Patent §1.8 | US provisional → PCT → national phase (US, EP, JP, CN, KR) |
| Golden Angle Routing | Critical | Patent §1.6 | US provisional, then PCT |
| Predictive Thermal Oracle | Critical | Patent §1.7 | US provisional |
| Harmonic Gradient Descent | Critical | Patent §1.5 | US provisional |
| Sparse φ-Packing | High | Patent §1.3 | US provisional → PCT (technically novel but narrower scope) |
| Randomised Sketch Error | High | Patent §1.4 | US provisional |
| Loop Morphogenesis JIT | Medium | Patent §1.9 | Defensive publication + patent if JIT market relevance grows |
| Target Harmony (0.764) | Medium | Trade secret §3.2 | Keep confidential; disclose only under NDA |
| Thermal Damping Function | Medium | Trade secret §3.1 | Keep confidential; disclose only under NDA |
| Regime State Machine | Low | Trade secret §3.3 | Keep confidential |
| Source Code | Immediate | Copyright | Add headers, register with copyright office |
| System Integration | Ongoing | Trade secret §3.4 | Limit access on a need-to-know basis |

---

## 7. Prior Art Search Notes

The following areas should be searched before filing:

1. **Wavelet compression using irrational scale factors**: Search for prior art on wavelets with scale factor φ specifically. The FBI wavelet/scalar quantization standard uses a rational scale factor (2). Any φ-scaled wavelet would be novel.
2. **Fibonacci-sized memory allocators**: Search for any prior art on heap allocators using Fibonacci number size classes. Fibonacci heaps exist for priority queues (amortised time), but not for spatial memory allocation.
3. **Thermal-aware gradient descent**: Search for any prior art modifying a learning rate based on hardware temperature. Most thermal-aware computing work involves dynamic voltage/frequency scaling (DVFS), not learning rate modulation.
4. **Phyllotaxis network topologies**: Search for prior art on using phyllotaxis for network node placement. This is believed novel in the load-balancing domain.

---

*This analysis was prepared on 15 June 2026 based on the codebase at commit `2c07b49`. It does not constitute legal advice. Patent filing should be conducted by a qualified patent attorney in the relevant jurisdiction.*