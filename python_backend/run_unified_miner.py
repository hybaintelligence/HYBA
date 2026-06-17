#!/usr/bin/env python3
"""
HYBA Unified Miner — Deterministic Structured Proof Generation
================================================================
Launches the PYTHIA/PULVINI Unified Mining Engine against configured pools.

Production invariants:
  - live/prod mode never injects dev fixture jobs
  - live candidate generation must call UnifiedMiningEngine.search(job)
  - every no-job / no-search / no-submit state records an explicit reason
  - live submission remains guarded by StratumClient.submit_validated_share()

Environment:
  HYBA_POOL_CONFIG_PATH=config/mining_pools_test.json (testnet) or config/mining_pools_live.json (mainnet)
  HYBA_ENABLE_LIVE_STRATUM=true for real pool IO
  HYBA_ENABLE_LIVE_SHARE_SUBMIT=true only when intentionally submitting live shares
  HYBA_ALLOW_DEV_FIXTURES=true only for non-production, non-live development runs
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, List, Optional, Tuple

# Add backend to path when this script is executed directly from the repository.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Set pool config path BEFORE importing pythia_mining modules to ensure it's respected
# For mainnet mission, use live config; for testing, use test config via env override
default_config = str(Path(__file__).resolve().parents[1] / "config" / "mining_pools_live.json")
os.environ.setdefault("HYBA_POOL_CONFIG_PATH", 
                      os.getenv("HYBA_POOL_CONFIG_PATH", default_config))

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
UINT32_MAX = 2**32 - 1
TRUTHY = {"1", "true", "yes", "on"}


def signal_handler(signum: int, frame: Any) -> None:
    del frame
    global RUNNING
    logger.info("Received signal %s, shutting down...", signum)
    RUNNING = False


def _env_true(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in TRUTHY


class UnifiedMiner:
    """Connect the UnifiedMiningEngine to validated Stratum pool profiles."""

    def __init__(self, pool_config_path: Optional[str] = None):
        # Set pool config path BEFORE importing pool_profiles to ensure it's respected
        default_config = str(
            Path(__file__).resolve().parents[1] / "config" / "mining_pools_test.json"
        )
        self.pool_config_path = pool_config_path or os.getenv("HYBA_POOL_CONFIG_PATH", default_config)
        os.environ["HYBA_POOL_CONFIG_PATH"] = self.pool_config_path

        self.engine = UnifiedMiningEngine()

        # Activate PYTHIA autonomous intelligence
        from pythia_mining.autonomous_mining_controller import AutonomyLevel
        self.engine.set_autonomy_level(AutonomyLevel.AUTONOMOUS)
        logger.info("PYTHIA intelligence activated: AUTONOMOUS mode")
        logger.info("  Self-healing: ENABLED (consciousness-driven regime adaptation)")
        logger.info("  Self-optimization: ENABLED (search strategy + hashrate tuning)")
        logger.info("  Safety constraints: ENFORCED (mathematical bounds)")

        # Seed PYTHIA mission memory — one block, then shutdown
        from pythia_mining.pythia_one_block_mission import (
            ShareOutcome,
            seed_mission_memory,
            validate_mission_memory,
        )
        # Make ShareOutcome available for mission recording
        self.ShareOutcome = ShareOutcome
        self.mission = seed_mission_memory()
        assert validate_mission_memory(self.mission), "Mission memory validation failed"
        logger.info("PYTHIA mission memory seeded: %s", self.mission.mission)
        logger.info("  Mission target: %d pool-confirmed accepted block(s)", self.mission.mission_target.accepted_blocks)
        logger.info("  Shutdown after completion: %s", self.mission.mission_target.shutdown_after_completion)
        logger.info("  Max hashrate: %.1f EH/s (hard limit)", self.mission.hashrate_limit.max_autonomous_hashrate_ehs)
        logger.info("  Supreme invariants: %s", "; ".join(self.mission.supreme_invariants.invariants))
        self.pool_configs: List[PoolCredentialConfig] = []
        self.active_pool_idx: int = 0
        self.stratum: Optional[StratumClient] = None
        self.stats_interval = 60
        self._last_stats_time = time.monotonic()
        self._total_searches = 0
        self._accepted = 0
        self._rejected = 0
        self._locally_invalid = 0
        self._last_no_job_reason: Optional[str] = None
        self._last_search_skip_reason: Optional[str] = None
        self._last_submit_reason: Optional[str] = None
        self._reason_log_cache: dict[str, str] = {}
        # Track submitted nonces to prevent duplicates
        self._submitted_nonces: set[tuple[str, int]] = set()

    @staticmethod
    def _safe_target_hex(target: Any) -> str:
        """Return a compact target string without allowing telemetry to crash search."""
        if target is None:
            return "unknown"
        try:
            return f"0x{int(target):064x}"[:20]
        except (TypeError, ValueError, OverflowError):
            return "unknown"

    @staticmethod
    def _normalise_solver_ranges(ranges: Any) -> List[Tuple[int, int]]:
        """Clamp solver ranges to uint32 nonce space and discard invalid ranges."""
        normalised: List[Tuple[int, int]] = []
        for raw_range in ranges or []:
            try:
                start_raw, end_raw = raw_range
                start = max(0, int(start_raw))
                end = min(UINT32_MAX, int(end_raw))
            except (TypeError, ValueError):
                continue
            if start <= end:
                normalised.append((start, end))
        return normalised or [(0, UINT32_MAX)]

    @staticmethod
    def _nonce_plan_telemetry(nonce_plan: Any) -> tuple[int, Any, Any, int]:
        """Return stable telemetry from the current CompressedNonceSpacePlan API."""
        coverage_segments = getattr(nonce_plan, "coverage_segments", ()) or ()
        solver_ranges = UnifiedMiner._normalise_solver_ranges(
            getattr(nonce_plan, "solver_ranges", [])
        )
        return (
            len(coverage_segments),
            getattr(nonce_plan, "complete_coverage", "unknown"),
            getattr(nonce_plan, "overlap_free", "unknown"),
            len(solver_ranges),
        )

    @staticmethod
    def _production_mode() -> bool:
        return (
            os.getenv("HYBA_ENV", "").strip().lower() == "production"
            or os.getenv("NODE_ENV", "").strip().lower() == "production"
        )

    @staticmethod
    def _live_stratum_enabled() -> bool:
        return _env_true("HYBA_ENABLE_LIVE_STRATUM")

    @classmethod
    def _dev_fixtures_allowed(cls) -> bool:
        return (
            _env_true("HYBA_ALLOW_DEV_FIXTURES")
            and not cls._production_mode()
            and not cls._live_stratum_enabled()
        )

    def _record_reason(
        self,
        category: str,
        reason: str,
        *,
        level: int = logging.INFO,
        detail: Optional[str] = None,
    ) -> None:
        """Record and log state-transition reasons without spamming every loop."""
        if not hasattr(self, "_reason_log_cache"):
            self._reason_log_cache = {}
        setattr(self, f"_last_{category}_reason", reason)
        previous = self._reason_log_cache.get(category)
        if previous == reason:
            return
        self._reason_log_cache[category] = reason
        suffix = f" — {detail}" if detail else ""
        logger.log(level, "%s reason: %s%s", category.replace("_", " "), reason, suffix)

    def _log_runtime_mode(self) -> None:
        logger.info(
            "Runtime mode: HYBA_ENV=%s NODE_ENV=%s live_stratum=%s live_submit=%s dev_fixtures_allowed=%s",
            os.getenv("HYBA_ENV", ""),
            os.getenv("NODE_ENV", ""),
            self._live_stratum_enabled(),
            _env_true("HYBA_ENABLE_LIVE_SHARE_SUBMIT"),
            self._dev_fixtures_allowed(),
        )
        if self._production_mode() and _env_true("HYBA_ALLOW_DEV_FIXTURES"):
            logger.warning(
                "HYBA_ALLOW_DEV_FIXTURES is set but ignored because production mode is active"
            )

    def load_pools(self) -> None:
        """Load enabled pool configurations from env/runtime config."""
        # Config path already set in __init__ to ensure pool_profiles respects it
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
            self._record_reason("no_job", "pool_index_out_of_range", level=logging.ERROR)
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
                self._record_reason(
                    "no_job",
                    "pool_connect_failed",
                    level=logging.ERROR,
                    detail=profile.name,
                )
                self.stratum = None
                return False
            logger.info("Connected to %s", profile.name)
            self._record_reason("no_job", "connected_waiting_for_job")
            self.active_pool_idx = idx
            return True
        except Exception as exc:
            logger.exception("Failed to connect to %s", profile.name)
            self._record_reason(
                "no_job",
                "pool_connect_exception",
                level=logging.ERROR,
                detail=f"{profile.name}: {exc}",
            )
            self.stratum = None
            return False

    async def connect_next_pool(self) -> bool:
        """Try pools in priority order, starting from the next index."""
        n = len(self.pool_configs)
        for offset in range(1, n + 1):
            idx = (self.active_pool_idx + offset) % n
            if await self.connect_pool(idx):
                return True
        self._record_reason("no_job", "all_pools_unreachable", level=logging.ERROR)
        return False

    async def _next_job(self, timeout: float = 10.0) -> Optional[MiningJob]:
        """Poll live Stratum events and fail closed on fixtures in live/prod mode."""
        if self.stratum is None:
            self._record_reason("no_job", "stratum_client_missing", level=logging.ERROR)
            return None
        if not getattr(self.stratum, "is_connected", False):
            self._record_reason("no_job", "stratum_not_connected", level=logging.WARNING)
            return None

        deadline = time.monotonic() + timeout
        while RUNNING and time.monotonic() < deadline:
            remaining = max(0.05, min(1.0, deadline - time.monotonic()))
            job = await self.stratum.poll_live_event(timeout=remaining)
            if job is not None:
                self._record_reason("no_job", "job_received")
                return job

            active_job = await self.stratum.get_active_job_copy()
            if active_job is not None:
                self._record_reason("no_job", "active_job_available")
                return active_job

            if getattr(self.stratum, "live_session", None) is None:
                if self._dev_fixtures_allowed():
                    self._record_reason(
                        "no_job",
                        "dev_fixture_injected_explicit_non_live_mode",
                        level=logging.WARNING,
                    )
                    maybe_job = self.stratum.inject_dev_fixture_target_job(
                        difficulty=self.stratum.current_difficulty
                    )
                    return await maybe_job if inspect.isawaitable(maybe_job) else maybe_job

                self._record_reason(
                    "no_job",
                    "live_session_missing_dev_fixture_refused",
                    level=logging.ERROR,
                    detail="no live session means no job and no search in production/live mode",
                )
                return None

            await asyncio.sleep(0.05)

        self._record_reason(
            "no_job",
            "job_poll_timeout_no_notify_or_active_job",
            level=logging.WARNING,
            detail=f"timeout={timeout:.1f}s",
        )
        return None

    async def _handle_nonce_result(
        self,
        job: MiningJob,
        nonce: int,
        *,
        strategy_used: str,
        phi_resonance_score: Optional[float],
        search_time: float,
    ) -> bool:
        """Verify a candidate locally, optionally submit, then feed back to the engine.

        Returns True when the candidate passed local SHA-256d target validation and
        reached the pool-submission path. Returns False when the candidate was
        rejected locally before any pool submission attempt.
        """
        local = self.engine.submit_candidate(job, nonce)
        
        # Check for duplicate nonce submission to prevent pool rejections
        nonce_key = (job.job_id, nonce)
        if nonce_key in self._submitted_nonces:
            logger.info("Skipping duplicate nonce submission: job=%s nonce=%s", job.job_id, nonce)
            self._rejected += 1
            return False
        
        self._submitted_nonces.add(nonce_key)
        
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
            self._record_reason(
                "submit",
                "local_validation_rejected_before_pool_submit",
                detail=share_info["error_msg"],
            )
            await self.engine.on_share_result(share_info, accepted=False)
            logger.info(
                "Candidate rejected locally — nonce=%s, job=%s, reason=%s",
                nonce,
                job.job_id,
                share_info["error_msg"],
            )
            return False

        if self.stratum is None:
            self._rejected += 1
            share_info.update({"error_code": 503, "error_msg": "stratum_disconnected"})
            self._record_reason("submit", "stratum_disconnected_after_local_pass", level=logging.ERROR)
            await self.engine.on_share_result(share_info, accepted=False)
            return True

        self._record_reason("submit", "candidate_locally_valid_submitting_to_pool")
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
            self._record_reason("submit", "pool_accepted_share")
            logger.info("🎉 SHARE ACCEPTED — nonce=%s, job=%s", nonce, job.job_id)
            if hasattr(self, "mission"):
                self.mission.record_share_outcome(ShareOutcome.ACCEPTED_SHARE)
        else:
            self._rejected += 1
            self._record_reason(
                "submit",
                "pool_or_submit_guard_rejected_share",
                level=logging.WARNING,
                detail=share.error_message or str(share.error_code),
            )
            logger.info(
                "Share rejected — nonce=%s, job=%s, reason=%s",
                nonce,
                job.job_id,
                share.error_message,
            )
            if hasattr(self, "mission"):
                self.mission.record_share_outcome(self.ShareOutcome.REJECTED)

        return True

    async def _run_structured_search_batch(
        self,
        job: MiningJob,
        batch_size: int,
    ) -> tuple[int, int, int]:
        """Run actual AIOptimizer → PULVINI solver search cycles for a live job.

        Returns (candidates_checked, locally_or_pool_passed, local_or_solver_failed).
        The live miner must consume engine.search(job); it must not silently revert
        to nonce_cursor += 1 while claiming structured traversal.
        """
        batch_checked = 0
        local_pass = 0
        local_fail = 0

        for _ in range(max(1, int(batch_size))):
            if not RUNNING:
                break

            search_start = time.monotonic()
            try:
                result = await self.engine.search(job)
            except Exception as exc:
                local_fail += 1
                self._record_reason(
                    "search_skip",
                    "engine_search_exception",
                    level=logging.ERROR,
                    detail=str(exc),
                )
                logger.exception("Structured engine.search failed for job=%s", job.job_id)
                continue

            search_time = float(
                getattr(result, "search_time", None) or (time.monotonic() - search_start)
            )
            raw_nonce = getattr(result, "nonce", None)
            if raw_nonce is None:
                local_fail += 1
                self._record_reason(
                    "search_skip",
                    "structured_solver_returned_no_nonce",
                    level=logging.WARNING,
                    detail=f"job={job.job_id} strategy={getattr(result, 'strategy_used', 'unknown')}",
                )
                continue

            try:
                nonce = int(raw_nonce) & UINT32_MAX
            except (TypeError, ValueError, OverflowError):
                local_fail += 1
                self._record_reason(
                    "search_skip",
                    "structured_solver_returned_non_integer_nonce",
                    level=logging.ERROR,
                    detail=repr(raw_nonce),
                )
                continue

            self._record_reason("search_skip", "search_active_candidate_generated")
            self._total_searches += 1
            batch_checked += 1
            locally_valid = await self._handle_nonce_result(
                job,
                nonce,
                strategy_used=str(
                    getattr(result, "strategy_used", "phi_scaled_compressed_solver_search")
                ),
                phi_resonance_score=getattr(result, "phi_resonance_score", None),
                search_time=search_time,
            )
            if locally_valid:
                local_pass += 1
            else:
                local_fail += 1

        return batch_checked, local_pass, local_fail

    async def run_search_loop(self) -> None:
        """Main loop: poll live jobs, run structured solver search, verify, submit, adapt."""
        batch_size = int(os.getenv("HYBA_MINING_BATCH_SIZE", "500"))
        logger.info("=" * 72)
        logger.info("  HENDRIX-Φ + PULVINI Unified Miner — Structured Solver Traversal")
        logger.info("  Structured search cycles per job poll: %d", batch_size)
        logger.info("=" * 72)
        self._log_runtime_mode()

        from pythia_mining.pulvini_nonce_compression import build_pulvini_nonce_plan

        try:
            nonce_plan = build_pulvini_nonce_plan()
            segments, coverage, overlap_free, active_ranges = self._nonce_plan_telemetry(
                nonce_plan
            )
            logger.info(
                "PULVINI nonce plan: %d coverage_segments, complete_coverage=%s, overlap_free=%s, active_ranges=%d",
                segments,
                coverage,
                overlap_free,
                active_ranges,
            )
        except Exception as exc:
            if self._production_mode() or self._live_stratum_enabled():
                logger.exception("Unable to build PULVINI nonce-plan telemetry in live/prod mode")
                raise RuntimeError("pulvini_nonce_plan_unavailable_in_live_mode") from exc
            logger.warning("Unable to build PULVINI nonce-plan telemetry: %s", exc)

        while RUNNING:
            if not self.stratum or not self.stratum.is_connected:
                self._record_reason("no_job", "not_connected_reconnect_required", level=logging.WARNING)
                if not await self.connect_next_pool():
                    self._record_reason("no_job", "all_pools_unreachable_retrying", level=logging.ERROR)
                    await asyncio.sleep(30)
                    continue

            try:
                job = await self._next_job(timeout=10.0)
                if job is None:
                    self._record_reason(
                        "search_skip",
                        "not_searching_because_no_live_job",
                        level=logging.WARNING,
                        detail=self._last_no_job_reason,
                    )
                    await asyncio.sleep(0.25)
                    continue

                batch_start = time.monotonic()
                batch_checked, local_pass, local_fail = await self._run_structured_search_batch(
                    job,
                    batch_size,
                )
                batch_elapsed = time.monotonic() - batch_start
                batch_rate = batch_checked / max(0.001, batch_elapsed)

                if batch_checked and self._total_searches % (batch_size * 5) == 0:
                    logger.info(
                        "Structured search batch: %d candidates in %.2fs (%.0f candidates/s) batch_pass=%d batch_fail=%d target=%s total=%d",
                        batch_checked,
                        batch_elapsed,
                        batch_rate,
                        local_pass,
                        local_fail,
                        self._safe_target_hex(getattr(job, "target", None)),
                        self._total_searches,
                    )
                elif local_fail and not batch_checked:
                    self._record_reason(
                        "search_skip",
                        "structured_search_batch_produced_no_candidates",
                        level=logging.WARNING,
                        detail=f"failures={local_fail} target={self._safe_target_hex(getattr(job, 'target', None))}",
                    )

                # Check mission memory for shutdown after accepted block
                if hasattr(self, "mission") and self.mission.should_shutdown():
                    logger.info("=" * 72)
                    logger.info("  PYTHIA MISSION COMPLETE")
                    logger.info("  One pool-confirmed accepted block detected.")
                    logger.info("  Shutting down per mission memory.")
                    logger.info("=" * 72)
                    signal_handler(signal.SIGTERM, None)
                    break

                now = time.monotonic()
                if now - self._last_stats_time >= self.stats_interval:
                    await self.print_stats()

            except asyncio.CancelledError:
                break
            except Exception as exc:
                self._record_reason("search_skip", "search_loop_exception", level=logging.ERROR, detail=str(exc))
                logger.exception("Search loop error")
                await asyncio.sleep(1)

    async def print_stats(self) -> None:
        """Print unified engine state and mining statistics."""
        self._last_stats_time = time.monotonic()
        state = self.engine.get_unified_state()

        logger.info("-" * 72)
        logger.info("  MINING STATISTICS")
        logger.info("  SEARCHES:          %s", self._total_searches)
        logger.info("  ACCEPTED:          %s", self._accepted)
        logger.info("  REJECTED:          %s", self._rejected)
        logger.info("  LOCALLY INVALID:   %s", self._locally_invalid)
        logger.info(
            "  ACCEPT RATE:       %.1f%%",
            self._accepted / max(1, self._accepted + self._rejected) * 100,
        )
        if hasattr(self, "mission"):
            logger.info("  MISSION:           %s", self.mission.status.value)
            logger.info("  MISSION ACCEPTED SHARES:  %s", self.mission.accepted_shares)
            logger.info("  MISSION ACCEPTED BLOCKS:  %s", self.mission.accepted_blocks)
        logger.info("  Last no-job reason:      %s", self._last_no_job_reason)
        logger.info("  Last no-search reason:   %s", self._last_search_skip_reason)
        logger.info("  Last no-submit reason:   %s", self._last_submit_reason)
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
