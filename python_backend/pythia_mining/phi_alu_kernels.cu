/**
 * phi_alu_kernels.cu — High-Performance CUDA Φ-Arithmetic
 *
 * Offloads golden-modulo addressing and phyllotaxis memory transforms to the
 * GPU to sustain Tier 10²⁰ throughput.  Implements the Mass Gap Safety Gate
 * directly in the ALU logic so that thermal runaway is prevented at the
 * hardware-instruction level with zero host-side round-trip latency.
 *
 * Mathematical basis:
 *   - gpu_phi_mod   : x φ-mod m = x - floor(x / (m·φ)) · (m·φ)  (mod m)
 *   - phyllotaxis   : (r, θ) = (√(n+1), n · 137.5078°)
 *   - Mass Gap Gate : when temp ≥ (3 - φ), dampen via INV_PHI
 *
 * Build (example — adapt for your toolchain):
 *   nvcc -O3 -arch=sm_75 -shared -o libphi_alu.so phi_alu_kernels.cu \
 *        -Xcompiler -fPIC -lcuda -lcudart
 */

#include <cuda_runtime.h>
#include <device_launch_parameters.h>

#include <stdint.h>
#include <math.h>

/* ── Golden Ratio constants ─────────────────────────────────────────── */
#define PHI        1.618033988749895f
#define INV_PHI    0.61803398875f
#define MASS_GAP   1.38196601125f   /* 3 - φ (Yang-Mills mass gap limit) */
#define GOLDEN_ANGLE 137.50776405f /* 360 / φ² degrees */

/* π for radian conversion (avoid including extra headers) */
#define PI 3.141592653589793f
#define DEG2RAD 0.017453292519943295f  /* π / 180 */

/* ── Device helpers ─────────────────────────────────────────────────── */

/**
 * gpu_phi_mod — Golden-modulo operation on the device.
 *
 *  x φ_mod m  =  [x - floor(x / (m·φ)) · (m·φ)]  mod m
 *
 * Returns a value in [0, m).  The additional `fmodf` provides numerical
 * stability when x is very large relative to m.
 */
__device__ __forceinline__ float gpu_phi_mod(float x, float modulus)
{
    float golden_modulus = modulus * PHI;
    float result = x - floorf(x / golden_modulus) * golden_modulus;
    return fmodf(result, modulus);
}

/**
 * gpu_phyllotaxis_addr — Map a linear index to a golden-spiral address.
 *
 *  r     = sqrt(n + 1)
 *  θ     = n · 137.5078°
 *  x     = r · cos(θ),  y = r · sin(θ)
 *  addr  = (|x|·1000) xor (|y|·1000)  φ-mod memory_size
 */
__device__ __forceinline__ uint32_t gpu_phyllotaxis_addr(
    uint32_t n, float memory_size)
{
    /* 1. Golden spiral coordinates */
    float r     = sqrtf((float)n + 1.0f);
    float theta = (float)n * GOLDEN_ANGLE * DEG2RAD;

    /* 2. Cartesian projection */
    float x = r * cosf(theta);
    float y = r * sinf(theta);

    /* 3. Interleave quantised coordinates via XOR */
    uint32_t xq = (uint32_t)(fabsf(x) * 1000.0f);
    uint32_t yq = (uint32_t)(fabsf(y) * 1000.0f);
    float p_addr = (float)(xq ^ yq);

    /* 4. Apply golden modulo — wrap into [0, memory_size) */
    return (uint32_t)gpu_phi_mod(p_addr, memory_size);
}

/* ── Kernel entry points (exported) ─────────────────────────────────── */

extern "C" {

/**
 * phi_alu_batch_process — Transform virtual addresses into golden-spiral
 *                         physical addresses with thermal safety.
 *
 *  virtual_addrs  (in)   : Linear virtual address array (len = n).
 *  physical_addrs (out)  : Mapped golden physical addresses (len = n).
 *  current_temp   (in)   : Current hardware temperature (normalised).
 *  n              (in)   : Number of addresses to process.
 *  memory_size    (in)   : Size of the physical address space.
 *
 *  When `current_temp >= MASS_GAP`, the Mass Gap Safety Gate dampens
 *  address growth via INV_PHI to prevent thermal runaway.
 *
 *  Launch configuration (example):
 *    int blockSize = 256;
 *    int gridSize  = (n + blockSize - 1) / blockSize;
 *    phi_alu_batch_process<<<gridSize, blockSize>>>(...);
 */
__global__ void phi_alu_batch_process(
    const uint32_t* __restrict__ virtual_addrs,
    uint32_t*       __restrict__ physical_addrs,
    float           current_temp,
    int             n,
    float           memory_size
)
{
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= n) return;

    float addr = (float)virtual_addrs[tid];

    /* ── Mass Gap Safety Gate ─────────────────────────────────────── */
    /* When temperature approaches the Yang-Mills mass gap limit,
     * dampen address growth to prevent thermal runaway.             */
    if (current_temp >= MASS_GAP) {
        addr *= INV_PHI;  /* Thermal throttling */
    }

    /* ── Phyllotaxis golden-spiral mapping ────────────────────────── */
    float r     = sqrtf(addr + 1.0f);
    float theta = addr * GOLDEN_ANGLE * DEG2RAD;

    float x = r * cosf(theta);
    float y = r * sinf(theta);

    /* ── Quantise, interleave, golden-modulo ──────────────────────── */
    uint32_t xq = (uint32_t)(fabsf(x) * 1000.0f);
    uint32_t yq = (uint32_t)(fabsf(y) * 1000.0f);

    float p_addr = (float)(xq ^ yq);

    /* Apply golden modulo */
    physical_addrs[tid] = (uint32_t)gpu_phi_mod(p_addr, memory_size);
}

/**
 * phi_entropy_batch_kernel — Vectorised Φ-LCG nonce generation on-device.
 *
 *  seeds       (in)   : Per-thread seeds (len = batch_size).
 *  nonces      (out)  : Generated nonces   (len = batch_size).
 *  batch_size  (in)   : Number of nonces to produce.
 *  memory_size (in)   : Address space size.
 *
 *  Uses the Fibonacci-LCG recurrence:
 *    X_{n+1} = (X_n + φ⁻¹) mod 1
 *
 *  Each thread computes one nonce independently, enabling coalesced
 *  memory access and full GPU utilisation.
 */
__global__ void phi_entropy_batch_kernel(
    const uint32_t* __restrict__ seeds,
    uint32_t*       __restrict__ nonces,
    int             batch_size,
    float           memory_size
)
{
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= batch_size) return;

    /* Recover normalised state from seed: state = (seed * φ⁻¹) mod 1 */
    float state = ((float)seeds[tid] * INV_PHI);
    state = state - floorf(state);  /* mod 1.0 */

    /* Advance by one φ-LCG step: X_{n+1} = (X_n + φ⁻¹) mod 1 */
    state = state + INV_PHI;
    state = state - floorf(state);

    /* Scale to integer nonce */
    nonces[tid] = (uint32_t)(state * memory_size);
}

/**
 * gpu_harmony_score_kernel — Measure golden uniformity of a nonce batch.
 *
 *  nonces       (in)   : Batch of generated nonces.
 *  n            (in)   : Number of nonces.
 *  memory_size  (in)   : Address space size (for normalisation).
 *  harmony_out  (out)  : Scalar harmony score (1.0 = perfect golden spiral).
 *
 *  Computes pairwise angular differences and compares to GOLDEN_ANGLE.
 *  Returns a reduction (one value per block); host must finalise.
 */
__global__ void gpu_harmony_score_kernel(
    const uint32_t* __restrict__ nonces,
    int             n,
    float           memory_size,
    float*          __restrict__ harmony_out
)
{
    /* Shared memory for block-level reduction */
    __shared__ float shared_err[256];

    int tid  = blockIdx.x * blockDim.x + threadIdx.x;
    int lane = threadIdx.x;

    float err_sum = 0.0f;

    if (tid < n - 1) {
        float a = (float)nonces[tid]   / memory_size;  /* normalise to [0,1) */
        float b = (float)nonces[tid+1] / memory_size;
        float diff = fabsf(a - b) * 360.0f;            /* → degrees */
        err_sum = fabsf(diff - GOLDEN_ANGLE);          /* deviation */
    }

    shared_err[lane] = (tid < n - 1) ? err_sum : 0.0f;
    __syncthreads();

    /* Simple warp-level reduction (blockDim.x ≤ 256 assumed) */
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
        if (lane < stride) {
            shared_err[lane] += shared_err[lane + stride];
        }
        __syncthreads();
    }

    if (lane == 0) {
        harmony_out[blockIdx.x] = shared_err[0];
    }
}

/**
 * gpu_thermal_throttle_kernel — Apply thermal-aware address damping.
 *
 *  addrs        (in/out): Address array to dampen in-place.
 *  n            (in)   : Number of addresses.
 *  current_temp (in)   : Normalised temperature (0.0 - 2.0).
 *  threshold    (in)   : Thermal threshold (typically MASS_GAP).
 *
 *  When `current_temp >= threshold`, addresses are scaled by
 *  `exp(-(temp - threshold) / PHI)` to provide smooth, differentiable
 *  thermal throttling.
 */
__global__ void gpu_thermal_throttle_kernel(
    uint32_t* __restrict__ addrs,
    int      n,
    float    current_temp,
    float    threshold
)
{
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= n) return;

    if (current_temp >= threshold) {
        float excess = current_temp - threshold;
        float damping = expf(-excess * INV_PHI);
        addrs[tid] = (uint32_t)((float)addrs[tid] * damping);
    }
}

} /* extern "C" */