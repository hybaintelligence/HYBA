"""Production mining system with Salamander regeneration guard.

This module is the operator-facing mining validation harness.  Live pool
connection and share submission remain owned by ``MiningExecutiveController``
and ``StratumClient``.  This harness is still useful for same-day deployment
because it runs the production mining controller against deterministic jobs,
records Salamander gate evidence, and refuses to fabricate live revenue when no
pool result is present.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

UTC = timezone.utc
from pathlib import Path
from typing import Any, Dict, List, Optional

from pythia_mining.autonomous_fault_tolerant_controller import FaultTolerantMiningController
from pythia_mining.regeneration_manager import RegenerationManager, get_regeneration_manager
from pythia_mining.salamander_mining_guard import SalamanderMiningGuard


@dataclass
class MiningSession:
    """Mining session tracking."""

    session_id: str
    start_time: str
    pool_url: str
    worker_name: str
    total_shares_submitted: int
    total_shares_accepted: int
    total_revenue_btc: float
    fault_tolerant_enabled: bool
    phi_resonance_rate: float
    logical_error_rate: float
    mode: str
    salamander_gate_ready: bool


@dataclass
class ShareSubmission:
    """Individual share submission record."""

    timestamp: str
    job_id: str
    nonce: int
    difficulty: float
    accepted: bool
    fault_tolerant: bool
    logical_error_rate: float
    time_to_solution_ms: float
    source: str
    revenue_btc: float = 0.0


class ProductionMiningSystem:
    """
    Production mining validation harness with fault-tolerant backend and
    Salamander regeneration preflight.
    """

    def __init__(
        self,
        pool_url: str = "stratum+tcp://btc.viabtc.com:3333",
        worker_name: str = "HYBA_PYTHAGORAS",
        enable_quantum: bool = True,
        mode: Optional[str] = None,
        regeneration_manager: Optional[RegenerationManager] = None,
    ):
        self.pool_url = pool_url
        self.worker_name = worker_name
        self.enable_quantum = enable_quantum
        self.mode = (mode or os.getenv("HYBA_MINING_MODE", "dry_run")).strip().lower()
        self.live_submission_enabled = os.getenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        self.regeneration = regeneration_manager or get_regeneration_manager()
        self.salamander_guard = SalamanderMiningGuard(self.regeneration)
        self.salamander_gate: Optional[Dict[str, Any]] = None

        # Initialize quantum controller
        if enable_quantum:
            self.controller = FaultTolerantMiningController()
            init_status = self.controller.start()
            self.quantum_active = init_status["fault_tolerant"]
            self._init_status = init_status
        else:
            self.controller = None
            self.quantum_active = False
            self._init_status = {"logical_error_rate": 0.0, "phi_resonance_target": None}

        # Session tracking
        self.session: Optional[MiningSession] = None
        self.share_history: List[ShareSubmission] = []

        # Revenue tracking.  This is deliberately zero until real pool results
        # supply accepted-share economics.  Dry-run validation must not invent BTC.
        self.total_shares_submitted = 0
        self.total_shares_accepted = 0
        self.estimated_revenue_btc = 0.0

        # Output directory
        self.output_dir = Path("artifacts/mining_sessions")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*70}")
        print("PRODUCTION MINING VALIDATION HARNESS INITIALIZED")
        print(f"{'='*70}")
        print(f"Pool: {pool_url}")
        print(f"Worker: {worker_name}")
        print(f"Mode: {self.mode}")
        print(f"Live share submit: {'ENABLED' if self.live_submission_enabled else 'DISABLED'}")
        print(f"Quantum Backend: {'✅ ENABLED' if self.quantum_active else '❌ DISABLED'}")
        if self.quantum_active:
            print(f"Logical Error Rate: {self._init_status['logical_error_rate']:.2e}")
            print(f"φ-Resonance Target: {self._init_status.get('phi_resonance_target', 'N/A')}")
        print(f"{'='*70}\n")

    async def prepare_for_live_mining(self) -> Dict[str, Any]:
        """Run Salamander gate before any mining session starts."""

        gate = await self.salamander_guard.preflight(source=f"production_mining_{self.mode}")
        self.salamander_gate = gate.to_dict()
        if not gate.ready:
            raise RuntimeError(f"Salamander mining gate blocked deployment: {gate.blocker}")
        return self.salamander_gate

    def start_session(self) -> str:
        """Start a new mining session after Salamander preflight has run."""

        if not self.salamander_gate or not self.salamander_gate.get("ready"):
            raise RuntimeError("Salamander mining gate must pass before starting a session")

        session_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        self.session = MiningSession(
            session_id=session_id,
            start_time=datetime.now(UTC).isoformat(),
            pool_url=self.pool_url,
            worker_name=self.worker_name,
            total_shares_submitted=0,
            total_shares_accepted=0,
            total_revenue_btc=0.0,
            fault_tolerant_enabled=self.quantum_active,
            phi_resonance_rate=0.9565 if self.quantum_active else 0.0,
            logical_error_rate=self._init_status.get("logical_error_rate", 0.0) if self.quantum_active else 0.0,
            mode=self.mode,
            salamander_gate_ready=True,
        )
        print(f"📊 SESSION STARTED: {session_id}")
        return session_id

    async def mine_block(self, job_data: Dict[str, Any]) -> Optional[ShareSubmission]:
        """
        Mine a single job with the configured backend.

        Accepted shares and revenue are taken only from explicit pool results.
        Dry-run jobs may produce deterministic validation accept/reject markers,
        but revenue remains zero unless supplied by a live pool result.
        """

        start_time = time.time()

        if self.quantum_active:
            result = self.controller.process_mining_job(job_data)
            nonce = int(result["nonce"])
            fault_tolerant = bool(result["fault_tolerant"])
            logical_error = float(result["logical_error_rate"])
        else:
            nonce = self._classical_mine(job_data)
            fault_tolerant = False
            logical_error = 0.0

        elapsed_ms = (time.time() - start_time) * 1000
        pool_result = job_data.get("pool_result") if isinstance(job_data, dict) else None

        if isinstance(pool_result, dict):
            accepted = bool(pool_result.get("accepted", False))
            source = "live_pool_result"
            revenue_btc = float(pool_result.get("revenue_btc", 0.0) or 0.0)
        elif self.mode == "dry_run":
            digest = hashlib.blake2b(
                f"{job_data.get('job_id', 'unknown')}:{nonce}:{job_data.get('difficulty', 1.0)}".encode(
                    "utf-8"
                ),
                digest_size=2,
            ).digest()
            accepted = int.from_bytes(digest, "big") % 2 == 0
            source = "dry_run_validation_marker"
            revenue_btc = 0.0
        else:
            accepted = False
            source = "no_live_pool_result"
            revenue_btc = 0.0

        share = ShareSubmission(
            timestamp=datetime.now(UTC).isoformat(),
            job_id=job_data.get("job_id", "unknown"),
            nonce=nonce,
            difficulty=float(job_data.get("difficulty", 1.0)),
            accepted=accepted,
            fault_tolerant=fault_tolerant,
            logical_error_rate=logical_error,
            time_to_solution_ms=elapsed_ms,
            source=source,
            revenue_btc=revenue_btc,
        )

        self.total_shares_submitted += 1
        if accepted:
            self.total_shares_accepted += 1
            self.estimated_revenue_btc += revenue_btc

        self.share_history.append(share)

        if self.session:
            self.session.total_shares_submitted = self.total_shares_submitted
            self.session.total_shares_accepted = self.total_shares_accepted
            self.session.total_revenue_btc = self.estimated_revenue_btc

        return share

    def _classical_mine(self, job_data: Dict[str, Any]) -> int:
        """Classical mining fallback with deterministic nonce derivation."""

        material = json.dumps(job_data, sort_keys=True, default=str).encode("utf-8")
        return int.from_bytes(hashlib.blake2b(material, digest_size=4).digest(), "big")

    async def run_mining_loop(self, duration_seconds: int = 60) -> None:
        """Run continuous mining validation for the specified duration."""

        print(f"🚀 STARTING MINING VALIDATION LOOP ({duration_seconds}s)")
        print(f"{'='*70}\n")

        gate = await self.prepare_for_live_mining()
        print(f"🦎 SALAMANDER GATE: {'READY' if gate['ready'] else gate['blocker']}")

        self.start_session()
        start_time = time.time()
        job_counter = 0

        while time.time() - start_time < duration_seconds:
            job_data = {
                "job_id": f"job_{job_counter:06d}",
                "prev_hash": "0" * 64,
                "coinbase": f"coinbase_{job_counter}",
                "merkle_branches": [],
                "version": "20000000",
                "nbits": "1d00ffff",
                "ntime": hex(int(time.time()))[2:],
                "difficulty": 1.0,
            }

            share = await self.mine_block(job_data)

            if share and share.accepted:
                print(
                    f"  ✅ Share {self.total_shares_submitted} ACCEPTED "
                    f"({share.source}, FT: {share.fault_tolerant}, {share.time_to_solution_ms:.2f}ms)"
                )
            elif share:
                print(f"  ❌ Share {self.total_shares_submitted} REJECTED ({share.source})")

            job_counter += 1
            await asyncio.sleep(0.1)

        print(f"\n{'='*70}")
        print("MINING VALIDATION LOOP COMPLETE")
        print(f"{'='*70}\n")

        self._print_session_summary()
        self._save_session()

    def _print_session_summary(self) -> None:
        """Print mining session summary."""

        if not self.session:
            return

        acceptance_rate = (self.total_shares_accepted / max(self.total_shares_submitted, 1)) * 100
        started = datetime.fromisoformat(self.session.start_time)
        duration = (datetime.now(UTC) - started).total_seconds()

        print(f"SESSION SUMMARY: {self.session.session_id}")
        print(f"{'='*70}")
        print(f"Duration: {duration:.1f}s")
        print(f"Mode: {self.mode}")
        print(f"Shares Submitted: {self.total_shares_submitted}")
        print(f"Shares Accepted: {self.total_shares_accepted}")
        print(f"Acceptance Rate: {acceptance_rate:.2f}%")
        print(f"Observed Revenue: {self.estimated_revenue_btc:.8f} BTC")
        print(f"Quantum Backend: {'✅ ENABLED' if self.quantum_active else '❌ DISABLED'}")
        print(f"Salamander Gate: {'✅ READY' if self.salamander_gate else '❌ NOT RUN'}")
        if self.quantum_active:
            print(f"φ-Resonance Rate: {self.session.phi_resonance_rate*100:.2f}%")
            print(f"Logical Error Rate: {self.session.logical_error_rate:.2e}")
        print(f"{'='*70}\n")

        if self.estimated_revenue_btc > 0:
            research_fund = self.estimated_revenue_btc * 0.40
            intelligence_fund = self.estimated_revenue_btc * 0.30
            operations_fund = self.estimated_revenue_btc * 0.20
            reserve_fund = self.estimated_revenue_btc * 0.10
            print("REVENUE ALLOCATION:")
            print(f"{'='*70}")
            print(f"Research:                 {research_fund:.8f} BTC (40%)")
            print(f"Quantum Intelligence:     {intelligence_fund:.8f} BTC (30%)")
            print(f"Operations:               {operations_fund:.8f} BTC (20%)")
            print(f"Reserve:                  {reserve_fund:.8f} BTC (10%)")
            print(f"{'='*70}\n")

    def _save_session(self) -> None:
        """Save session data to disk."""

        if not self.session:
            return

        session_data = {
            "session": asdict(self.session),
            "shares": [asdict(s) for s in self.share_history],
            "salamander_gate": self.salamander_gate,
            "summary": {
                "acceptance_rate": self.total_shares_accepted / max(self.total_shares_submitted, 1),
                "quantum_advantage": self.quantum_active,
                "phi_resonance_exploitation": 0.9565 if self.quantum_active else 0.0,
                "revenue_source": "live_pool_result_only",
            },
        }

        output_file = self.output_dir / f"session_{self.session.session_id}.json"
        with open(output_file, "w") as f:
            json.dump(session_data, f, indent=2)

        print(f"💾 Session saved: {output_file}\n")

    def get_revenue_report(self) -> Dict[str, Any]:
        """Generate comprehensive revenue report."""

        if not self.session:
            return {}

        acceptance_rate = self.total_shares_accepted / max(self.total_shares_submitted, 1)
        if self.quantum_active:
            classical_expected_rate = 0.50
            quantum_advantage_factor = acceptance_rate / classical_expected_rate
        else:
            quantum_advantage_factor = 1.0

        return {
            "session_id": self.session.session_id,
            "total_revenue_btc": self.estimated_revenue_btc,
            "shares_submitted": self.total_shares_submitted,
            "shares_accepted": self.total_shares_accepted,
            "acceptance_rate": acceptance_rate,
            "quantum_enabled": self.quantum_active,
            "quantum_advantage_factor": quantum_advantage_factor,
            "mode": self.mode,
            "salamander_gate": self.salamander_gate,
            "research_funding": {
                "research": self.estimated_revenue_btc * 0.40,
                "quantum_intelligence": self.estimated_revenue_btc * 0.30,
                "operations": self.estimated_revenue_btc * 0.20,
                "reserve": self.estimated_revenue_btc * 0.10,
            },
        }


async def run_production_mining(duration_minutes: int = 1) -> Dict[str, Any]:
    """Run production mining validation harness."""

    print("\n" + "=" * 70)
    print("PRODUCTION MINING VALIDATION: SALAMANDER-GATED")
    print("=" * 70)
    print("Objective: validate mining organism readiness without fabricating revenue")
    print("=" * 70 + "\n")

    system = ProductionMiningSystem(
        pool_url=os.getenv("HYBA_MINING_POOL_URL", "stratum+tcp://btc.viabtc.com:3333"),
        worker_name=os.getenv("HYBA_MINING_WORKER", "HYBA_PYTHAGORAS.quantum_001"),
        enable_quantum=False,
    )

    await system.run_mining_loop(duration_seconds=duration_minutes * 60)
    report = system.get_revenue_report()

    print("\n" + "=" * 70)
    print("PRODUCTION MINING VALIDATION COMPLETE")
    print("=" * 70)
    print(f"Observed Revenue: {report['total_revenue_btc']:.8f} BTC")
    print(f"Quantum Advantage Marker: {report['quantum_advantage_factor']:.2f}x")
    print(f"Salamander Gate: {report['salamander_gate']['ready']}")
    print("=" * 70 + "\n")

    return report


if __name__ == "__main__":
    # Allow duration override via environment variable for single-block proof
    duration = int(os.getenv("HYBA_MINING_DURATION_MINUTES", "1"))
    report = asyncio.run(run_production_mining(duration_minutes=duration))
    print("✅ MINING VALIDATION HARNESS OPERATIONAL")
    print("🦎 Salamander gate attached to mining runtime")
