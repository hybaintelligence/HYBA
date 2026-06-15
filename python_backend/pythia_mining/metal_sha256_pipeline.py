"""Metal-aware Bitcoin SHA-256d batch verification pipeline.

This module is the production verifier layer for HENDRIX-Φ candidate nonces.
It keeps the cryptographic oracle exact: every candidate is validated with the
same Bitcoin block-header double-SHA256 rules used by ``mining_validation``.

On Apple Silicon with MLX available, ``MetalSHA256Pipeline`` stages nonce batches
through the MLX/Metal device path before exact digest verification. On all other
hosts, ``CPUParallelVerifier`` provides a deterministic bounded-worker fallback.
The unified wrapper reports the backend used for every batch so operator
telemetry can distinguish measured host throughput from configured EHS capacity.
"""

from __future__ import annotations

import hashlib
import os
import platform
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, List, Optional, Sequence

from pythia_mining.mining_validation import (
    MiningValidationError,
    ShareValidationResult,
    build_block_header,
    coinbase_hash_hex,
    compute_merkle_root,
    display_hash,
    effective_target,
    hash256,
    validate_share,
)
from pythia_mining.stratum_client import MiningJob

UINT32_MAX = 2**32 - 1
DEFAULT_CPU_WORKERS = 32


@dataclass(frozen=True)
class NonceVerification:
    """Exact local verification result for one nonce candidate."""

    nonce: int
    valid: bool
    block_hash: str
    hash_int: int
    target: int
    header_hex: str
    merkle_root: str
    reason: Optional[str] = None
    backend: str = "cpu_parallel_exact_sha256d"
    elapsed_seconds: float = 0.0

    @classmethod
    def from_share_validation(
        cls,
        *,
        nonce: int,
        validation: ShareValidationResult,
        backend: str,
        elapsed_seconds: float,
    ) -> "NonceVerification":
        return cls(
            nonce=nonce,
            valid=bool(validation.valid),
            block_hash=validation.block_hash,
            hash_int=int(validation.hash_int),
            target=int(validation.target),
            header_hex=validation.header_hex,
            merkle_root=validation.merkle_root,
            reason=validation.reason,
            backend=backend,
            elapsed_seconds=float(elapsed_seconds),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BatchResult:
    """Batch-level verifier metrics and winner summary."""

    backend: str
    total_nonces: int
    elapsed_seconds: float
    hashes_per_second: float
    hashrate_ehs: float
    configured_capacity_ehs: Optional[float]
    target: int
    winners: List[NonceVerification] = field(default_factory=list)
    best_nonce: Optional[int] = None
    best_hash: Optional[str] = None
    best_hash_int: Optional[int] = None
    best_reason: Optional[str] = None
    metal_available: bool = False
    cpu_workers: int = DEFAULT_CPU_WORKERS

    @property
    def accepted_count(self) -> int:
        return len(self.winners)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["accepted_count"] = self.accepted_count
        return payload


def _resolve_extranonce2(job: MiningJob, extranonce2: Optional[str]) -> str:
    if extranonce2 is not None:
        return extranonce2
    return "00" * int(job.extranonce2_size)


def _check_nonce(nonce: int) -> int:
    if not isinstance(nonce, int) or nonce < 0 or nonce > UINT32_MAX:
        raise MiningValidationError("nonce must be an unsigned 32-bit integer")
    return int(nonce)


def verify_nonce(
    job: MiningJob,
    nonce: int,
    extranonce2: Optional[str] = None,
    *,
    backend: str = "cpu_parallel_exact_sha256d",
) -> NonceVerification:
    """Verify one Bitcoin block-header nonce with canonical double-SHA256."""

    checked_nonce = _check_nonce(nonce)
    started = time.perf_counter()
    validation = validate_share(job, checked_nonce, _resolve_extranonce2(job, extranonce2))
    elapsed = time.perf_counter() - started
    return NonceVerification.from_share_validation(
        nonce=checked_nonce,
        validation=validation,
        backend=backend,
        elapsed_seconds=elapsed,
    )


def verify_header_sha256d(header: bytes, target: int) -> tuple[bool, str, int]:
    """Verify a raw 80-byte Bitcoin header against a target."""

    if len(header) != 80:
        raise MiningValidationError("block header must be exactly 80 bytes")
    digest = hash256(header)
    hash_int = int.from_bytes(digest, byteorder="little", signed=False)
    return hash_int <= int(target), display_hash(digest), hash_int


def _build_header_for_nonce(job: MiningJob, nonce: int, extranonce2: str) -> tuple[bytes, str]:
    coinbase_hash = coinbase_hash_hex(job, extranonce2)
    merkle_root = compute_merkle_root(coinbase_hash, job.merkle_branch)
    return build_block_header(job, merkle_root, nonce), merkle_root


def sha256d_headers(headers: Sequence[bytes]) -> list[bytes]:
    """Hash a sequence of 80-byte headers exactly with hashlib."""

    return [hashlib.sha256(hashlib.sha256(header).digest()).digest() for header in headers]


class CPUParallelVerifier:
    """Bounded-worker exact SHA-256d batch verifier."""

    def __init__(self, workers: Optional[int] = None) -> None:
        env_workers = os.getenv("HYBA_CPU_VERIFY_WORKERS")
        configured = int(env_workers) if env_workers and env_workers.isdigit() else workers
        if configured is None:
            configured = DEFAULT_CPU_WORKERS
        self.workers = max(1, min(int(configured), DEFAULT_CPU_WORKERS))
        self.backend = "cpu_parallel_exact_sha256d"

    def verify_batch(
        self,
        job: MiningJob,
        nonces: Iterable[int],
        extranonce2: Optional[str] = None,
        *,
        configured_capacity_ehs: Optional[float] = None,
    ) -> BatchResult:
        nonce_list = [_check_nonce(int(nonce)) for nonce in nonces]
        target = effective_target(job)
        if not nonce_list:
            return BatchResult(
                backend=self.backend,
                total_nonces=0,
                elapsed_seconds=0.0,
                hashes_per_second=0.0,
                hashrate_ehs=0.0,
                configured_capacity_ehs=configured_capacity_ehs,
                target=target,
                cpu_workers=self.workers,
            )

        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            results = list(
                executor.map(
                    lambda nonce: verify_nonce(
                        job,
                        nonce,
                        extranonce2,
                        backend=self.backend,
                    ),
                    nonce_list,
                )
            )
        elapsed = max(time.perf_counter() - started, 1e-12)
        return _batch_result_from_verifications(
            backend=self.backend,
            verifications=results,
            elapsed_seconds=elapsed,
            target=target,
            metal_available=False,
            cpu_workers=self.workers,
            configured_capacity_ehs=configured_capacity_ehs,
        )

    def verify_nonce(
        self,
        job: MiningJob,
        nonce: int,
        extranonce2: Optional[str] = None,
    ) -> NonceVerification:
        return verify_nonce(job, nonce, extranonce2, backend=self.backend)


class MetalSHA256Pipeline:
    """Apple Silicon MLX/Metal batch staging with exact SHA-256d verification."""

    def __init__(self, require_mlx: bool = False) -> None:
        self.require_mlx = bool(require_mlx)
        self.backend = "metal_mlx_staged_exact_sha256d"
        self.apple_silicon_detected = (
            platform.system() == "Darwin" and platform.machine().lower() in {"arm64", "aarch64"}
        )
        self._mlx_core: Optional[Any] = None
        self._mlx_error: Optional[str] = None
        self._load_mlx()

    def _load_mlx(self) -> None:
        try:
            import mlx.core as mx  # type: ignore

            self._mlx_core = mx
        except Exception as exc:  # pragma: no cover - depends on host extras
            self._mlx_core = None
            self._mlx_error = str(exc)
            if self.require_mlx:
                raise RuntimeError(f"MLX/Metal verifier requested but unavailable: {exc}") from exc

    @property
    def mlx_available(self) -> bool:
        return self._mlx_core is not None

    @property
    def available(self) -> bool:
        allow_any_platform = os.getenv("HYBA_ENABLE_MLX_SHA256_ANY_PLATFORM", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        return bool(self.mlx_available and (self.apple_silicon_detected or allow_any_platform))

    @property
    def unavailable_reason(self) -> Optional[str]:
        if self.available:
            return None
        if not self.mlx_available:
            return self._mlx_error or "mlx_not_available"
        if not self.apple_silicon_detected:
            return "apple_silicon_not_detected"
        return "metal_unavailable"

    def initialize(self) -> dict[str, Any]:
        if self.available:
            self._stage_nonces([0, 1, 2, 3])
        elif self.require_mlx:
            raise RuntimeError(self.unavailable_reason or "MLX/Metal unavailable")
        return self.status()

    def status(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "available": self.available,
            "mlx_available": self.mlx_available,
            "apple_silicon_detected": self.apple_silicon_detected,
            "unavailable_reason": self.unavailable_reason,
        }

    def _stage_nonces(self, nonces: Sequence[int]) -> None:
        if not self.available or self._mlx_core is None:
            return
        mx = self._mlx_core
        dtype = getattr(mx, "uint32", getattr(mx, "float32", None))
        device = getattr(mx, "gpu", None)
        if device is not None and hasattr(mx, "default_device"):
            with mx.default_device(device):
                arr = mx.array(list(nonces), dtype=dtype)
                if hasattr(mx, "eval"):
                    mx.eval(arr)
        else:
            arr = mx.array(list(nonces), dtype=dtype)
            if hasattr(mx, "eval"):
                mx.eval(arr)

    def verify_batch(
        self,
        job: MiningJob,
        nonces: Iterable[int],
        extranonce2: Optional[str] = None,
        *,
        cpu_workers: int = DEFAULT_CPU_WORKERS,
        configured_capacity_ehs: Optional[float] = None,
    ) -> BatchResult:
        nonce_list = [_check_nonce(int(nonce)) for nonce in nonces]
        target = effective_target(job)
        if not nonce_list:
            return BatchResult(
                backend=self.backend,
                total_nonces=0,
                elapsed_seconds=0.0,
                hashes_per_second=0.0,
                hashrate_ehs=0.0,
                configured_capacity_ehs=configured_capacity_ehs,
                target=target,
                metal_available=self.available,
                cpu_workers=cpu_workers,
            )
        started = time.perf_counter()
        self._stage_nonces(nonce_list)
        with ThreadPoolExecutor(max_workers=max(1, min(int(cpu_workers), DEFAULT_CPU_WORKERS))) as executor:
            results = list(
                executor.map(
                    lambda nonce: verify_nonce(
                        job,
                        nonce,
                        extranonce2,
                        backend=self.backend,
                    ),
                    nonce_list,
                )
            )
        elapsed = max(time.perf_counter() - started, 1e-12)
        return _batch_result_from_verifications(
            backend=self.backend,
            verifications=results,
            elapsed_seconds=elapsed,
            target=target,
            metal_available=self.available,
            cpu_workers=cpu_workers,
            configured_capacity_ehs=configured_capacity_ehs,
        )

    def verify_nonce(
        self,
        job: MiningJob,
        nonce: int,
        extranonce2: Optional[str] = None,
    ) -> NonceVerification:
        if self.available:
            self._stage_nonces([nonce])
        return verify_nonce(job, nonce, extranonce2, backend=self.backend)


def _batch_result_from_verifications(
    *,
    backend: str,
    verifications: Sequence[NonceVerification],
    elapsed_seconds: float,
    target: int,
    metal_available: bool,
    cpu_workers: int,
    configured_capacity_ehs: Optional[float],
) -> BatchResult:
    total = len(verifications)
    hashes_per_second = total / max(elapsed_seconds, 1e-12)
    best = min(verifications, key=lambda item: item.hash_int) if verifications else None
    winners = [item for item in verifications if item.valid]
    return BatchResult(
        backend=backend,
        total_nonces=total,
        elapsed_seconds=float(elapsed_seconds),
        hashes_per_second=float(hashes_per_second),
        hashrate_ehs=float(hashes_per_second / 1e18),
        configured_capacity_ehs=configured_capacity_ehs,
        target=int(target),
        winners=winners,
        best_nonce=best.nonce if best else None,
        best_hash=best.block_hash if best else None,
        best_hash_int=best.hash_int if best else None,
        best_reason=best.reason if best else None,
        metal_available=bool(metal_available),
        cpu_workers=int(cpu_workers),
    )


class UnifiedBatchVerifier:
    """Select Metal when verified, otherwise use exact CPU batch verification."""

    def __init__(
        self,
        *,
        prefer_metal: Optional[bool] = None,
        require_metal: Optional[bool] = None,
        cpu_workers: Optional[int] = None,
        configured_capacity_ehs: Optional[float] = None,
    ) -> None:
        if prefer_metal is None:
            prefer_metal = os.getenv("HYBA_ENABLE_METAL_SHA256", "true").lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
        if require_metal is None:
            require_metal = os.getenv("HYBA_REQUIRE_METAL_SHA256", "false").lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
        self.prefer_metal = bool(prefer_metal)
        self.require_metal = bool(require_metal)
        self.cpu = CPUParallelVerifier(workers=cpu_workers)
        self.metal = MetalSHA256Pipeline(require_mlx=self.require_metal)
        self.configured_capacity_ehs = configured_capacity_ehs
        self.selected_backend = self.cpu.backend
        self.last_batch: Optional[BatchResult] = None
        self.initialize_metal()

    def initialize_metal(self) -> dict[str, Any]:
        status = self.metal.initialize()
        if self.prefer_metal and self.metal.available:
            self.selected_backend = self.metal.backend
        elif self.require_metal:
            raise RuntimeError(status.get("unavailable_reason") or "MLX/Metal unavailable")
        else:
            self.selected_backend = self.cpu.backend
        return self.status()

    def status(self) -> dict[str, Any]:
        return {
            "selected_backend": self.selected_backend,
            "prefer_metal": self.prefer_metal,
            "require_metal": self.require_metal,
            "cpu_workers": self.cpu.workers,
            "configured_capacity_ehs": self.configured_capacity_ehs,
            "metal": self.metal.status(),
            "last_batch": self.last_batch.to_dict() if self.last_batch else None,
        }

    def verify_batch(
        self,
        job: MiningJob,
        nonces: Iterable[int],
        extranonce2: Optional[str] = None,
    ) -> BatchResult:
        if self.prefer_metal and self.metal.available:
            result = self.metal.verify_batch(
                job,
                nonces,
                extranonce2,
                cpu_workers=self.cpu.workers,
                configured_capacity_ehs=self.configured_capacity_ehs,
            )
        else:
            result = self.cpu.verify_batch(
                job,
                nonces,
                extranonce2,
                configured_capacity_ehs=self.configured_capacity_ehs,
            )
        self.selected_backend = result.backend
        self.last_batch = result
        return result

    def submit_candidate(
        self,
        job: MiningJob,
        nonce: int,
        extranonce2: Optional[str] = None,
    ) -> NonceVerification:
        if self.prefer_metal and self.metal.available:
            result = self.metal.verify_nonce(job, nonce, extranonce2)
            self.selected_backend = self.metal.backend
        else:
            result = self.cpu.verify_nonce(job, nonce, extranonce2)
            self.selected_backend = self.cpu.backend
        return result


__all__ = [
    "BatchResult",
    "CPUParallelVerifier",
    "MetalSHA256Pipeline",
    "NonceVerification",
    "UnifiedBatchVerifier",
    "sha256d_headers",
    "verify_header_sha256d",
    "verify_nonce",
]
