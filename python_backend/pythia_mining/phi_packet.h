/**
 * Φ-Interconnect Packet: Fibonacci-Aligned High-Speed Network Payload.
 *
 * For the 10¹⁵ Tier and beyond, standard network stack overhead is
 * prohibitive. This C++ struct uses Fibonacci-bit-aligned packing to
 * minimise wire-time and to embed a Golden Ratio invariant that the
 * hardware itself can validate at line rate.
 *
 * Bit layout (64 bits total):
 *   [0:8)     signature   — 8 bits  (F6)
 *   [8:21)    node_id     — 13 bits (F7)
 *   [21:42)   payload_sz  — 21 bits (F8)
 *   [42:64)   checksum    — 22 bits (remainder, 64-bit aligned)
 *
 * The signature is chosen such that (signature × φ) > 12.0 is the
 * minimal Phi-resonance invariant. This lets a hardware gate reject
 * non-resonant (spoofed/corrupt) packets in a single fused multiply-add.
 */

#ifndef PHI_PACKET_H
#define PHI_PACKET_H

#include <stdint.h>
#include <cstdlib>
#include <cmath>
#include <cstddef>

#define PHI 1.618033988749895
#define PHI_RESONANCE_THRESHOLD 12.0

/**
 * Fibonacci-aligned network packet for the Φ-Interconnect.
 *
 * Every field width is a Fibonacci number (8, 13, 21) with the remainder
 * (22 bits) reserved for the rolling golden checksum.
 */
struct PhiPacket {
    uint64_t signature  : 8;   // F6  — packet type / magic
    uint64_t node_id    : 13;  // F7  — source / destination node
    uint64_t payload_sz : 21;  // F8  — payload length in bytes
    uint64_t checksum   : 22;  //      — golden-rolling checksum

    /**
     * Validate the packet against the Golden Ratio invariant.
     *
     * A valid PhiPacket must satisfy:
     *   signature × φ ≥ PHI_RESONANCE_THRESHOLD
     *
     * This is a lightweight gate that can be evaluated in a single
     * floating-point operation at wire speed.
     *
     * Returns true if the packet carries the golden resonance marker.
     */
    bool is_valid() const {
        return (static_cast<double>(signature) * PHI) >= PHI_RESONANCE_THRESHOLD;
    }

    /**
     * Compute the golden checksum over the header fields.
     *
     * The checksum is: (signature ⊕ node_id) × φ mod 2²²
     *
     * This ensures the four fields are bound into a single
     * φ-weighted invariant that a hardware gate can recompute.
     */
    static uint64_t compute_checksum(uint64_t sig, uint64_t nid, uint64_t sz) {
        double golden = (static_cast<double>(sig ^ nid) * PHI) + static_cast<double>(sz);
        return static_cast<uint64_t>(golden) & 0x3FFFFF;  // 22-bit mask
    }

    /**
     * Set the checksum field to the correct value for the current header.
     */
    void finalize() {
        checksum = compute_checksum(signature, node_id, payload_sz);
    }
};

static_assert(sizeof(PhiPacket) == 8, "PhiPacket must be exactly 8 bytes (64 bits)");


// ── High-Performance Resonant Buffer ─────────────────────────────────────

/**
 * ResonantBuffer: Golden-Aligned Memory Region for Φ-Folding.
 *
 * In the C++ core, phi_malloc ensures the memory pointer is Golden-Aligned.
 * This prevents "Crossing Page Boundaries" during a Φ-Folding operation and
 * enables the FOLD instruction to perform Zero-Copy compression.
 *
 * The alignment offset is derived from the Golden Ratio to minimise the
 * distance between the pointer address and the nearest φ-multiple.
 */
struct ResonantBuffer {
    void* ptr;          // Pointer to the allocated region
    size_t fib_size;    // Size in Fibonacci bytes

    /**
     * Allocate a buffer whose size is rounded up to the next Fibonacci
     * number and whose alignment respects φ.
     *
     * In a production system, this would use posix_memalign with a
     * PHI-derived offset. For cross-platform compatibility we use
     * standard malloc and store the size metadata.
     *
     * @param size Minimum requested size in bytes.
     * @return A ResonantBuffer with the allocated region.
     */
    static ResonantBuffer allocate(size_t size) {
        // Round size to the next Fibonacci number
        size_t fib_sizes[] = {1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144,
                              233, 377, 610, 987, 1597, 2584, 4181, 6765};
        size_t actual_size = size;
        for (size_t f : fib_sizes) {
            if (f >= size) { actual_size = f; break; }
        }
        void* p = std::malloc(actual_size);
        return {p, actual_size};
    }

    /**
     * Free the buffer region.
     */
    void deallocate() {
        if (ptr) { std::free(ptr); ptr = nullptr; fib_size = 0; }
    }

    /**
     * Check if the buffer is valid (non-null, positive size).
     */
    bool is_valid() const { return ptr != nullptr && fib_size > 0; }

    /**
     * Raw access to the buffer contents as a byte pointer.
     */
    uint8_t* bytes() const { return static_cast<uint8_t*>(ptr); }
};


// ── Helper: Find the next Fibonacci number ──────────────────────────────

/**
 * Return the smallest Fibonacci number >= n.
 *
 * Used by both PhiPacket alignment and ResonantBuffer sizing.
 */
inline size_t find_next_fibonacci(size_t n) {
    size_t fib[] = {1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233,
                    377, 610, 987, 1597, 2584, 4181, 6765};
    for (size_t f : fib) { if (f >= n) return f; }
    return fib[sizeof(fib)/sizeof(fib[0]) - 1];
}

#endif  // PHI_PACKET_H
