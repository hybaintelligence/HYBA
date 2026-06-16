"""
Enterprise Stratum Client v2.2 (Stratum v1 & v2 Compatibility Layer)
PYTHIA Mining System - Pool Communication Layer & Deterministic Scheduler
"""

from __future__ import annotations

import asyncio
import hashlib
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
from pythia_mining.live_stratum_session import (
    LiveStratumSession,
    LiveStratumSessionError,
)
from pythia_mining.live_stratum_v2_session import (
    LiveStratumV2Session,
    LiveStratumV2SessionError,
)
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

    def __init__(
        self,
        pool_url: str,
        username: str,
        password: str,
        pool_name: str,
        stratum_version: int = 1,
        max_reconnect_attempts: int = 10,
        max_share_retry_attempts: int = 3,
        reconnect_backoff_base: float = 1.0,
        reconnect_backoff_max: float = 60.0,
        share_retry_backoff_base: float = 0.5,
        share_retry_backoff_max: float = 5.0,
    ):
        if _is_production() and (not username or not password):
            raise ProductionConfigurationError(
                f"Missing production credentials for pool {pool_name}"
            )

        self.pool_url = pool_url
        self.username = username
        self.password = password
        self.pool_name = pool_name
        self.stratum_version = stratum_version
        self.max_reconnect_attempts = max_reconnect_attempts
        self.max_share_retry_attempts = max_share_retry_attempts
        self.reconnect_backoff_base = reconnect_backoff_base
        self.reconnect_backoff_max = reconnect_backoff_max
        self.share_retry_backoff_base = share_retry_backoff_base
        self.share_retry_backoff_max = share_retry_backoff_max

        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.live_session: Optional[Any] = None
        self.is_connected = False
        self.is_authenticated = False
        self.connection_state = "DISCONNECTED"
        self._jobs_lock = asyncio.Lock()
        self._metrics_lock = asyncio.Lock()
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
        self._blockchain_oracle = None
        self._last_block_height_check: float = 0
        self._block_height_check_interval: float = 30.0

        # Circuit breaker state
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure: float = 0
        self._circuit_breaker_state = "closed"  # closed, open, half_open
        self._circuit_breaker_threshold = 5  # failures before opening
        self._circuit_breaker_timeout = 60.0  # seconds to stay open
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
        self.heartbeat_interval = 60.0
        self.idle_timeout = 120.0
        self._heartbeat_task: Optional[asyncio.Task] = None
        self.share_retry_attempts = 0
        self.logger = logging.getLogger(f"stratum.{pool_name}")
        self.audit_logger = get_audit_logger()
        self.metrics_store = get_metrics_store()

    def _calculate_backoff_delay(self) -> float:
        delay = min(
            self.reconnect_backoff_base * (2**self.reconnect_attempts),
            self.reconnect_backoff_max,
        )
        jitter_material = f"{self.pool_name}:{self.pool_url}:{self.reconnect_attempts}".encode(
            "utf-8"
        )
        jitter_unit = (
            int.from_bytes(hashlib.blake2b(jitter_material, digest_size=2).digest(), "big")
            / 65535.0
        )
        return delay + (delay * 0.1 * jitter_unit)

    def _circuit_breaker_allow_request(self) -> bool:
        """Check if circuit breaker allows connection attempts."""
        now = time.time()

        if self._circuit_breaker_state == "open":
            # Check if timeout has elapsed
            if now - self._circuit_breaker_last_failure > self._circuit_breaker_timeout:
                self._circuit_breaker_state = "half_open"
                self.logger.info(
                    "Circuit breaker transitioning to half-open state for pool %s",
                    self.pool_name,
                )
                return True
            return False

        return True

    def _circuit_breaker_record_success(self) -> None:
        """Record successful connection and reset circuit breaker."""
        if self._circuit_breaker_state == "half_open":
            self._circuit_breaker_state = "closed"
            self.logger.info(
                "Circuit breaker closed for pool %s after successful connection",
                self.pool_name,
            )
        self._circuit_breaker_failures = 0

    def _circuit_breaker_record_failure(self) -> None:
        """Record failed connection and potentially open circuit breaker."""
        self._circuit_breaker_failures += 1
        self._circuit_breaker_last_failure = time.time()

        if self._circuit_breaker_failures >= self._circuit_breaker_threshold:
            self._circuit_breaker_state = "open"
            self.logger.warning(
                "Circuit breaker opened for pool %s after %s failures",
                self.pool_name,
                self._circuit_breaker_failures,
            )

    async def connect(self) -> bool:
        # Check circuit breaker before attempting connection
        if not self._circuit_breaker_allow_request():
            self.logger.warning(
                "Circuit breaker is open for pool %s, rejecting connection attempt",
                self.pool_name,
            )
            self.connection_state = "CIRCUIT_OPEN"
            return False

        self.audit_logger.log_connection_attempt(
            pool_name=self.pool_name,
            pool_url=self.pool_url,
            stratum_version=self.stratum_version,
            attempt_number=self.reconnect_attempts + 1,
        )
        self.logger.info(
            "Connecting via Stratum v%s to pool %s (%s)",
            self.stratum_version,
            self.pool_name,
            self.pool_url,
        )
        self.connection_state = "CONNECTING"
        started = time.monotonic()
        try:
            parsed = urlparse(self.pool_url)
            if not parsed.scheme or not parsed.hostname:
                raise ValueError(f"Invalid pool URL: {self.pool_url}")
            if parsed.port is None:
                default_port = 3334 if self.stratum_version == 2 else 3333
                self.pool_url = (
                    f"{parsed.scheme}://{parsed.hostname}:{default_port}{parsed.path or ''}"
                )

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
            self._circuit_breaker_record_success()
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
            await self._persist_metrics()
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
            self._circuit_breaker_record_failure()
            await self._close_live_session()
            await self._persist_metrics()
            if isinstance(
                e,
                (
                    ValueError,
                    ProductionConfigurationError,
                    LiveStratumSessionError,
                    LiveStratumV2SessionError,
                ),
            ):
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
                self.logger.info(
                    "Reconnection attempt %s/%s for pool %s in %.2f seconds",
                    self.reconnect_attempts + 1,
                    self.max_reconnect_attempts,
                    self.pool_name,
                    delay,
                )
                await asyncio.sleep(delay)
                return await self.connect()
            return False

    async def _persist_metrics(self) -> None:
        async with self._metrics_lock:
            acceptance_rate = (
                self.shares_accepted / self.shares_submitted if self.shares_submitted > 0 else 0.0
            )
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
            if not hasattr(self.live_session, "read_event"):
                break
            try:
                await asyncio.sleep(self.heartbeat_interval)
                idle_time = time.time() - self.last_activity
                if idle_time > self.idle_timeout:
                    try:
                        event, _payload = await self.live_session.read_event(timeout=5.0)
                        if event:
                            self.last_activity = time.time()
                            self.last_pool_event_at = self.last_activity
                    except (
                        asyncio.TimeoutError,
                        StratumTransportError,
                        LiveStratumSessionError,
                    ):
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
        self.audit_logger.log_handshake_start(
            pool_name=self.pool_name, pool_url=self.pool_url, username=self.username
        )
        profile = build_profile(
            self.pool_name.lower().replace(" ", "_"),
            name=self.pool_name,
            url=self.pool_url,
            username=self.username,
            password=self.password,
            stratum_version=self.stratum_version,
            tls_required=urlparse(self.pool_url).scheme
            in {"stratum+ssl", "stratum+tls", "stratum2+ssl", "stratum2+tls"},
        )
        if self.stratum_version == 1:
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
                self.audit_logger.log_handshake_success(
                    pool_name=self.pool_name,
                    pool_url=self.pool_url,
                    extranonce1=self.extranonce1,
                    extranonce2_size=self.extranonce2_size,
                )
            else:
                self.audit_logger.log_handshake_failure(
                    pool_name=self.pool_name,
                    pool_url=self.pool_url,
                    error="Authorization rejected by pool",
                )
        elif self.stratum_version == 2:
            v2_session = LiveStratumV2Session(profile)
            self.live_session = v2_session
            await v2_session.connect()
            self.is_connected = True
            self.connection_state = "CONNECTED_V2"
            handshake = await v2_session.setup_connection()
            self.is_authenticated = True
            self.connection_state = "SETUP_CONNECTION_SUCCESS_V2"
            self.audit_logger.log_handshake_success(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                extranonce1=f"sv2-version-{handshake.used_version}",
                extranonce2_size=0,
            )
        else:
            raise LiveStratumSessionError(
                f"unsupported live Stratum version: {self.stratum_version}"
            )
        self.last_activity = time.time()

    async def _connect_development_fixture(self) -> None:
        self.is_connected = True
        self.connection_state = "CONNECTED"
        self.last_activity = time.time()
        await self._negotiate_fixture_handshake()

    async def _negotiate_fixture_handshake(self):
        if not _dev_fixtures_allowed():
            raise ProductionConfigurationError(
                "development Stratum fixtures are disabled in production"
            )
        self.request_counter += 1
        rid = self.request_counter
        if self.stratum_version == 1:
            self.logger.info(
                "[Stratum v1 fixture] Subscription payload: %s",
                json.dumps(
                    {
                        "id": rid,
                        "method": "mining.subscribe",
                        "params": ["pythia-quantum/2.0.0", None],
                    }
                ),
            )
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
        if self.live_session is None or not hasattr(self.live_session, "read_event"):
            return None
        try:
            event, payload = await self.live_session.read_event(timeout=timeout)
        except (asyncio.TimeoutError, StratumTransportError):
            # Check for stale jobs based on block height even on timeout
            await self._check_block_height_for_stale_jobs()
            return None
        self.last_activity = time.time()
        self.last_pool_event_at = self.last_activity

        # Check for stale jobs based on block height on successful event read
        await self._check_block_height_for_stale_jobs()
        if event == "mining.set_difficulty":
            old_difficulty = self.current_difficulty
            self.current_difficulty = float(payload.difficulty)
            self.audit_logger.log_difficulty_change(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                old_difficulty=old_difficulty,
                new_difficulty=self.current_difficulty,
            )
            await self._persist_metrics()
            return None
        if event == "mining.notify":
            async with self._jobs_lock:
                if payload.clean_jobs:
                    for job_id in self.current_jobs:
                        self.stale_job_ids.add(job_id)
                        self.audit_logger.log_job_stale(
                            pool_name=self.pool_name,
                            pool_url=self.pool_url,
                            job_id=job_id,
                        )
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
                self.audit_logger.log_job_received(
                    pool_name=self.pool_name,
                    pool_url=self.pool_url,
                    job_id=job.job_id,
                    clean_jobs=payload.clean_jobs,
                    difficulty=self.current_difficulty,
                )
                await self._persist_metrics()
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
            self.logger.warning(
                "Pool %s sent unsupported message: method=%s",
                self.pool_name,
                payload.get("method"),
            )
            return None
        return None

    def _validate_pool_response(self, response: Dict[str, Any]) -> bool:
        """Validate pool response structure before processing."""
        if not isinstance(response, dict):
            return False
        if "id" not in response:
            return False
        if "result" not in response and "error" not in response:
            return False
        if "error" in response and response["error"] is not None:
            if not isinstance(response["error"], (list, str)):
                return False
        return True

    async def submit_validated_share(
        self, job: MiningJob, nonce: int, extranonce2: Optional[str] = None
    ) -> ShareResult:
        """Validate locally, then submit to the pool before recording accepted/rejected counters."""
        from pythia_mining.mining_validation import (
            MiningValidationError,
            validate_share,
        )

        if job.job_id in self.stale_job_ids or job.is_stale:
            self.shares_submitted += 1
            self.shares_rejected += 1
            self.last_share_error = "stale_job"
            self.audit_logger.log_share_rejected(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                job_id=job.job_id,
                nonce=nonce,
                reason="stale_job",
                error_code=410,
            )
            self.metrics_store.record_share_submission(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                job_id=job.job_id,
                nonce=nonce,
                accepted=False,
                error_code=410,
                error_message="stale_job",
            )
            await self._persist_metrics()
            return ShareResult(False, 410, "stale_job", job.job_id, nonce)

        extranonce2_value = extranonce2 or ("00" * job.extranonce2_size)
        if self.live_session is not None and not _live_share_submit_enabled():
            self.audit_logger.log_share_rejected(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                job_id=job.job_id,
                nonce=nonce,
                reason="live_share_submit_disabled",
                error_code=423,
            )
            self.shares_submitted += 1
            self.shares_rejected += 1
            self.last_share_error = "live_share_submit_disabled"
            self.metrics_store.record_share_submission(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                job_id=job.job_id,
                nonce=nonce,
                accepted=False,
                error_code=423,
                error_message="live_share_submit_disabled",
            )
            await self._persist_metrics()
            return ShareResult(False, 423, "live_share_submit_disabled", job.job_id, nonce)

        try:
            validation = validate_share(job, nonce, extranonce2_value)
        except MiningValidationError as exc:
            self.audit_logger.log_share_validation_error(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                job_id=job.job_id,
                nonce=nonce,
                error=str(exc),
            )
            self.shares_submitted += 1
            self.shares_rejected += 1
            self.last_share_error = str(exc)
            self.metrics_store.record_share_submission(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                job_id=job.job_id,
                nonce=nonce,
                accepted=False,
                error_code=400,
                error_message=str(exc),
            )
            await self._persist_metrics()
            return ShareResult(False, 400, str(exc), job.job_id, nonce)

        if not validation.valid:
            self.audit_logger.log_share_rejected(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                job_id=job.job_id,
                nonce=nonce,
                reason=validation.reason,
                error_code=1,
            )
            self.shares_submitted += 1
            self.shares_rejected += 1
            self.last_share_error = validation.reason
            self.metrics_store.record_share_submission(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                job_id=job.job_id,
                nonce=nonce,
                accepted=False,
                error_code=1,
                error_message=validation.reason,
                block_hash=validation.block_hash,
                target=validation.target,
            )
            await self._persist_metrics()
            return ShareResult(
                False,
                1,
                validation.reason,
                job.job_id,
                nonce,
                validation.block_hash,
                validation.target,
            )

        if self.live_session is None:
            return await self.validate_and_record_share(job, nonce, extranonce2_value)

        self.shares_submitted += 1
        self.last_share_submit_at = time.time()
        nonce_hex = nonce.to_bytes(4, byteorder="little", signed=False).hex()
        self.audit_logger.log_share_submission(
            pool_name=self.pool_name,
            pool_url=self.pool_url,
            job_id=job.job_id,
            nonce=nonce,
            extranonce2=extranonce2_value,
        )

        submit_result = None
        last_exception = None
        for attempt in range(self.max_share_retry_attempts):
            try:
                submit_result = await self.live_session.submit_share(
                    job_id=job.job_id,
                    extranonce2=extranonce2_value,
                    ntime=job.ntime,
                    nonce=nonce_hex,
                )
                # Validate pool response structure
                if not self._validate_pool_response(submit_result.response):
                    self.logger.warning(
                        "Pool %s returned invalid response structure on attempt %s",
                        self.pool_name,
                        attempt + 1,
                    )
                    if attempt < self.max_share_retry_attempts - 1:
                        await asyncio.sleep(
                            min(
                                self.share_retry_backoff_base * (2**attempt),
                                self.share_retry_backoff_max,
                            )
                        )
                        continue
                    else:
                        self.audit_logger.log_share_rejected(
                            pool_name=self.pool_name,
                            pool_url=self.pool_url,
                            job_id=job.job_id,
                            nonce=nonce,
                            reason="invalid_pool_response_structure",
                            error_code=503,
                        )
                        self.shares_rejected += 1
                        self.last_share_error = "invalid_pool_response_structure"
                        self.metrics_store.record_share_submission(
                            pool_name=self.pool_name,
                            pool_url=self.pool_url,
                            job_id=job.job_id,
                            nonce=nonce,
                            accepted=False,
                            error_code=503,
                            error_message="invalid_pool_response_structure",
                            block_hash=validation.block_hash,
                            target=validation.target,
                        )
                        await self._persist_metrics()
                        return ShareResult(
                            False,
                            503,
                            "invalid_pool_response_structure",
                            job.job_id,
                            nonce,
                            validation.block_hash,
                            validation.target,
                        )
                if submit_result.accepted:
                    break
                if not submit_result.accepted and submit_result.error:
                    break
            except Exception as exc:
                last_exception = exc
                if attempt < self.max_share_retry_attempts - 1:
                    await asyncio.sleep(
                        min(
                            self.share_retry_backoff_base * (2**attempt),
                            self.share_retry_backoff_max,
                        )
                    )
                else:
                    self.audit_logger.log_share_rejected(
                        pool_name=self.pool_name,
                        pool_url=self.pool_url,
                        job_id=job.job_id,
                        nonce=nonce,
                        reason=f"pool_submit_failed: {last_exception}",
                        error_code=502,
                    )
                    self.shares_rejected += 1
                    self.last_share_error = str(last_exception)
                    self.metrics_store.record_share_submission(
                        pool_name=self.pool_name,
                        pool_url=self.pool_url,
                        job_id=job.job_id,
                        nonce=nonce,
                        accepted=False,
                        error_code=502,
                        error_message=f"pool_submit_failed: {last_exception}",
                        block_hash=validation.block_hash,
                        target=validation.target,
                    )
                    await self._persist_metrics()
                    return ShareResult(
                        False,
                        502,
                        f"pool_submit_failed: {last_exception}",
                        job.job_id,
                        nonce,
                        validation.block_hash,
                        validation.target,
                    )

        if submit_result is None:
            self.shares_rejected += 1
            self.last_share_error = "pool_submit_no_response"
            self.metrics_store.record_share_submission(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                job_id=job.job_id,
                nonce=nonce,
                accepted=False,
                error_code=502,
                error_message="pool_submit_no_response",
                block_hash=validation.block_hash,
                target=validation.target,
            )
            await self._persist_metrics()
            return ShareResult(
                False,
                502,
                "pool_submit_no_response",
                job.job_id,
                nonce,
                validation.block_hash,
                validation.target,
            )

        if submit_result.accepted:
            self.audit_logger.log_share_accepted(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                job_id=job.job_id,
                nonce=nonce,
                block_hash=validation.block_hash,
            )
            self.metrics_store.record_share_submission(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                job_id=job.job_id,
                nonce=nonce,
                accepted=True,
                block_hash=validation.block_hash,
                target=validation.target,
            )
            self.shares_accepted += 1
            self.last_share_error = None
        else:
            self.audit_logger.log_share_rejected(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                job_id=job.job_id,
                nonce=nonce,
                reason=str(submit_result.error),
                error_code=2,
            )
            self.metrics_store.record_share_submission(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                job_id=job.job_id,
                nonce=nonce,
                accepted=False,
                error_code=2,
                error_message=str(submit_result.error),
                block_hash=validation.block_hash,
                target=validation.target,
            )
            self.shares_rejected += 1
            self.last_share_error = str(submit_result.error)
        await self._persist_metrics()
        return ShareResult(
            submit_result.accepted,
            None if submit_result.accepted else 2,
            None if submit_result.accepted else str(submit_result.error),
            job.job_id,
            nonce,
            validation.block_hash,
            validation.target,
        )

    async def _close_live_session(self) -> None:
        if self.live_session is not None:
            try:
                await self.live_session.close()
            except (
                LiveStratumSessionError,
                LiveStratumV2SessionError,
                StratumTransportError,
                OSError,
            ):
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
        self.audit_logger.log_event(
            AuditEvent(
                AuditEventType.DISCONNECTION,
                self.pool_name,
                self.pool_url,
                time.time(),
                {},
                "INFO",
            )
        )
        self.metrics_store.record_connection_event(
            pool_name=self.pool_name, pool_url=self.pool_url, event_type="disconnection"
        )
        await self._persist_metrics()

    async def close(self):
        """Alias for disconnect() for compatibility with cleanup patterns."""
        await self.disconnect()

    async def inject_dev_fixture_target_job(self, difficulty: float):
        """Create a dev/test mining job fixture. Disabled in production."""
        if not _dev_fixtures_allowed():
            raise ProductionConfigurationError("Dev fixture mining jobs are disabled in production")
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
        await self._persist_metrics()
        return job

    async def validate_and_record_share(
        self, job: MiningJob, nonce: int, extranonce2: str
    ) -> ShareResult:
        from pythia_mining.mining_validation import validate_share

        validation = validate_share(job, nonce, extranonce2)
        self.shares_submitted += 1
        self.last_share_submit_at = time.time()
        if validation.valid:
            self.shares_accepted += 1
            self.last_share_error = None
            self.audit_logger.log_share_accepted(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                job_id=job.job_id,
                nonce=nonce,
                block_hash=validation.block_hash,
            )
            result = ShareResult(
                True,
                job_id=job.job_id,
                nonce=nonce,
                block_hash=validation.block_hash,
                target=validation.target,
            )
        else:
            self.shares_rejected += 1
            self.last_share_error = validation.reason
            self.audit_logger.log_share_rejected(
                pool_name=self.pool_name,
                pool_url=self.pool_url,
                job_id=job.job_id,
                nonce=nonce,
                reason=validation.reason,
                error_code=1,
            )
            result = ShareResult(
                False,
                1,
                validation.reason,
                job.job_id,
                nonce,
                validation.block_hash,
                validation.target,
            )
        self.metrics_store.record_share_submission(
            pool_name=self.pool_name,
            pool_url=self.pool_url,
            job_id=job.job_id,
            nonce=nonce,
            accepted=result.accepted,
            error_code=result.error_code,
            error_message=result.error_message,
            block_hash=result.block_hash,
            target=result.target,
        )
        await self._persist_metrics()
        return result

    async def get_current_jobs_copy(self) -> Dict[str, MiningJob]:
        """Thread-safe copy of current jobs dict."""
        async with self._jobs_lock:
            return dict(self.current_jobs)

    async def get_active_job_copy(self) -> Optional[MiningJob]:
        """Thread-safe copy of active job."""
        async with self._jobs_lock:
            return self.current_jobs.get(self.active_job_id) if self.active_job_id else None

    async def _check_block_height_for_stale_jobs(self) -> None:
        """Proactively check for stale jobs based on block height changes."""
        if self._blockchain_oracle is None:
            try:
                from pythia_mining.blockchain_oracle import BlockchainOracle

                self._blockchain_oracle = BlockchainOracle()
            except ImportError:
                return

        now = time.time()
        if now - self._last_block_height_check < self._block_height_check_interval:
            return

        self._last_block_height_check = now
        try:
            current_tip = await self._blockchain_oracle.get_current_block_tip()
            if current_tip is None:
                return

            async with self._jobs_lock:
                jobs_to_mark_stale = []
                for job_id, job in self.current_jobs.items():
                    if self._blockchain_oracle.is_job_stale_by_block_height(
                        job.prevhash, current_tip
                    ):
                        jobs_to_mark_stale.append(job_id)

                for job_id in jobs_to_mark_stale:
                    if job_id not in self.stale_job_ids:
                        self.stale_job_ids.add(job_id)
                        self.audit_logger.log_job_stale(
                            pool_name=self.pool_name,
                            pool_url=self.pool_url,
                            job_id=job_id,
                        )
                        self.logger.info(
                            "Marked job %s as stale due to block height change (new tip: %s)",
                            job_id,
                            current_tip.hash[:16],
                        )

                if jobs_to_mark_stale:
                    await self._persist_metrics()
        except Exception as e:
            self.logger.error("Error checking block height for stale jobs: %s", e)

    def get_health_score(self) -> float:
        """Calculate pool health score for graceful degradation decisions (0.0 to 1.0)."""
        score = 1.0

        # Penalize for connection failures
        if self.connection_failures > 0:
            score -= min(0.3, self.connection_failures * 0.05)

        # Penalize for circuit breaker state
        if self._circuit_breaker_state == "open":
            score -= 0.5
        elif self._circuit_breaker_state == "half_open":
            score -= 0.2

        # Penalize for low acceptance rate
        if self.shares_submitted > 10:
            acceptance_rate = self.shares_accepted / self.shares_submitted
            if acceptance_rate < 0.9:
                score -= (0.9 - acceptance_rate) * 0.5

        # Penalize for high latency
        if self.avg_latency and self.avg_latency > 1000:  # > 1 second
            score -= min(0.2, (self.avg_latency - 1000) / 10000)

        # Penalize for stale jobs
        if len(self.stale_job_ids) > 0:
            score -= min(0.3, len(self.stale_job_ids) * 0.1)

        # Boost for recent activity
        if self.last_activity and (time.time() - self.last_activity) < 60:
            score += 0.1

        return max(0.0, min(1.0, score))

    def get_status(self) -> Dict[str, Any]:
        submitted = self.shares_submitted
        accepted = self.shares_accepted
        current_job = self.current_jobs.get(self.active_job_id) if self.active_job_id else None

        # Provide a precise reason when last_job is null instead of vague DEGRADED
        last_job_null_reason: str | None = None
        if current_job is None:
            if not self.is_connected:
                last_job_null_reason = "not_connected"
            elif not self.is_authenticated:
                last_job_null_reason = "not_authenticated"
            elif self.jobs_received == 0:
                last_job_null_reason = "no_job_received_since_connection"
            elif self.active_job_id and self.active_job_id not in self.current_jobs:
                last_job_null_reason = "active_job_id_not_in_current_jobs"
            else:
                last_job_null_reason = "unknown"

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
            "last_job_null_reason": last_job_null_reason,
            "health_score": self.get_health_score(),
            "circuit_breaker_state": self._circuit_breaker_state,
            "production_state": (
                "ready" if (
                    self.is_connected
                    and self.is_authenticated
                    and current_job is not None
                    and not current_job.is_stale
                )
                else "blocked"
            ),
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

        profiles = (
            _profiles_from_legacy_config(pools_config or {})
            if pools_config
            else load_pool_profiles()
        )
        if _is_production() and not profiles:
            raise ProductionConfigurationError(
                "Production mining requires at least one HYBA_POOL_<ID>_* configuration"
            )
        self.pools: Dict[str, StratumClient] = {
            profile.pool_id: StratumClient(
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
        """Get the best pool based on health score and connection status for graceful degradation."""
        # Check if current pool is healthy enough to continue using
        if self.current_pool_key and self.current_pool_key in self.pools:
            current = self.pools[self.current_pool_key]
            if current.is_connected and current.is_authenticated:
                health_score = current.get_health_score()
                # If current pool is healthy (score > 0.5), continue using it
                if health_score > 0.5:
                    return current
                # If current pool is degraded, try to find a healthier pool
                logger = logging.getLogger("pool_manager")
                logger.warning(
                    "Current pool %s has degraded health score %.2f, seeking better pool",
                    current.pool_name,
                    health_score,
                )

        # Find the best pool based on health score and connection status
        best_pool = None
        best_pool_key: Optional[str] = None
        best_score = -1.0

        # First, check already connected pools
        for pool_id, pool in self.pools.items():
            if pool.is_connected and pool.is_authenticated:
                health_score = pool.get_health_score()
                if health_score > best_score:
                    best_score = health_score
                    best_pool = pool
                    best_pool_key = pool_id
                    self.current_pool_key = pool_id

        if best_pool and best_score > 0.5:
            return best_pool

        # If no healthy connected pool, try to connect to the best available pool
        for pool_id, pool in self.pools.items():
            health_score = pool.get_health_score()
            if health_score > best_score and not pool.is_connected:
                best_score = health_score
                best_pool = pool
                best_pool_key = pool_id

        if best_pool and best_pool_key is not None:
            if await best_pool.connect():
                self.current_pool_key = best_pool_key
                return best_pool

        # Last resort: try all pools in order
        failures: list[str] = []
        for pool_id, pool in self.pools.items():
            if await pool.connect():
                self.current_pool_key = pool_id
                return pool
            failures.append(f"{pool.pool_name}: {pool.connection_state}")

        self.current_pool_key = None
        raise AllPoolsOfflineError(
            "All configured mining pools are offline or unauthenticated: " + "; ".join(failures)
        )

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
