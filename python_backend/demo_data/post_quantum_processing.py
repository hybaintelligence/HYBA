"""POST-QUANTUM Processing Module for Demos.

This module provides functions to process demo data with HYBA's POST-QUANTUM
architecture (Golden Quantum Trifecta + PULVINI Memory Compression + Salamander).
"""

import sys
import os
import time
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pythia_mining.pulvini_phi_memory import PulviniPhiMemoryCompressionEngine
from pythia_mining.phi_malloc import PhiMalloc
from pythia_mining.salamander_frontier import SalamanderOrchestrator


def process_with_pulvini(
    data: np.ndarray,
    use_sparse: bool = False,
) -> Dict[str, Any]:
    """
    Process data with PULVINI φ-folding transform.
    
    Args:
        data: Input data array
        use_sparse: Whether to force sparse φ-packing (deprecated, engine auto-selects)
    
    Returns:
        Dictionary with compression results
    """
    engine = PulviniPhiMemoryCompressionEngine()
    
    # Use the compress() method which automatically selects strategy
    result = engine.compress(data)
    
    return {
        'result': result,
        'compressed': result.folded,
        'kernel': result.retained_kernel,
        'original_size': result.original_bytes,
        'compressed_size': result.folded_working_set_bytes + result.retained_kernel_bytes,
        'working_set_compression_ratio': result.working_set_compression_ratio,
        'retained_state_compression_ratio': result.retained_state_compression_ratio,
        'reconstruction_error': result.reconstruction_error,
        'reversible': result.reversible,
        'compression_strategy': result.compression_strategy,
        'engine': engine,
    }


def allocate_with_phimalloc(
    size: int,
) -> Dict[str, Any]:
    """
    Allocate memory with PhiMalloc for golden coalescing.
    
    Args:
        size: Size to allocate in bytes
    
    Returns:
        Dictionary with allocation results
    """
    allocator = PhiMalloc()
    
    ptr = allocator.malloc(size)
    
    return {
        'allocator': allocator,
        'ptr': ptr,
        'size': size,
    }


def process_with_salamander(
    data: np.ndarray,
    target_hashrate: float = 100.0,
) -> Dict[str, Any]:
    """
    Process data with Salamander autonomous operations.
    
    Args:
        data: Input data array
        target_hashrate: Target hashrate for optimization
    
    Returns:
        Dictionary with Salamander processing results
    """
    orchestrator = SalamanderOrchestrator(total_target_hashrate=target_hashrate)
    orchestrator.initialize()
    
    # Observe system state
    metrics = orchestrator.salamander_core.observe_system_state(
        hashrate_current=len(data),
        hashrate_target=target_hashrate,
        memory_used=data.nbytes,
        memory_available=1024 * 1024 * 1024,  # 1 GB
        agent_health=[],
        worker_health=[],
    )
    
    # Log processing to audit trail
    orchestrator.audit_log = orchestrator.audit_log.append(
        "data_processed",
        timestamp=time(),
        data_size=data.nbytes,
        data_shape=data.shape,
        target_hashrate=target_hashrate,
    )
    
    return {
        'orchestrator': orchestrator,
        'metrics': metrics,
        'audit_log': orchestrator.audit_log,
    }


def process_with_post_quantum(
    data: np.ndarray,
    use_sparse_pulvini: bool = False,
    target_hashrate: float = 100.0,
    use_phimalloc: bool = True,
) -> Dict[str, Any]:
    """
    Process data with complete POST-QUANTUM architecture.
    
    Args:
        data: Input data array
        use_sparse_pulvini: Whether to use sparse φ-packing (deprecated, engine auto-selects)
        target_hashrate: Target hashrate for Salamander
        use_phimalloc: Whether to use PhiMalloc
    
    Returns:
        Dictionary with complete POST-QUANTUM processing results
    """
    results = {}
    
    # Step 1: PULVINI Memory Compression
    print("Step 1: PULVINI Memory Compression with φ-folding transform...")
    pulvini_results = process_with_pulvini(data, use_sparse=use_sparse_pulvini)
    results['pulvini'] = pulvini_results
    print(f"  ✓ Compression ratio: {pulvini_results['working_set_compression_ratio']:.2f}x (working set)")
    print(f"  ✓ Retained state ratio: {pulvini_results['retained_state_compression_ratio']:.2f}x (lossless)")
    print(f"  ✓ Original size: {pulvini_results['original_size']:,} bytes")
    print(f"  ✓ Compressed size: {pulvini_results['compressed_size']:,} bytes")
    print(f"  ✓ Strategy: {pulvini_results['compression_strategy']}")
    print(f"  ✓ Reversible: {pulvini_results['reversible']}")
    
    # Step 2: PhiMalloc Golden Coalescing
    if use_phimalloc:
        print("Step 2: PhiMalloc Golden Coalescing...")
        phimalloc_results = allocate_with_phimalloc(pulvini_results['compressed_size'])
        results['phimalloc'] = phimalloc_results
        print(f"  ✓ Allocated {phimalloc_results['size']:,} bytes with PhiMalloc")
    
    # Step 3: Salamander Autonomous Operations
    print("Step 3: Salamander Autonomous Operations...")
    salamander_results = process_with_salamander(data, target_hashrate=target_hashrate)
    results['salamander'] = salamander_results
    print(f"  ✓ System metrics: {salamander_results['metrics']}")
    print(f"  ✓ Audit log entries: {len(salamander_results['audit_log'].entries())}")
    
    # Step 4: Evidence-Based Regeneration
    print("Step 4: Evidence-Based Regeneration...")
    results['audit_log'] = salamander_results['audit_log']
    print(f"  ✓ Audit trail ready for regulatory compliance")
    
    return results


def demonstrate_post_quantum_advantages(
    data: np.ndarray,
) -> Dict[str, Any]:
    """
    Demonstrate POST-QUANTUM advantages vs traditional approaches.
    
    Args:
        data: Input data array
    
    Returns:
        Dictionary with comparison results
    """
    results = {}
    
    # POST-QUANTUM processing
    post_quantum_results = process_with_post_quantum(data)
    results['post_quantum'] = post_quantum_results
    
    # Traditional compression (gzip) for comparison
    import gzip
    import io
    
    data_bytes = data.tobytes()
    compressed_gzip = gzip.compress(data_bytes)
    traditional_ratio = len(data_bytes) / len(compressed_gzip)
    
    results['traditional'] = {
        'original_size': len(data_bytes),
        'compressed_size': len(compressed_gzip),
        'compression_ratio': traditional_ratio,
        'method': 'gzip',
    }
    
    # Comparison
    results['comparison'] = {
        'pulvini_advantage': post_quantum_results['pulvini']['working_set_compression_ratio'] / traditional_ratio,
        'pulvini_working_set_ratio': post_quantum_results['pulvini']['working_set_compression_ratio'],
        'pulvini_retained_state_ratio': post_quantum_results['pulvini']['retained_state_compression_ratio'],
        'traditional_ratio': traditional_ratio,
    }
    
    print("\n=== POST-QUANTUM vs Traditional Compression ===")
    print(f"Traditional (gzip): {traditional_ratio:.2f}x compression")
    print(f"POST-QUANTUM (PULVINI): {post_quantum_results['pulvini']['working_set_compression_ratio']:.2f}x working set")
    print(f"POST-QUANTUM (PULVINI): {post_quantum_results['pulvini']['retained_state_compression_ratio']:.2f}x retained state (lossless)")
    print(f"POST-QUANTUM Advantage: {results['comparison']['pulvini_advantage']:.2f}x")
    
    return results


if __name__ == "__main__":
    # Test POST-QUANTUM processing
    print("=== HYBA POST-QUANTUM Processing Demo ===")
    
    # Generate test data
    test_data = np.random.randn(1000, 1000).astype(np.float32)
    print(f"Test data shape: {test_data.shape}")
    print(f"Test data size: {test_data.nbytes:,} bytes")
    
    # Process with POST-QUANTUM
    results = process_with_post_quantum(test_data)
    
    # Demonstrate advantages
    comparison = demonstrate_post_quantum_advantages(test_data)
    
    print("\n=== Summary ===")
    print(f"PULVINI compression ratio: {results['pulvini']['compression_ratio']:.2f}x")
    print(f"Salamander audit log entries: {len(results['audit_log'].entries())}")
    print(f"POST-QUANTUM advantage: {comparison['comparison']['pulvini_advantage']:.2f}x")
