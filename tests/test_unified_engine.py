#!/usr/bin/env python3

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python_backend"))

from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine
from pythia_mining.stratum_client import MiningJob


async def test_unified_engine():
    print("Testing UnifiedMiningEngine...")

    job = MiningJob(
        job_id="doctor-job",
        prevhash="00" * 32,
        coinbase_parts=("", ""),
        merkle_branch=[],
        version="20000000",
        nbits="1d00ffff",
        ntime="5f5e1000",
        target=2**240,
        extranonce1="abcd",
        extranonce2_size=4,
    )
    engine = UnifiedMiningEngine()
    result = await engine.search(job)
    metrics = engine.solver.get_metrics()
    state = engine.get_unified_state()

    print("✓ Nonce:", result.nonce)
    print("✓ Metrics keys:", list(metrics.keys()))
    print("✓ Nonce space contract:", metrics.get("nonce_space_contract"))
    print("✓ Complete coverage:", metrics.get("complete_nonce_coverage"))
    print("✓ Overlap-free coverage:", metrics.get("overlap_free_nonce_coverage"))
    print("✓ Compressed working set:", metrics.get("compressed_working_set_size"))
    print("✓ SHA256d proof:", state["proofs"]["sha256d_external_oracle"])


if __name__ == "__main__":
    asyncio.run(test_unified_engine())
