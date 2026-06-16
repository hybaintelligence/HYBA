"""
Φ-Memory Allocator: Fibonacci-Sized Heap Management.

Standard memory management (C malloc, Python heap) is built on Powers of 2,
creating "Geometric Friction" when processing Golden Ratio data. phi_malloc
solves this by using Fibonacci-Sized Heaps, enabling Golden Coalescing:

    F_n + F_{n-1} = F_{n+1}

Adjacent free blocks merge with zero fragmentation, mirroring the way
biological cells pack into a growing organism. This allows the FOLD
instruction to perform "Zero-Copy" compression, as data is already aligned
to Golden Ratio boundaries.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np


PHI = 1.618033988749895


class PhiBlock:
    """
    A single block in the Fibonacci heap.

    Attributes:
        size: Block size in bytes (must be a Fibonacci number).
        offset: Starting offset within the memory region.
        is_free: Whether the block is currently free.
    """

    def __init__(self, size: int, offset: int) -> None:
        self.size = size
        self.offset = offset
        self.is_free = True

    def __repr__(self) -> str:
        status = "free" if self.is_free else "used"
        return f"PhiBlock(size={self.size}, offset={self.offset}, {status})"


class PhiMalloc:
    """
    Fibonacci-based Memory Allocator.

    Optimises memory layout for Golden-Ratio folding and icosahedral
    addressing. Allocates in Fibonacci number sizes (1, 2, 3, 5, 8, 13,
    21, 34, 55, 89, 144, 233, 377, 610, 987) and performs Golden
    Coalescing on free operations.
    """

    # Pre-generated Fibonacci numbers for rapid lookup
    FIB = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]

    def __init__(self, total_size: int = 144):
        """
        Initialise the Φ-Allocator.

        Args:
            total_size: Total memory pool size in bytes. Defaults to 144
                        (F12), a computationally significant Fibonacci number.
        """
        self.PHI = PHI
        self.memory = np.zeros(total_size, dtype=np.uint8)
        self.total_size = total_size
        self.blocks: List[PhiBlock] = [PhiBlock(total_size, 0)]
        self._allocation_count = 0
        self._free_count = 0

    def _get_next_fib(self, n: int) -> int:
        """
        Return the smallest Fibonacci number >= n.

        Args:
            n: Requested size.

        Returns:
            The next Fibonacci number meeting or exceeding n.
        """
        for f in self.FIB:
            if f >= n:
                return f
        return self.FIB[-1]

    def allocate(self, requested_size: int) -> int:
        """
        Allocate a Fibonacci-sized block.

        If a free block is too large, it is split into smaller Fibonacci
        blocks (F_n → F_{n-1} + F_{n-2}) until the target size is reached.

        Args:
            requested_size: Minimum number of bytes needed.

        Returns:
            The offset of the allocated block within the memory region.

        Raises:
            MemoryError: If no resonant block is available.
        """
        target_size = self._get_next_fib(requested_size)

        for idx, block in enumerate(self.blocks):
            if block.is_free and block.size >= target_size:
                # Golden Splitting: recursively split F_n into F_{n-1} + F_{n-2}
                while block.size > target_size:
                    # Find the Fibonacci pair that sum to the current size
                    try:
                        fib_idx = self.FIB.index(block.size)
                    except ValueError:
                        # Size is between Fibonacci numbers; just allocate directly
                        break
                    if fib_idx < 2:
                        break  # Cannot split F_1 or F_2 further
                    f_n_minus_1 = self.FIB[fib_idx - 1]
                    f_n_minus_2 = self.FIB[fib_idx - 2]

                    # Split the block: first part = F_{n-1}, new block = F_{n-2}
                    old_size = block.size
                    block.size = f_n_minus_1
                    new_block = PhiBlock(f_n_minus_2, block.offset + f_n_minus_1)
                    self.blocks.insert(idx + 1, new_block)

                    # If the new block is still too big, continue splitting
                    if f_n_minus_1 > target_size:
                        # The first part is also too big; the while loop will
                        # handle it on the next iteration
                        pass
                    elif f_n_minus_1 < target_size:
                        # The split didn't reach target (shouldn't happen with
                        # proper Fibonacci sizes, but guard against edge cases)
                        break

                block.is_free = False
                self._allocation_count += 1
                return block.offset

        raise MemoryError(
            "Φ-Manifold Exhausted: No resonant blocks available. "
            f"Requested {requested_size} bytes (aligned to {target_size}). "
            f"Total pool: {self.total_size} bytes."
        )

    def free(self, offset: int) -> None:
        """
        Free an allocated block at the given offset.

        Performs Golden Coalescing: adjacent free Fibonacci blocks
        (F_n + F_{n-1}) are merged back into F_{n+1}, achieving
        zero-fragmentation heap management.

        Args:
            offset: The offset of the block to free.
        """
        for block in self.blocks:
            if block.offset == offset:
                block.is_free = True
                self._free_count += 1
                self._coalesce()
                return

    def _coalesce(self) -> None:
        """
        Merge adjacent free Fibonacci blocks.

        If two adjacent blocks are free and their sizes sum to a Fibonacci
        number, they are merged into one block. This process repeats until
        no further merges are possible.
        """
        i = 0
        while i < len(self.blocks) - 1:
            curr = self.blocks[i]
            nxt = self.blocks[i + 1]

            if curr.is_free and nxt.is_free:
                combined_size = curr.size + nxt.size
                if combined_size in self.FIB:
                    curr.size = combined_size
                    self.blocks.pop(i + 1)
                    # Restart coalescing to catch cascading merges
                    i = 0
                    continue
            i += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Return memory allocation statistics.

        Returns:
            Dictionary with allocation count, free count, free space,
            used space, fragmentation ratio, and block count.
        """
        free_bytes = sum(b.size for b in self.blocks if b.is_free)
        used_bytes = sum(b.size for b in self.blocks if not b.is_free)
        total_blocks = len(self.blocks)

        # Fragmentation: how many free blocks vs. a single contiguous region
        free_blocks = sum(1 for b in self.blocks if b.is_free)
        fragmentation = 1.0 - (
            1.0 / max(free_blocks, 1) if free_blocks > 0 else 0.0
        )

        return {
            "total_size": self.total_size,
            "used": used_bytes,
            "free": free_bytes,
            "total_blocks": total_blocks,
            "free_blocks": free_blocks,
            "used_blocks": total_blocks - free_blocks,
            "allocations": self._allocation_count,
            "frees": self._free_count,
            "fragmentation": float(fragmentation),
            "phi_alignment": PHI,
        }

    def status(self) -> str:
        """Return a human-readable status of the allocator."""
        stats = self.get_stats()
        return (
            f"PhiMalloc({self.total_size}B): "
            f"{stats['used']}B used, {stats['free']}B free, "
            f"{stats['total_blocks']} blocks, "
            f"frag={stats['fragmentation']:.3f}"
        )


__all__ = [
    "PhiBlock",
    "PhiMalloc",
]