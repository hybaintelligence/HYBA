#!/usr/bin/env python3
"""
HYBA Unified Miner — Deterministic Structured Proof Generation
================================================================
Launches the PYTHIA/PULVINI Unified Mining Engine against live pools.

Connects to two pools with automatic failover:
  1. Primary: CKPool (solo.ckpool.org:3333) — solo mining to your BTC address
  2. Backup: NiceHash SHA256 (sha256.auto.nicehash.com:443) — hashrate marketplace

The engine runs the full stack:
  Consciousness → AI Optimizer → HENDRIX-Φ Solver → PULVINI Memory → Stratum

Usage:
  python python_backend/run_unified_miner.py

Environment (optional overrides):
  HYBA_POOL_CONFIG_PATH=config/mining_pools_live.json
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine
from pythia_mining.stratum_client import StratumClient
from pythia_mining.pool_profiles import (
    load_runtime_pool_configs,
    save_runtime_pool_config,
    validate_pool_config,
    PoolCredentialConfig,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("unified_miner")

RUNNING = True


def signal_handler(signum: int, frame: Any) -> None:
    global RUNNING
    logger.info(f"Received signal {signum}, shutting down...")
    RUNNING = False


class UnifiedMiner:
    """Connects the UnifiedMiningEngine to live stratum pools."""

    def __init__(self, pool_config_path: Optional[str] = None):
        self.engine = UnifiedMiningEngine()
        self.pool_config_path = pool_config_path or str(
            Path(__file__).resolve().parents[1] / "config" / "mining_pools_live.json"
        )
        self.pool_configs: List[PoolCredentialConfig] = []
        self.active_pool_idx: int = 0
        self.stratum: Optional[StratumClient] = None
        self.stats_interval = 60  # print stats every 60s
        self._last_stats_time = time.time()
        self._total_searches = 0
        self._accepted = 0
        self._rejected = 0

    def load_pools(self) -> None:
        """Load pool configurations from config file."""
        # Set config path
        os.environ["HYBA_POOL_CONFIG_PATH"] = self.pool_config_path

        # Load and validate
        configs = load_runtime_pool_configs()
        self.pool_configs = [
            cfg for cfg in configs.values() if cfg.enabled
        ]
        if not self.pool_configs:
            logger.error("No enabled pool configurations found")
            sys.exit(1)

        logger.info(f"Loaded {len(self.pool_configs)} pool(s):")
        for i, cfg in enumerate(self.pool_configs):
            username = cfg.btc_address or cfg.username or "(not set)"
            logger.info(f"  [{i}] {cfg.name:20s} → {cfg.url:45s} user: {username}")

    async def connect_pool(self, idx: int) -> bool:
        """Connect to pool at given index."""
        if idx >= len(self.pool_configs):
            logger.error(f"Pool index {idx} out of range")
            return False

        cfg = self.pool_configs[idx]
        logger.info(f"Connecting to {cfg.name} at {cfg.url}...")

        try:
            # StratumClient now takes direct pool fields, not profiles
            self.stratum = StratumClient(
                pool_url=cfg.url,
                username=cfg.username or cfg.btc_address or "",
                password=cfg.password or "x",
                pool_name=cfg.name,
                stratum_version=cfg.stratum_version,
            )
            success = await self.stratum.connect()
            if success:
                logger.info(f"✅ Connected to {cfg.name}")
                self.active_pool_idx = idx
                return True
            else:
                logger.error(f"❌ Failed to connect to {cfg.name}")
                self.stratum = None
                return False
        except Exception as exc:
            logger.error(f"❌ Failed to connect to {cfg.name}: {exc}")
            self.stratum = None
            return False

    async def connect_next_pool(self) -> bool:
        """Try pools in priority order, starting from next index."""
        n = len(self.pool_configs)
        for offset in range(1, n + 1):
            idx = (self.active_pool_idx + offset) % n
            if await self.connect_pool(idx):
                return True
        return False

    async def run_search_loop(self) -> None:
        """Main search loop: run deterministic structured traversal on each job."""
        logger.info("=" * 72)
        logger.info("  HENDRIX-Φ + PULVINI Unified Miner — Deterministic Structured Traversal")
        logger.info("=" * 72)

        while RUNNING:
            if not self.stratum or not self.stratum.is_connected():
                logger.warning("Not connected. Reconnecting...")
                if not await self.connect_next_pool():
                    logger.error("All pools unreachable. Retrying in 30s...")
                    await asyncio.sleep(30)
                    continue

            try:
                # Wait for a mining job from the pool
                job = await self.stratum.wait_for_job(timeout=10.0)
                if job is None:
                    await asyncio.sleep(0.5)
                    continue

                # Run one deterministic structured search
                result = await self.engine.search(job)
                self._total_searches += 1

                if result.nonce is not None:
                    # Submit the found nonce to the pool
                    accepted = await self.stratum.submit_share(
                        job_id=job.job_id,
                        nonce=result.nonce,
                    )
                    share_info = {
                        "nonce": result.nonce,
                        "job_id": job.job_id,
                        "strategy_used": result.strategy_used,
                        "phi_resonance_score": result.phi_resonance_score,
                        "search_time": result.search_time,
                    }

                    # Feed back into the engine (meta-learning + consciousness)
                    await self.engine.on_share_result(share_info, accepted=accepted)

                    if accepted:
                        self._accepted += 1
                        logger.info(f"✅ Share ACCEPTED — nonce={result.nonce}, job={job.job_id}")
                    else:
                        self._rejected += 1
                        logger.info(f"❌ Share REJECTED — nonce={result.nonce}, job={job.job_id}")

                # Periodic stats
                now = time.time()
                if now - self._last_stats_time >= self.stats_interval:
                    await self.print_stats()

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Search error: {exc}")
                await asyncio.sleep(1)

    async def print_stats(self) -> None:
        """Print unified engine state and mining statistics."""
        self._last_stats_time = time.time()
        state = self.engine.get_unified_state()

        logger.info("-" * 72)
        logger.info(f"  MINING STATISTICS")
        logger.info(f"  Searches: {self._total_searches}")
        logger.info(f"  Accepted: {self._accepted}")
        logger.info(f"  Rejected: {self._rejected}")
        logger.info(f"  Accept rate: {self._accepted / max(1, self._accepted + self._rejected) * 100:.1f}%")
        logger.info(f"")
        logger.info(f"  ENGINE STATE:")
        logger.info(f"  Coherence:    {state['state']['phi_coherence']:.4f}")
        logger.info(f"  Regime:       {state['state']['integration_regime']}")
        logger.info(f"  Strategy:     {state['state']['strategy']}")
        logger.info(f"  Compression:  {state['state']['working_set_compression']:.2f}×")
        logger.info(f"  M32 domains:  {state['state']['m32_domains_covered']}/32")
        logger.info(f"")
        logger.info(f"  CONSCIOUSNESS:")
        logger.info(f"  Coherence:    {state['consciousness'].get('coherence_meter', 0):.4f}")
        logger.info(f"  Regime:       {state['consciousness'].get('integration_regime', '?')}")
        logger.info(f"  Components:   {state['consciousness'].get('active_components', 0)} active")
        logger.info(f"")
        logger.info(f"  SOLVER:")
        logger.info(f"  Available:    {state['solver'].get('available', False)}")
        logger.info(f"  Φ alignment:  {state['solver'].get('phi_phase_alignment', 0):.6f}")
        logger.info(f"  Entropy:      {state['solver'].get('dodecahedral_entropy', 0):.4f}")
        logger.info(f"")
        logger.info(f"  PROOFS:")
        proofs = state.get("proofs", {})
        logger.info(f"  Φ-fold lossless:        {proofs.get('phi_folding_lossless', '?')}")
        logger.info(f"  M32 expander gap:       {proofs.get('m32_expander_spectral_gap', '?')}")
        logger.info(f"  YM on-manifold fraction: {proofs.get('ym_on_manifold_fraction', '?')}")
        logger.info(f"  Grover advantage:        {proofs.get('grover_structured_advantage', '?')}×")
        logger.info("-" * 72)

    async def run(self) -> None:
        """Main entry point."""
        self.load_pools()

        # Connect to first pool
        if not await self.connect_pool(0):
            logger.warning("Primary pool failed, trying backup...")
            if not await self.connect_next_pool():
                logger.error("No pools available. Exiting.")
                return

        # Announce the doctrine
        logger.info("")
        logger.info("  ╔══════════════════════════════════════════════════════════╗")
        logger.info("  ║  HYBA transforms mining from undirected probabilistic   ║")
        logger.info("  ║  search into deterministic structured traversal with    ║")
        logger.info("  ║  externally verified proof acceptance.                  ║")
        logger.info("  ╚══════════════════════════════════════════════════════════╝")
        logger.info("")

        # Run the search loop
        await self.run_search_loop()


async def main() -> None:
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    miner = UnifiedMiner()
    await miner.run()


if __name__ == "__main__":
    asyncio.run(main())