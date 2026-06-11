"""
Enterprise Stratum Client v2.2 (Stratum v1 & v2 Compatibility Layer)
PYTHIA Mining System - Pool Communication Layer & Deterministic Scheduler
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:
    import aiohttp
except ImportError:  # pragma: no cover - optional dependency shape only
    class AiohttpUnavailable:
        ClientWebSocketResponse = Any
    aiohttp = AiohttpUnavailable()

from pythia_mining.audit_logger import AuditEvent, AuditEventType, get_audit_logger
from pythia_mining.live_stratum_session import LiveStratumSession, LiveStratumSessionError
from pythia_mining.metrics_store import PoolMetrics, get_metrics_store
from pythia_mining.pool_profiles import PoolProfile, build_profile, order_profiles
from pythia_mining.stratum_transport import StratumTransportError


@dataclass
class MiningJob:
    job_id: str
    prevhash: str
    coinbase_parts: Tuple[str, str]
    merkle_branch: List[str]
    version: str
    nbits: str
    ntime: str
    target: int
    received_timestamp: float = field(default_factory=time.time)
    extranonce1: str = ""
    extranonce2_size: int = 4
    stratum_version: int = 1
    is_stale: bool = False

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["coinbase1"] = self.coinbase_parts[0]
        payload["coinbase2"] = self.coinbase_parts[1]
        payload["target_hex"] = f"{int(self.target):064x}"
        return payload


@dataclass
class ShareResult:
    accepted: bool
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    job_id: str = ""
    nonce: int = 0
    block_hash: Optional[str] = None
    target: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AllPoolsOfflineError(ConnectionError):
    """Raised when every configured pool fails connection or authentication."""


class ProductionConfigurationError(RuntimeError):
    """Raised when production mode is missing required external configuration."""


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _is_production() -> bool:
    return os.getenv("NODE_ENV", os.getenv("HYBA_ENV", "development")).lower() == "production"


def _dev_fixtures_allowed() -> bool:
    return not _is_production() or _env_bool("HYBA_ALLOW_DEV_FIXTURES", default=False)


def _live_stratum_enabled() -> bool:
    """Enable real network I/O only in production or when explicitly requested."""
    return _is_production() or _env_bool("HYBA_ENABLE_LIVE_STRATUM", default=False)


def _live_share_submit_enabled() -> bool:
    """Gate live share submission separately from subscribe/authorize rollout."""
    return _env_bool("HYBA_ENABLE_LIVE_SHARE_SUBMIT", default=False)


def _difficulty_to_target(difficulty: float) -> int:
    if difficulty <= 0:
        raise ValueError("difficulty must be positive")
    target_limit = int("00000000ffff" + "0" * 52, 16)
    return max(1, int(target_limit / difficulty))


def _profiles_from_legacy_config(pools_config: Dict[str, Any]) -> List[PoolProfile]:
    profiles: List[PoolProfile] = []
    for pool_id, payload in (pools_config or {}).items():
        if not isinstance(payload, dict):
            continue
        enabled = bool(payload.get("enabled", True))
        if not enabled:
            continue
        try:
            profiles.append(
                build_profile(
                    str(pool_id),
                    name=str(payload.get("name") or pool_id),
                    url=str(payload.get("url") or payload.get("pool_url") or ""),
                    username=str(payload.get("username") or payload.get("worker") or ""),
                    password=str(payload.get("password") or payload.get("pass") or ""),
                    stratum_version=int(payload.get("stratum_version") or 1),
                    priority=int(payload.get("priority") or 100),
                    tls_required=bool(payload.get("tls_required", False)),
                )
            )
        except Exception:
            continue
    return order_profiles(profiles)


class StratumClient:
    """
    Substrate-independent Stratum client.

    Production credentials must be supplied externally. Development fixtures are allowed
    only outside production so test/smoke paths cannot leak into live deployments.
    """

    def __init__(self, pool_url: str, username: str, password: str, pool_name: str, stratum_version: int = 1):
        if _is_production() and (not username or not password):
            raise ProductionConfigurationError(f"Missing production credentials for pool {pool_name}")

        self.pool_url = pool_url
        self.username = username
        self.password = password
        self.pool_name = pool_name
        self.stratum_version = stratum_version

        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.live_session: Optional[LiveStratumSession] = None
        self.is_connected = False
        self.is_authenticated = False
        self.connection_state = "DISCONNECTED"
        self.current_jobs: Dict[str, MiningJob] = {}
        self.current_difficulty = 1.0
        self.extranonce1 = "00000001"
        self.extranonce2_size = 4
        self.shares_submitted = 0
        self.shares_accepted = 0
        self.shares_rejected = 0
        self.jobs_received = 0
        self.last_job_received_at: Optional[float] = None
        self.active_job_id: Optional[str] = None
        self.request_counter = 0
        self.connection_failures = 0
        self.last_failure_at: Optional[float] = None
        self.avg_latency: Optional[float] = None
        self.last_activity = time.time()
        self.last_pool_event_at: Optional[float] = None
        self.last_share_submit_at: Optional[float] = None
        self.last_share_error: Optional[str] = None
        self.stale_job_ids: set[str] = set()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_backoff_base = 1.0
        self.reconnect_backoff_max = 60.0
        self.heartbeat_interval = 60.0
        self.idle_timeout = 120.0
        self._heartbeat_task: Optional[asyncio.Task] = None
        self.share_retry_attempts = 0
        self.max_share_retry_attempts = 3
        self.share_retry_backoff_base = 0.5
        self.share_retry_backoff_max = 5.0
        self.logger = logging.getLogger(f"stratum.{pool_name}")
        self.audit_logger = get_audit_logger()
        self.metrics_store = get_metrics_store()

    def _calculate_backoff_delay(self) -> float:
        delay = min(self.reconnect_backoff_base * (2 ** self.reconnect_attempts), self.reconnect_backoff_max)
        import random
        jitter = delay * 0.1 * random.random()
        return delay + jitter

    async def connect(self) -> bool:
        self.audit_logger.log_connection_attempt(
            pool_name=self.pool_name,
            pool_url=self.pool_url,
            stratum_version=self.stratum_version,
            attempt_number=self.reconnect_attempts + 1,
        )
        self.logger.info("Connecting via Stratum v%s to pool %s (%s)", self.stratum_version, self.pool_name, self.pool_url)
        self.connection_state = "CONNECTING"
        started = time.monotonic()
        try:
            parsed = urlparse(self.pool_url)
            if not parsed.scheme or not parsed.hostname:
                raise ValueError(f"Invalid pool URL: {self.pool_url}")
            if parsed.port is None:
                default_port = 3334 if self.stratum_version == 2 else 3333
                self.pool_url = f"{parsed.scheme}://{parsed.hostname}:{default_port}{parsed.path or ''}"

            self.connection_state = "ESTABLISHING"
            if _live_stratum_enabled():
                await self._connect_live()
            else:
                await self._connect_development_fixture()

            self.connection_failures = 0
            self.last_failure_at = None
            self.avg_latency = (time.monotonic() - started) * 1000.0
            self.last_activity = time.time()
            self.reconnect_attempts = 0
            self.audit_logger.log_connection_success(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                latency_ms=self.avg_latency,
                stratum_version=self.stratum_version,
            )
            self.metrics_store.record_connection_event(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                event_type="connection_success",
                latency_ms=self.avg_latency,
                attempt_number=self.reconnect_attempts + 1,
            )
            self._persist_metrics()
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            return True
        except Exception as e:
            self.audit_logger.log_connection_failure(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                error=str(e),
                attempt_number=self.reconnect_attempts + 1,
            )
            self.metrics_store.record_connection_event(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                event_type="connection_failure",
                error_message=str(e),
                attempt_number=self.reconnect_attempts + 1,
            )
            self.logger.error("Failed to connect to pool %s: %s", self.pool_name, e)
            self.connection_state = f"ERROR: {str(e)}"
            self.is_connected = False
            self.is_authenticated = False
            self.connection_failures += 1
            self.last_failure_at = time.time()
            self.reconnect_attempts += 1
            await self._close_live_session()
            self._persist_metrics()
            if isinstance(e, (ValueError, ProductionConfigurationError, LiveStratumSessionError)):
                self.logger.error("Pool %s connection failed permanently: %s", self.pool_name, e)
                return False
            if self.reconnect_attempts < self.max_reconnect_attempts:
                delay = self._calculate_backoff_delay()
                self.audit_logger.log_reconnection_attempt(
                    pool_name=self.pool_name,
                    pool_url=self.pool_url,
                    attempt_number=self.reconnect_attempts + 1,
                    delay_seconds=delay,
                )
                self.logger.info("Reconnection attempt %s/%s for pool %s in %.2f seconds", self.reconnect_attempts + 1, self.max_reconnect_attempts, self.pool_name, delay)
                await asyncio.sleep(delay)
                return await self.connect()
            return False

    def _persist_metrics(self) -> None:
        acceptance_rate = self.shares_accepted / self.shares_submitted if self.shares_submitted > 0 else 0.0
        self.metrics_store.update_pool_metrics(
            PoolMetrics(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                shares_submitted=self.shares_submitted,
                shares_accepted=self.shares_accepted,
                shares_rejected=self.shares_rejected,
                connection_failures=self.connection_failures,
                avg_latency_ms=self.avg_latency,
                last_activity_timestamp=self.last_activity,
                last_pool_event_timestamp=self.last_pool_event_at,
                last_share_submit_timestamp=self.last_share_submit_at,
                current_difficulty=self.current_difficulty,
                current_jobs_count=len(self.current_jobs),
                acceptance_rate=acceptance_rate,
            )
        )

    async def _heartbeat_loop(self) -> None:
        while self.is_connected and self.live_session is not None:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                idle_time = time.time() - self.last_activity
                if idle_time > self.idle_timeout:
                    try:
                        event, _payload = await self.live_session.read_event(timeout=5.0)
                        if event:
                            self.last_activity = time.time()
                            self.last_pool_event_at = self.last_activity
                    except (asyncio.TimeoutError, StratumTransportError, LiveStratumSessionError):
                        self.audit_logger.log_heartbeat_failure(
                            pool_name=self.pool_name,
                            pool_url=self.pool_url,
                            idle_time_seconds=idle_time,
                        )
                        await self.disconnect()
                        await self.connect()
                        break
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Heartbeat loop error for pool %s: %s", self.pool_name, e)
                break

    async def _connect_live(self) -> None:
        if self.stratum_version != 1:
            raise LiveStratumSessionError("live Stratum v2 transport is not implemented; configure a Stratum v1 pool or keep this pool disabled")

        self.audit_logger.log_handshake_start(pool_name=self.pool_name, pool_url=self.pool_url, username=self.username)
        profile = build_profile(
            self.pool_name.lower().replace(" ", "_"),
            name=self.pool_name,
            url=self.pool_url,
            username=self.username,
            password=self.password,
            stratum_version=self.stratum_version,
            tls_required=urlparse(self.pool_url).scheme in {"stratum+ssl", "stratum+tls"},
        )
        self.live_session = LiveStratumSession(profile)
        await self.live_session.connect()
        self.is_connected = True
        self.connection_state = "CONNECTED"
        handshake = await self.live_session.subscribe_and_authorize()
        self.extranonce1 = handshake.extranonce1
        self.extranonce2_size = int(handshake.extranonce2_size)
        self.is_authenticated = handshake.authorized
        self.connection_state = "AUTHENTICATED"
        if self.is_authenticated:
            self.audit_logger.log_handshake_success(pool_name=self.pool_name, pool_url=self.pool_url, extranonce1=self.extranonce1, extranonce2_size=self.extranonce2_size)
        else:
            self.audit_logger.log_handshake_failure(pool_name=self.pool_name, pool_url=self.pool_url, error="Authorization rejected by pool")

    async def _connect_development_fixture(self) -> None:
        self.is_connected = True
        self.connection_state = "CONNECTED"
        self.last_activity = time.time()
        await self._negotiate_fixture_handshake()

    async def _negotiate_fixture_handshake(self):
        if not _dev_fixtures_allowed():
            raise ProductionConfigurationError("development Stratum fixtures are disabled in production")
        self.request_counter += 1
        rid = self.request_counter
        if self.stratum_version == 1:
            self.logger.info("[Stratum v1 fixture] Subscription payload: %s", json.dumps({"id": rid, "method": "mining.subscribe", "params": ["pythia-quantum/2.0.0", None]}))
            self.extranonce1 = os.getenv("HYBA_STRATUM_EXTRANONCE1", "f000bba1")
            self.extranonce2_size = int(os.getenv("HYBA_STRATUM_EXTRANONCE2_SIZE", "4"))
            self.is_authenticated = True
            self.connection_state = "AUTHENTICATED"
        elif self.stratum_version == 2:
            self.extranonce1 = os.getenv("HYBA_STRATUM_V2_EXTRANONCE1", "ff02")
            self.extranonce2_size = int(os.getenv("HYBA_STRATUM_V2_EXTRANONCE2_SIZE", "3"))
            self.is_authenticated = True
            self.connection_state = "AUTHENTICATED_V2"
        else:
            raise ValueError(f"Unsupported Stratum version: {self.stratum_version}")

    async def poll_live_event(self, *, timeout: float = 0.1) -> Optional[MiningJob]:
        if self.live_session is None:
            return None
        try:
            event, payload = await self.live_session.read_event(timeout=timeout)
        except (asyncio.TimeoutError, StratumTransportError):
            return None
        self.last_activity = time.time()
        self.last_pool_event_at = self.last_activity
        if event == "mining.set_difficulty":
            old_difficulty = self.current_difficulty
            self.current_difficulty = float(payload.difficulty)
            self.audit_logger.log_difficulty_change(pool_name=self.pool_name, pool_url=self.pool_url, old_difficulty=old_difficulty, new_difficulty=self.current_difficulty)
            self._persist_metrics()
            return None
        if event == "mining.notify":
            if payload.clean_jobs:
                for job_id in self.current_jobs:
                    self.stale_job_ids.add(job_id)
                    self.audit_logger.log_job_stale(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job_id)
                self.current_jobs.clear()
            job = MiningJob(
                job_id=payload.job_id,
                prevhash=payload.prevhash,
                coinbase_parts=(payload.coinbase1, payload.coinbase2),
                merkle_branch=payload.merkle_branch,
                version=payload.version,
                nbits=payload.nbits,
                ntime=payload.ntime,
                target=_difficulty_to_target(self.current_difficulty),
                received_timestamp=time.time(),
                extranonce1=self.extranonce1,
                extranonce2_size=self.extranonce2_size,
                stratum_version=self.stratum_version,
                is_stale=False,
            )
            self.current_jobs[job.job_id] = job
            self.jobs_received += 1
            self.last_job_received_at = job.received_timestamp
            self.active_job_id = job.job_id
            self.audit_logger.log_job_received(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, clean_jobs=payload.clean_jobs, difficulty=self.current_difficulty)
            self._persist_metrics()
            return job
        if event == "mining.set_extranonce":
            self.audit_logger.log_extranonce_change(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                old_extranonce1=self.extranonce1,
                new_extranonce1=payload.extranonce1,
                old_extranonce2_size=self.extranonce2_size,
                new_extranonce2_size=payload.extranonce2_size,
            )
            self.extranonce1 = payload.extranonce1
            self.extranonce2_size = payload.extranonce2_size
            return None
        if event == "mining.set_version_mask":
            return None
        if event == "unknown":
            self.logger.warning("Pool %s sent unsupported message: method=%s", self.pool_name, payload.get("method"))
            return None
        return None

    async def submit_validated_share(self, job: MiningJob, nonce: int, extranonce2: Optional[str] = None) -> ShareResult:
        """Validate locally, then submit to the pool before recording accepted/rejected counters."""
        from pythia_mining.mining_validation import MiningValidationError, validate_share

        if job.job_id in self.stale_job_ids or job.is_stale:
            self.shares_submitted += 1
            self.shares_rejected += 1
            self.last_share_error = "stale_job"
            self.audit_logger.log_share_rejected(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, reason="stale_job", error_code=410)
            self.metrics_store.record_share_submission(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, accepted=False, error_code=410, error_message="stale_job")
            self._persist_metrics()
            return ShareResult(False, 410, "stale_job", job.job_id, nonce)

        extranonce2_value = extranonce2 or ("00" * job.extranonce2_size)
        if self.live_session is not None and not _live_share_submit_enabled():
            self.audit_logger.log_share_rejected(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, reason="live_share_submit_disabled", error_code=423)
            self.shares_submitted += 1
            self.shares_rejected += 1
            self.last_share_error = "live_share_submit_disabled"
            self.metrics_store.record_share_submission(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, accepted=False, error_code=423, error_message="live_share_submit_disabled")
            self._persist_metrics()
            return ShareResult(False, 423, "live_share_submit_disabled", job.job_id, nonce)

        try:
            validation = validate_share(job, nonce, extranonce2_value)
        except MiningValidationError as exc:
            self.audit_logger.log_share_validation_error(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, error=str(exc))
            self.shares_submitted += 1
            self.shares_rejected += 1
            self.last_share_error = str(exc)
            self.metrics_store.record_share_submission(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, accepted=False, error_code=400, error_message=str(exc))
            self._persist_metrics()
            return ShareResult(False, 400, str(exc), job.job_id, nonce)

        if not validation.valid:
            self.audit_logger.log_share_rejected(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, reason=validation.reason, error_code=1)
            self.shares_submitted += 1
            self.shares_rejected += 1
            self.last_share_error = validation.reason
            self.metrics_store.record_share_submission(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, accepted=False, error_code=1, error_message=validation.reason, block_hash=validation.block_hash, target=validation.target)
            self._persist_metrics()
            return ShareResult(False, 1, validation.reason, job.job_id, nonce, validation.block_hash, validation.target)

        if self.live_session is None:
            return self.validate_and_record_share(job, nonce, extranonce2_value)

        self.shares_submitted += 1
        self.last_share_submit_at = time.time()
        nonce_hex = nonce.to_bytes(4, byteorder="little", signed=False).hex()
        self.audit_logger.log_share_submission(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, extranonce2=extranonce2_value)

        submit_result = None
        last_exception = None
        for attempt in range(self.max_share_retry_attempts):
            try:
                submit_result = await self.live_session.submit_share(job_id=job.job_id, extranonce2=extranonce2_value, ntime=job.ntime, nonce=nonce_hex)
                if submit_result.accepted:
                    break
                if not submit_result.accepted and submit_result.error:
                    break
            except Exception as exc:
                last_exception = exc
                if attempt < self.max_share_retry_attempts - 1:
                    await asyncio.sleep(min(self.share_retry_backoff_base * (2 ** attempt), self.share_retry_backoff_max))
                else:
                    self.audit_logger.log_share_rejected(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, reason=f"pool_submit_failed: {last_exception}", error_code=502)
                    self.shares_rejected += 1
                    self.last_share_error = str(last_exception)
                    self.metrics_store.record_share_submission(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, accepted=False, error_code=502, error_message=f"pool_submit_failed: {last_exception}", block_hash=validation.block_hash, target=validation.target)
                    self._persist_metrics()
                    return ShareResult(False, 502, f"pool_submit_failed: {last_exception}", job.job_id, nonce, validation.block_hash, validation.target)

        if submit_result is None:
            self.shares_rejected += 1
            self.last_share_error = "pool_submit_no_response"
            self.metrics_store.record_share_submission(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, accepted=False, error_code=502, error_message="pool_submit_no_response", block_hash=validation.block_hash, target=validation.target)
            self._persist_metrics()
            return ShareResult(False, 502, "pool_submit_no_response", job.job_id, nonce, validation.block_hash, validation.target)

        if submit_result.accepted:
            self.audit_logger.log_share_accepted(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, block_hash=validation.block_hash)
            self.metrics_store.record_share_submission(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, accepted=True, block_hash=validation.block_hash, target=validation.target)
            self.shares_accepted += 1
            self.last_share_error = None
        else:
            self.audit_logger.log_share_rejected(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, reason=str(submit_result.error), error_code=2)
            self.metrics_store.record_share_submission(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, accepted=False, error_code=2, error_message=str(submit_result.error), block_hash=validation.block_hash, target=validation.target)
            self.shares_rejected += 1
            self.last_share_error = str(submit_result.error)
        self._persist_metrics()
        return ShareResult(submit_result.accepted, None if submit_result.accepted else 2, None if submit_result.accepted else str(submit_result.error), job.job_id, nonce, validation.block_hash, validation.target)

    async def _close_live_session(self) -> None:
        if self.live_session is not None:
            try:
                await self.live_session.close()
            except (LiveStratumSessionError, StratumTransportError, OSError):
                pass
            finally:
                self.live_session = None

    async def disconnect(self):
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
        await self._close_live_session()
        self.is_connected = False
        self.is_authenticated = False
        self.connection_state = "DISCONNECTED"
        self.audit_logger.log_event(AuditEvent(AuditEventType.DISCONNECTION, self.pool_name, self.pool_url, time.time(), {}, "INFO"))
        self.metrics_store.record_connection_event(pool_name=self.pool_name, pool_url=self.pool_url, event_type="disconnection")
        self._persist_metrics()

    def inject_dev_fixture_target_job(self, difficulty: float):
        """Create a dev/test mining job fixture. Disabled in production."""
        if not _dev_fixtures_allowed():
            raise ProductionConfigurationError("Simulated mining jobs are disabled in production")
        if difficulty <= 0:
            raise ValueError("difficulty must be positive")
        target = _difficulty_to_target(difficulty)
        job_id = f"fixture-{int(time.time() * 1000)}"
        job = MiningJob(
            job_id=job_id,
            prevhash="00" * 32,
            coinbase_parts=("0100000001", "ffffffff"),
            merkle_branch=[],
            version="20000000",
            nbits="1d00ffff",
            ntime="5e9a5c00",
            target=target,
            extranonce1=self.extranonce1,
            extranonce2_size=self.extranonce2_size,
            stratum_version=self.stratum_version,
        )
        self.current_jobs[job.job_id] = job
        self.jobs_received += 1
        self.last_job_received_at = job.received_timestamp
        self.active_job_id = job.job_id
        self._persist_metrics()
        return job

    def validate_and_record_share(self, job: MiningJob, nonce: int, extranonce2: str) -> ShareResult:
        from pythia_mining.mining_validation import validate_share
        validation = validate_share(job, nonce, extranonce2)
        self.shares_submitted += 1
        self.last_share_submit_at = time.time()
        if validation.valid:
            self.shares_accepted += 1
            self.last_share_error = None
            self.audit_logger.log_share_accepted(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, block_hash=validation.block_hash)
            result = ShareResult(True, job_id=job.job_id, nonce=nonce, block_hash=validation.block_hash, target=validation.target)
        else:
            self.shares_rejected += 1
            self.last_share_error = validation.reason
            self.audit_logger.log_share_rejected(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, reason=validation.reason, error_code=1)
            result = ShareResult(False, 1, validation.reason, job.job_id, nonce, validation.block_hash, validation.target)
        self.metrics_store.record_share_submission(pool_name=self.pool_name, pool_url=self.pool_url, job_id=job.job_id, nonce=nonce, accepted=result.accepted, error_code=result.error_code, error_message=result.error_message, block_hash=result.block_hash, target=result.target)
        self._persist_metrics()
        return result

    def get_status(self) -> Dict[str, Any]:
        submitted = self.shares_submitted
        accepted = self.shares_accepted
        current_job = self.current_jobs.get(self.active_job_id) if self.active_job_id else None
        return {
            "pool_name": self.pool_name,
            "pool_url": self.pool_url,
            "stratum_version": self.stratum_version,
            "connection_state": self.connection_state,
            "is_connected": self.is_connected,
            "is_authenticated": self.is_authenticated,
            "current_difficulty": self.current_difficulty,
            "current_jobs_count": len(self.current_jobs),
            "active_job_id": self.active_job_id,
            "last_job_received_at": self.last_job_received_at,
            "last_pool_event_at": self.last_pool_event_at,
            "last_share_submit_at": self.last_share_submit_at,
            "last_share_error": self.last_share_error,
            "current_job": current_job.to_dict() if current_job else None,
            "performance": {
                "latency_ms": self.avg_latency,
                "shares_submitted": submitted,
                "shares_accepted": accepted,
                "shares_rejected": self.shares_rejected,
                "jobs_received": self.jobs_received,
                "acceptance_rate": accepted / max(submitted, 1),
            },
        }


class PoolManager:
    def __init__(self, pools_config: Optional[Dict[str, Any]] = None):
        from pythia_mining.pool_profiles import load_pool_profiles
        profiles = _profiles_from_legacy_config(pools_config or {}) if pools_config else load_pool_profiles()
        if _is_production() and not profiles:
            raise ProductionConfigurationError("Production mining requires at least one HYBA_POOL_<ID>_* configuration")
        self.pools: Dict[str, StratumClient] = {
            profile.pool_id: StratumClient(
                pool_url=profile.url,
                username=profile.username,
                password=profile.password,
                pool_name=profile.name,
                stratum_version=profile.stratum_version,
            )
            for profile in profiles
        }
        if not self.pools:
            self.pools = {
                "dev": StratumClient(
                    pool_url="stratum+tcp://localhost:3333",
                    username="dev.worker",
                    password="dev",
                    pool_name="Development Fixture Pool",
                    stratum_version=1,
                )
            }
        self.current_pool_key: Optional[str] = None

    async def get_best_pool(self) -> StratumClient:
        if self.current_pool_key and self.current_pool_key in self.pools:
            current = self.pools[self.current_pool_key]
            if current.is_connected and current.is_authenticated:
                return current
        for pool_id, pool in self.pools.items():
            if pool.is_connected and pool.is_authenticated:
                self.current_pool_key = pool_id
                return pool
        failures: list[str] = []
        for pool_id, pool in self.pools.items():
            if await pool.connect():
                self.current_pool_key = pool_id
                return pool
            failures.append(f"{pool.pool_name}: {pool.connection_state}")
        self.current_pool_key = None
        raise AllPoolsOfflineError("All configured mining pools are offline or unauthenticated: " + "; ".join(failures))

    def get_active_pool(self) -> Optional[StratumClient]:
        if self.current_pool_key and self.current_pool_key in self.pools:
            return self.pools[self.current_pool_key]
        return next(iter(self.pools.values()), None)

    def get_all_pools_status(self) -> List[Dict[str, Any]]:
        statuses: List[Dict[str, Any]] = []
        for pool_id, pool in self.pools.items():
            payload = pool.get_status()
            payload["pool_id"] = pool_id
            payload["is_active"] = self.current_pool_key == pool_id
            statuses.append(payload)
        return statuses

    async def disconnect_all(self):
        for pool in self.pools.values():
            await pool.disconnect()
        self.current_pool_key = None


__all__ = [
    "MiningJob",
    "ShareResult",
    "StratumClient",
    "PoolManager",
    "AllPoolsOfflineError",
    "ProductionConfigurationError",
    "_difficulty_to_target",
]
