#!/usr/bin/env python3
"""
HYBA Unified Miner — Deterministic Structured Proof Generation
================================================================
Launches the PYTHIA/PULVINI Unified Mining Engine against configured pools.

The miner uses the current StratumClient API directly:
  - direct pool_url/username/password construction from validated PoolProfile
  - boolean connection/authentication state
  - poll_live_event() / get_active_job_copy() for jobs
  - submit_validated_share() for exact SHA-256d validation and optional live submit

Environment:
  HYBA_POOL_CONFIG_PATH=config/mining_pools_live.json
  HYBA_ENABLE_LIVE_STRATUM=true for real pool IO
  HYBA_ENABLE_LIVE_SHARE_SUBMIT=true only when intentionally submitting live shares
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, List, Optional

# Add backend to path when this script is executed directly from the repository.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine
from pythia_mining.pool_profiles import (
    PoolCredentialConfig,
    PoolProfileError,
    load_runtime_pool_configs,
)
from pythia_mining.stratum_client import MiningJob, ShareResult, StratumClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("unified_miner")

RUNNING = True


def signal_handler(signum: int, frame: Any) -> None:
    del frame
    global RUNNING
    logger.info("Received signal %s, shutting down...", signum)
    RUNNING = False


class UnifiedMiner:
    """Connect the UnifiedMiningEngine to validated Stratum pool profiles."""

    def __init__(self, pool_config_path: Optional[str] = None):
        self.engine = UnifiedMiningEngine()
        self.pool_config_path = pool_config_path or str(
            Path(__file__).resolve().parents[1] / "config" / "mining_pools_live.json"
        )
        self.pool_configs: List[PoolCredentialConfig] = []
        self.active_pool_idx: int = 0
        self.stratum: Optional[StratumClient] = None
        self.stats_interval = 60
        self._last_stats_time = time.time()
        self._total_searches = 0
        self._accepted = 0
        self._rejected = 0
        self._locally_invalid = 0

    def load_pools(self) -> None:
        """Load enabled pool configurations from env/runtime config."""
        os.environ["HYBA_POOL_CONFIG_PATH"] = self.pool_config_path

        configs = load_runtime_pool_configs()
        valid_configs: list[PoolCredentialConfig] = []
        skipped: list[str] = []
        for cfg in configs.values():
            if not cfg.enabled:
                continue
            try:
                cfg.to_profile()
            except PoolProfileError as exc:
                skipped.append(f"{cfg.pool_id}: {exc}")
                continue
            valid_configs.append(cfg)

        self.pool_configs = valid_configs
        if not self.pool_configs:
            logger.error("No enabled, valid pool configurations found")
            if skipped:
                logger.error("Skipped invalid pool profiles: %s", "; ".join(skipped))
            sys.exit(1)

        logger.info("Loaded %s valid pool(s):", len(self.pool_configs))
        if skipped:
            logger.info("Skipped incomplete default pool profiles: %s", "; ".join(skipped))
        for i, cfg in enumerate(self.pool_configs):
            username = cfg.btc_address or cfg.username or cfg.worker or "(not set)"
            logger.info("  [%s] %-20s -> %-45s user: %s", i, cfg.name, cfg.url, username)

    async def connect_pool(self, idx: int) -> bool:
        """Connect to the pool at the given index using the current StratumClient API."""
        if idx >= len(self.pool_configs):
            logger.error("Pool index %s out of range", idx)
            return False

        cfg = self.pool_configs[idx]
        profile = cfg.to_profile()
        logger.info("Connecting to %s at %s...", profile.name, profile.url)

        try:
            if self.stratum is not None:
                await self.stratum.disconnect()
            self.stratum = StratumClient(
                pool_url=profile.url,
                username=profile.username,
                password=profile.password,
                pool_name=profile.name,
                stratum_version=profile.stratum_version,
                max_reconnect_attempts=profile.max_reconnect_attempts,
                max_share_retry_attempts=profile.max_share_retry_attempts,
                reconnect_backoff_base=profile.reconnect_backoff_base,
                reconnect_backoff_max=profile.reconnect_backoff_max,
                share_retry_backoff_base=profile.share_retry_backoff_base,
                share_retry_backoff_max=profile.share_retry_backoff_max,
            )
            connected = await self.stratum.connect()
            if not connected or not self.stratum.is_connected:
                logger.error("Pool %s did not reach connected state", profile.name)
                self.stratum = None
                return False
            logger.info("Connected to %s", profile.name)
            self.active_pool_idx = idx
            return True
        except Exception as exc:
            logger.error("Failed to connect to %s: %s", profile.name, exc)
            self.stratum = None
            return False

    async def connect_next_pool(self) -> bool:
        """Try pools in priority order, starting from the next index."""
        n = len(self.pool_configs)
        for offset in range(1, n + 1):
            idx = (self.active_pool_idx + offset) % n
            if await self.connect_pool(idx):
                return True
        return False

    async def _next_job(self, timeout: float = 10.0) -> Optional[MiningJob]:
        """Poll live Stratum events or return the active/dev fixture job."""
        if self.stratum is None:
            return None

        deadline = time.monotonic() + timeout
        while RUNNING and time.monotonic() < deadline:
            remaining = max(0.05, min(1.0, deadline - time.monotonic()))
            job = await self.stratum.poll_live_event(timeout=remaining)
            if job is not None:
                return job

            active_job = await self.stratum.get_active_job_copy()
            if active_job is not None:
                return active_job

            if self.stratum.live_session is None:
                return await self.stratum.inject_dev_fixture_target_job(
                    difficulty=self.stratum.current_difficulty
                )

            await asyncio.sleep(0.05)
        return None

    async def _handle_nonce_result(
        self,
        job: MiningJob,
        nonce: int,
        *,
        strategy_used: str,
        phi_resonance_score: Optional[float],
        search_time: float,
    ) -> None:
        """Verify a candidate locally, optionally submit, then feed back to the engine."""
        local = self.engine.submit_candidate(job, nonce)
        share_info: dict[str, Any] = {
            "nonce": nonce,
            "job_id": job.job_id,
            "strategy_used": strategy_used,
            "phi_resonance_score": phi_resonance_score,
            "solve_time": search_time,
            "block_hash": local.block_hash,
            "target": local.target,
        }

        if not local.valid:
            self._locally_invalid += 1
            self._rejected += 1
            share_info.update(
                {
                    "error_code": 400,
                    "error_msg": local.reason or "local_sha256d_target_miss",
                }
            )
            await self.engine.on_share_result(share_info, accepted=False)
            logger.info(
                "Candidate rejected locally — nonce=%s, job=%s, reason=%s",
                nonce,
                job.job_id,
                share_info["error_msg"],
            )
            return

        if self.stratum is None:
            self._rejected += 1
            share_info.update({"error_code": 503, "error_msg": "stratum_disconnected"})
            await self.engine.on_share_result(share_info, accepted=False)
            return

        share: ShareResult = await self.stratum.submit_validated_share(job, nonce)
        share_info.update(
            {
                "error_code": share.error_code,
                "error_msg": share.error_message,
                "block_hash": share.block_hash or local.block_hash,
                "target": share.target or local.target,
            }
        )
        await self.engine.on_share_result(share_info, accepted=share.accepted)

        if share.accepted:
            self._accepted += 1
            logger.info("Share accepted — nonce=%s, job=%s", nonce, job.job_id)
        else:
            self._rejected += 1
            logger.info(
                "Share rejected — nonce=%s, job=%s, reason=%s",
                nonce,
                job.job_id,
                share.error_message,
            )

    async def run_search_loop(self) -> None:
        """Main loop: poll jobs, verify nonces, submit, adapt.

        Uses full-space sequential nonce iteration through the PULVINI compressed
        plan's solver_ranges to maximize hash throughput.  The solver's coordinate
        collapse / quantum-walk / tunnel-anneal provides structural guidance but
        produces only ~20 unique nonces per cycle — far below the 2^32 space.
        This loop instead does a direct sequential scan through the full nonce
        space, which is what real mining hardware does, leveraging the compressed
        plan's overlap-free ranges for coverage.
        """
        batch_size = int(os.getenv("HYBA_MINING_BATCH_SIZE", "500"))
        logger.info("=" * 72)
        logger.info("  HENDRIX-Φ + PULVINI Unified Miner — Full-Space Sequential Traversal")
        logger.info("  Batch size: %d nonces per job cycle", batch_size)
        logger.info("=" * 72)

        # Build the full-space nonce range from the engine's compressed plan.
        from pythia_mining.pulvini_nonce_compression import build_pulvini_nonce_plan
        try:
            nonce_plan = build_pulvini_nonce_plan()
            solver_ranges = nonce_plan.solver_ranges
            logger.info(
                "PULVINI nonce plan: %d regions, coverage=%s, overlap_free=%s",
                len(nonce_plan.regions),
                nonce_plan.total_nonce_coverage,
                nonce_plan.is_overlap_free,
            )
        except Exception as exc:
            logger.warning("Falling back to full 2^32 range: %s", exc)
            solver_ranges = [(0, 2**32 - 1)]

        # Flatten ranges into a sequential nonce cursor.
        nonce_cursor = 0  # Current position across the full space
        range_start, range_end = 0, 0
        range_idx = 0

        def _next_nonce_range():
            nonlocal range_idx, range_start, range_end
            if range_idx < len(solver_ranges):
                range_start, range_end = solver_ranges[range_idx]
                range_idx += 1
                return range_start, range_end
            return None

        current_range = _next_nonce_range()

        while RUNNING:
            if not self.stratum or not self.stratum.is_connected:
                logger.warning("Not connected. Reconnecting...")
                if not await self.connect_next_pool():
                    logger.error("All pools unreachable. Retrying in 30s...")
                    await asyncio.sleep(30)
                    continue

            try:
                job = await self._next_job(timeout=10.0)
                if job is None:
                    await asyncio.sleep(0.01)
                    continue

                batch_start = time.time()
                batch_checked = 0
                local_pass = 0
                local_fail = 0
                for _ in range(batch_size):
                    if not RUNNING:
                        break
                    if current_range is None:
                        current_range = _next_nonce_range()
                        if current_range is None:
                            # Exhausted the full nonce space — wrap around.
                            range_idx = 0
                            current_range = _next_nonce_range()
                            if current_range is None:
                                break
                    rs, re = current_range
                    nonce = nonce_cursor
                    nonce_cursor += 1
                    if nonce > re:
                        current_range = _next_nonce_range()
                        if current_range is None:
                            range_idx = 0
                            current_range = _next_nonce_range()
                        if current_range is None:
                            break
                        rs, re = current_range
                        nonce = rs
                        nonce_cursor = rs + 1

                    self._total_searches += 1
                    batch_checked += 1

                    # Fast local SHA-256d validation via the engine verifier.
                    local = self.engine.submit_candidate(job, nonce)
                    if not local.valid:
                        local_fail += 1
                        self._locally_invalid += 1
                        self._rejected += 1
                        continue
                    local_pass += 1

                    # Candidate passed local validation — submit to pool.
                    logger.info(
                        "Candidate passed local validation! nonce=%s, job=%s — submitting to pool",
                        nonce, job.job_id,
                    )
                    share_info: dict[str, Any] = {
                        "nonce": nonce,
                        "job_id": job.job_id,
                        "strategy_used": "full_space_sequential",
                        "phi_resonance_score": None,
                        "solve_time": 0.0,
                        "block_hash": local.block_hash,
                        "target": local.target,
                    }
                    if self.stratum is not None:
                        share: ShareResult = await self.stratum.submit_validated_share(job, nonce)
                        share_info.update({
                            "error_code": share.error_code,
                            "error_msg": share.error_message,
                            "block_hash": share.block_hash or local.block_hash,
                            "target": share.target or local.target,
                        })
                        await self.engine.on_share_result(share_info, accepted=share.accepted)
                        if share.accepted:
                            self._accepted += 1
                            logger.info("🎉 SHARE ACCEPTED — nonce=%s, job=%s", nonce, job.job_id)
                        else:
                            self._rejected += 1
                            logger.info(
                                "Share rejected by pool — nonce=%s, job=%s, reason=%s",
                                nonce, job.job_id, share.error_message,
                            )
                    else:
                        self._rejected += 1
                        share_info.update({"error_code": 503, "error_msg": "stratum_disconnected"})
                        await self.engine.on_share_result(share_info, accepted=False)

                batch_elapsed = time.time() - batch_start
                batch_rate = batch_checked / max(0.001, batch_elapsed)
                if self._total_searches % (batch_size * 5) == 0:
                    nonce_range_pct = (nonce_cursor / (2**32)) * 100
                    logger.info(
                        "Scan: %d nonces in %.2fs (%.0f nonces/s) pass=%d fail=%d target=%s total=%d (%.4f%% of space)",
                        batch_checked, batch_elapsed, batch_rate,
                        local_pass, local_fail, hex(int(job.target))[:20],
                        self._total_searches, nonce_range_pct,
                    )

                now = time.time()
                if now - self._last_stats_time >= self.stats_interval:
                    await self.print_stats()

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Search error: %s", exc)
                await asyncio.sleep(1)

    async def print_stats(self) -> None:
        """Print unified engine state and mining statistics."""
        self._last_stats_time = time.time()
        state = self.engine.get_unified_state()

        logger.info("-" * 72)
        logger.info("  MINING STATISTICS")
        logger.info("  Searches:          %s", self._total_searches)
        logger.info("  Accepted:          %s", self._accepted)
        logger.info("  Rejected:          %s", self._rejected)
        logger.info("  Locally invalid:   %s", self._locally_invalid)
        logger.info(
            "  Accept rate:       %.1f%%",
            self._accepted / max(1, self._accepted + self._rejected) * 100,
        )
        logger.info("")
        logger.info("  ENGINE STATE:")
        logger.info("  Coherence:    %.4f", state["state"]["phi_coherence"])
        logger.info("  Regime:       %s", state["state"]["integration_regime"])
        logger.info("  Strategy:     %s", state["state"]["strategy"])
        logger.info(
            "  Compression:  %.2fx", state["state"]["working_set_compression"]
        )
        logger.info("  M32 domains:  %s/32", state["state"]["m32_domains_covered"])
        logger.info("  Verifier:     %s", state["state"]["verifier_backend"])
        logger.info("  Last H/s:     %.2f", state["state"]["last_batch_hashrate_hps"])
        logger.info("")
        logger.info("  CONSCIOUSNESS:")
        logger.info(
            "  Coherence:    %.4f", state["consciousness"].get("coherence_meter", 0)
        )
        logger.info(
            "  Regime:       %s", state["consciousness"].get("integration_regime", "?")
        )
        logger.info(
            "  Components:   %s active",
            state["consciousness"].get("active_components", 0),
        )
        logger.info("")
        logger.info("  SOLVER:")
        logger.info("  Available:    %s", state["solver"].get("available", False))
        logger.info(
            "  Φ alignment:  %.6f", state["solver"].get("phi_phase_alignment", 0)
        )
        logger.info(
            "  Entropy:      %.4f", state["solver"].get("dodecahedral_entropy", 0)
        )
        logger.info("")
        logger.info("  PROOFS:")
        proofs = state.get("proofs", {})
        logger.info("  Φ-fold lossless:         %s", proofs.get("phi_folding_lossless", "?"))
        logger.info("  M32 expander gap:        %s", proofs.get("m32_expander_spectral_gap", "?"))
        logger.info(
            "  YM on-manifold fraction: %s",
            proofs.get("ym_on_manifold_fraction", "?"),
        )
        logger.info(
            "  Grover advantage:        %sx",
            proofs.get("grover_structured_advantage", "?"),
        )
        logger.info(
            "  External oracle:         %s",
            proofs.get("sha256d_external_oracle", "?"),
        )
        logger.info("-" * 72)

    async def shutdown(self) -> None:
        if self.stratum is not None:
            await self.stratum.disconnect()
            self.stratum = None

    async def run(self) -> None:
        """Main entry point."""
        self.load_pools()

        if not await self.connect_pool(0):
            logger.warning("Primary pool failed, trying backup...")
            if not await self.connect_next_pool():
                logger.error("No pools available. Exiting.")
                return

        logger.info("")
        logger.info("  HYBA deterministic structured traversal active.")
        logger.info("  External proof acceptance remains SHA-256d + pool target.")
        logger.info("")

        try:
            await self.run_search_loop()
        finally:
            await self.shutdown()


async def main() -> None:
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    miner = UnifiedMiner()
    await miner.run()


if __name__ == "__main__":
    asyncio.run(main())
