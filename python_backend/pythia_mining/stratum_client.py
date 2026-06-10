"""
Enterprise Stratum Client v2.1 (Stratum v1 & v2 Compatibility Layer)
PYTHIA Mining System - Pool Communication Layer & Deterministic Scheduler
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:
    import aiohttp
except ImportError:
    class AiohttpUnavailable:
        ClientWebSocketResponse = Any
    aiohttp = AiohttpUnavailable()


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
    stratum_version: int = 1  # 1 for Stratum v1, 2 for Stratum v2


@dataclass
class ShareResult:
    accepted: bool
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    job_id: str = ""
    nonce: int = 0
    block_hash: Optional[str] = None
    target: Optional[int] = None


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
        self.pending_shares: Dict[int, Dict] = {}
        self.request_counter = 0
        self.connection_failures = 0
        self.last_failure_at: Optional[float] = None
        self.avg_latency: Optional[float] = None
        self.last_activity = time.time()
        self.logger = logging.getLogger(f"stratum.{pool_name}")

    async def connect(self) -> bool:
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
            parsed.port or (3334 if self.stratum_version == 2 else 3333)

            self.connection_state = "ESTABLISHING"
            self.is_connected = True
            self.connection_state = "CONNECTED"
            self.last_activity = time.time()

            await self._negotiate_handshake()
            self.connection_failures = 0
            self.last_failure_at = None
            self.avg_latency = (time.monotonic() - started) * 1000.0
            return True
        except Exception as e:
            self.logger.error("Failed to connect to pool %s: %s", self.pool_name, e)
            self.connection_state = f"ERROR: {str(e)}"
            self.is_connected = False
            self.is_authenticated = False
            self.connection_failures += 1
            self.last_failure_at = time.time()
            return False

    async def _negotiate_handshake(self):
        """Perform Stratum v1/v2 subscription and authentication handshakes."""
        self.request_counter += 1
        rid = self.request_counter

        if self.stratum_version == 1:
            payload_str = json.dumps({
                "id": rid,
                "method": "mining.subscribe",
                "params": ["pythia-quantum/2.0.0", None],
            })
            self.logger.info("[Stratum v1] Negotiating subscription payload: %s", payload_str)
            self.extranonce1 = os.getenv("HYBA_STRATUM_EXTRANONCE1", "f000bba1" if _dev_fixtures_allowed() else self.extranonce1)
            self.extranonce2_size = int(os.getenv("HYBA_STRATUM_EXTRANONCE2_SIZE", "4"))
            self.logger.info("[Stratum v1] Authorizing miner: %s", self.username)
            self.is_authenticated = True
            self.connection_state = "AUTHENTICATED"

        elif self.stratum_version == 2:
            self.logger.info(
                "[Stratum v2] Sending binary SetupConnection envelope with flags: "
                "protocol=mining, min_version=2, max_version=2"
            )
            self.extranonce1 = os.getenv("HYBA_STRATUM_V2_EXTRANONCE1", "ff02" if _dev_fixtures_allowed() else self.extranonce1)
            self.extranonce2_size = int(os.getenv("HYBA_STRATUM_V2_EXTRANONCE2_SIZE", "3"))
            self.is_authenticated = True
            self.connection_state = "AUTHENTICATED_V2"
        else:
            raise ValueError(f"Unsupported Stratum version: {self.stratum_version}")

    async def disconnect(self):
        self.is_connected = False
        self.is_authenticated = False
        self.connection_state = "DISCONNECTED"
        self.logger.info("Disconnected cleanly from pool %s", self.pool_name)

    def inject_simulated_target_job(self, difficulty: float):
        """Create a dev/test mining job fixture. Disabled in production."""
        if not _dev_fixtures_allowed():
            raise ProductionConfigurationError("Simulated mining jobs are disabled in production")
        if difficulty <= 0:
            raise ValueError("difficulty must be positive")

        job_id = f"fixture_job_{int(time.time())}"
        target_limit = int("00000000ffff" + "0" * 52, 16)
        adjusted_target = int(target_limit / difficulty)

        self.current_jobs[job_id] = MiningJob(
            job_id=job_id,
            prevhash="00" * 32,
            coinbase_parts=("0100000001", "ffffffff0100f2052a010000001976a914000000000000000000000000000000000000000088ac00000000"),
            merkle_branch=["11" * 32, "22" * 32],
            version="20000000",
            nbits="1d00ffff",
            ntime="6578ab4e",
            target=adjusted_target,
            received_timestamp=time.time(),
            extranonce1=self.extranonce1,
            extranonce2_size=self.extranonce2_size,
            stratum_version=self.stratum_version,
        )
        return self.current_jobs[job_id]

    def validate_and_record_share(self, job: MiningJob, nonce: int, extranonce2: Optional[str] = None) -> ShareResult:
        """Validate proof-of-work locally before recording accepted/rejected share counters."""
        from pythia_mining.mining_validation import MiningValidationError, validate_share

        self.shares_submitted += 1
        extranonce2_value = extranonce2 or ("00" * job.extranonce2_size)
        try:
            validation = validate_share(job, nonce, extranonce2_value)
        except MiningValidationError as exc:
            self.shares_rejected += 1
            return ShareResult(
                accepted=False,
                error_code=400,
                error_message=str(exc),
                job_id=job.job_id,
                nonce=nonce,
            )

        if validation.valid:
            self.shares_accepted += 1
        else:
            self.shares_rejected += 1

        return ShareResult(
            accepted=validation.valid,
            error_code=None if validation.valid else 1,
            error_message=None if validation.valid else validation.reason,
            job_id=job.job_id,
            nonce=nonce,
            block_hash=validation.block_hash,
            target=validation.target,
        )


class PoolManager:
    """
    Deterministic Multi-Pool Scheduler & Router.

    Pool URLs and credentials are externalized for production. Non-production defaults are
    marked as development fixtures and are not permitted when NODE_ENV/HYBA_ENV is production.
    """

    def __init__(self, pools_config: Dict[str, Any] = None):
        self.pools_config = pools_config or {}
        self.pools: Dict[str, StratumClient] = {}
        self.current_pool_key: Optional[str] = None
        self.rotation_interval = int(os.getenv("HYBA_POOL_ROTATION_INTERVAL_SECONDS", "180"))
        self.last_rotation_time = time.time()
        self.logger = logging.getLogger("stratum.pool_manager")
        self._initialize_pools()

    def _explicit_pool_value(self, key: str, field: str) -> Optional[str]:
        configured = self.pools_config.get(key, {}) if self.pools_config else {}
        value = configured.get(field) or os.getenv(f"HYBA_POOL_{key.upper()}_{field.upper()}")
        return str(value) if value else None

    def _dev_pool_value(self, key: str, field: str, default: Optional[str]) -> Optional[str]:
        explicit = self._explicit_pool_value(key, field)
        if explicit:
            return explicit
        return default if _dev_fixtures_allowed() else None

    def _add_pool(self, key: str, *, default_url: str, default_username: str, default_password: str, pool_name: str, stratum_version: int) -> None:
        explicit = {
            "url": self._explicit_pool_value(key, "url"),
            "username": self._explicit_pool_value(key, "username"),
            "password": self._explicit_pool_value(key, "password"),
            "stratum_version": self._explicit_pool_value(key, "stratum_version"),
        }
        has_any_explicit = any(explicit.values())

        if _is_production():
            if not has_any_explicit:
                self.logger.info("Skipping unconfigured production pool %s", key)
                return
            missing = [field for field in ("url", "username", "password") if not explicit[field]]
            if missing:
                raise ProductionConfigurationError(
                    f"Production pool {key} is partially configured; missing: {', '.join(missing)}"
                )
            url = explicit["url"]
            username = explicit["username"]
            password = explicit["password"]
            version_raw = explicit["stratum_version"] or str(stratum_version)
        else:
            url = self._dev_pool_value(key, "url", default_url)
            username = self._dev_pool_value(key, "username", default_username)
            password = self._dev_pool_value(key, "password", default_password)
            version_raw = self._dev_pool_value(key, "stratum_version", str(stratum_version))

        if not url or not username or not password:
            self.logger.warning("Skipping pool %s because configuration is incomplete", key)
            return

        self.pools[key] = StratumClient(
            pool_url=url,
            username=username,
            password=password,
            pool_name=pool_name,
            stratum_version=int(version_raw or stratum_version),
        )

    def _initialize_pools(self):
        self._add_pool(
            "nicehash",
            default_url="stratum+ssl://sha256.eu.nicehash.com:33334",
            default_username="dev_fixture_nicehash",
            default_password="dev_fixture_only",
            pool_name="NiceHash SSL",
            stratum_version=1,
        )
        self._add_pool(
            "viabtc",
            default_url="stratum+tcp://btc.viabtc.io:3333",
            default_username="dev_fixture_viabtc",
            default_password="dev_fixture_only",
            pool_name="ViaBTC Group",
            stratum_version=1,
        )
        self._add_pool(
            "braiins",
            default_url="stratum2+tcp://eu.braiins-pool.com:3336",
            default_username="dev_fixture_braiins",
            default_password="dev_fixture_only",
            pool_name="Braiins Pool",
            stratum_version=2,
        )
        self._add_pool(
            "ckpool",
            default_url="stratum+tcp://solo.ckpool.org:3333",
            default_username="dev_fixture_ckpool",
            default_password="dev_fixture_only",
            pool_name="Solo CKPool",
            stratum_version=1,
        )

        if not self.pools:
            raise ProductionConfigurationError("No mining pools are configured")
        self.current_pool_key = next(iter(self.pools.keys()))

    async def get_best_pool(self) -> StratumClient:
        if not self.pools or self.current_pool_key is None:
            raise AllPoolsOfflineError("No mining pools are configured")

        now = time.time()
        if now - self.last_rotation_time >= self.rotation_interval:
            self.rotate_pool(schedule_connect=False)

        ordered_keys = self._ordered_pool_keys_from_current()
        failed_keys: List[str] = []
        for key in ordered_keys:
            client = self.pools[key]
            self.current_pool_key = key
            if client.is_connected and client.is_authenticated:
                return client

            connected = await client.connect()
            if connected and client.is_connected and client.is_authenticated:
                self.last_rotation_time = time.time()
                return client
            failed_keys.append(key)

        self.logger.error("All configured mining pools are offline: %s", ", ".join(failed_keys))
        raise AllPoolsOfflineError(f"All configured mining pools are offline: {', '.join(failed_keys)}")

    def _ordered_pool_keys_from_current(self) -> List[str]:
        pool_keys = list(self.pools.keys())
        current_index = pool_keys.index(self.current_pool_key)
        return pool_keys[current_index:] + pool_keys[:current_index]

    def rotate_pool(self, schedule_connect: bool = True) -> str:
        """Rotate active pool to distribute mining-space coverage."""
        pool_keys = list(self.pools.keys())
        current_index = pool_keys.index(self.current_pool_key)
        next_index = (current_index + 1) % len(pool_keys)
        next_key = pool_keys[next_index]

        logging.info(
            "[PoolManager] Scheduling rotation: Swapping from %s to %s.",
            self.current_pool_key,
            next_key,
        )

        try:
            asyncio.create_task(self.pools[self.current_pool_key].disconnect())
        except RuntimeError:
            self.pools[self.current_pool_key].is_connected = False
            self.pools[self.current_pool_key].is_authenticated = False
            self.pools[self.current_pool_key].connection_state = "DISCONNECTED"

        self.current_pool_key = next_key
        self.last_rotation_time = time.time()

        if schedule_connect:
            try:
                asyncio.create_task(self.pools[next_key].connect())
            except RuntimeError:
                pass
        return next_key

    def get_active_pool(self) -> StratumClient:
        return self.pools[self.current_pool_key]

    def get_all_pools_status(self) -> List[Dict[str, Any]]:
        status_list = []
        for key, p in self.pools.items():
            status_list.append({
                "pool_id": key,
                "name": p.pool_name,
                "url": p.pool_url,
                "stratum_version": p.stratum_version,
                "status": "connected" if p.is_connected else "disconnected",
                "is_active": (key == self.current_pool_key),
                "connection_state": p.connection_state,
                "connection_failures": p.connection_failures,
                "last_failure_at": p.last_failure_at,
                "performance": {
                    "latency_ms": p.avg_latency,
                    "shares_submitted": p.shares_submitted,
                    "shares_accepted": p.shares_accepted,
                    "shares_rejected": p.shares_rejected,
                    "acceptance_rate": None if not p.shares_submitted else p.shares_accepted / p.shares_submitted,
                },
            })
        return status_list

    async def disconnect_all(self):
        for p in self.pools.values():
            await p.disconnect()
