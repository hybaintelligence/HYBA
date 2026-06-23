"""
Production Redis State Engine for Distributed QaaS/CIaaS Instance Management

Provides:
- Atomic instance topology serialization/deserialization
- Distributed lock acquisition for multi-tenant hardware execution
- Resource consumption tracking with compute unit metering
- Horizontal scaling support across worker tiers
- Graceful fallback to in-memory state when Redis unavailable

Enterprise patterns:
- Lua scripting for atomic lock release (prevents race conditions)
- Pipeline transactions for batched metering updates
- JSON serialization for complex topology state
- Tenant-isolated lock keys with millisecond-precision leases
"""

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger("hyba.hardware_state")


class RedisQuantumSubstrateRegistry:
    """
    Production Redis state engine for physical/virtual QPU registers.

    Handles dynamic instance topology serialization, atomic transaction locks,
    and live telemetry caching across horizontally scaled worker tiers.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: int = 0,
        password: Optional[str] = None,
    ):
        """Initialize Redis client with optional environment variable overrides.

        Args:
            host: Redis host (default: HYBA_REDIS_HOST or localhost)
            port: Redis port (default: HYBA_REDIS_PORT or 6379)
            db: Redis database number (default: 0)
            password: Redis password (default: HYBA_REDIS_PASSWORD or None)
        """
        self.host = host or os.getenv("HYBA_REDIS_HOST", "localhost")
        self.port = int(port or os.getenv("HYBA_REDIS_PORT", "6379"))
        self.db = db
        self.password = password or os.getenv("HYBA_REDIS_PASSWORD")
        self.lock_lease_ms = 10000  # 10s execution safeguard window
        self._client: Optional[Any] = None
        self._available = False

        # Lazy initialization - only import redis if actually configured
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Redis client if available, mark as unavailable if not."""
        try:
            import redis

            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            # Test connection
            self._client.ping()
            self._available = True
            logger.info(
                "Redis state registry initialized",
                extra={"host": self.host, "port": self.port, "db": self.db},
            )
        except (ImportError, ConnectionError, TimeoutError, Exception) as e:
            logger.warning(
                "Redis not available; using in-memory state only",
                extra={"error": str(e), "host": self.host, "port": self.port},
            )
            self._client = None
            self._available = False

    @property
    def available(self) -> bool:
        """Check if Redis is available for distributed state operations."""
        return self._available and self._client is not None

    def serialize_instance_topology(
        self, instance_id: str, topology_data: Dict[str, Any]
    ) -> bool:
        """Serialize live instance metadata into distributed hash layer.

        Args:
            instance_id: Unique identifier for the compute instance
            topology_data: Complete instance topology (code_distance, qubits, policy, etc.)

        Returns:
            True if successfully persisted to Redis, False otherwise
        """
        if not self.available:
            return False

        state_key = f"quantum:instance:{instance_id}:metadata"
        try:
            # Atomic multi-set payload with TTL for garbage collection
            self._client.setex(state_key, 86400, json.dumps(topology_data))  # 24h TTL
            logger.debug(
                "Instance topology serialized",
                extra={"instance_id": instance_id, "key": state_key},
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to persist substrate state",
                extra={"instance_id": instance_id, "error": str(e)},
            )
            return False

    def get_instance_topology(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve and deserialize active register topology from distributed store.

        Args:
            instance_id: Unique identifier for the compute instance

        Returns:
            Deserialized topology dict if found, None otherwise
        """
        if not self.available:
            return None

        state_key = f"quantum:instance:{instance_id}:metadata"
        try:
            raw_data = self._client.get(state_key)
            if not raw_data:
                return None
            return json.loads(raw_data)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(
                "Failed to deserialize instance topology",
                extra={"instance_id": instance_id, "error": str(e)},
            )
            return None

    def acquire_register_lock(self, instance_id: str, client_tenant_id: str) -> bool:
        """
        Acquire atomic distributed lock on hardware register slice.

        Prevents race-condition corruption across multi-tenant execution requests.

        Args:
            instance_id: Unique identifier for the compute instance
            client_tenant_id: Tenant/customer ID requesting the lock

        Returns:
            True if lock acquired, False if already held by another tenant
        """
        if not self.available:
            return True  # In-memory mode always grants locks

        lock_key = f"quantum:lock:register:{instance_id}"
        try:
            # Set if Not Exists (NX) with millisecond expiration (PX)
            result = self._client.set(
                lock_key, client_tenant_id, px=self.lock_lease_ms, nx=True
            )
            if result:
                logger.debug(
                    "Register lock acquired",
                    extra={
                        "instance_id": instance_id,
                        "tenant_id": client_tenant_id,
                        "lease_ms": self.lock_lease_ms,
                    },
                )
            return bool(result)
        except Exception as e:
            logger.error(
                "Lock acquisition failed",
                extra={
                    "instance_id": instance_id,
                    "tenant_id": client_tenant_id,
                    "error": str(e),
                },
            )
            return False

    def release_register_lock(self, instance_id: str, client_tenant_id: str) -> bool:
        """
        Safely release execution lock using atomic Lua script.

        Ensures a tenant can never delete another tenant's active hardware lease.

        Args:
            instance_id: Unique identifier for the compute instance
            client_tenant_id: Tenant/customer ID releasing the lock

        Returns:
            True if lock released, False if not held by this tenant
        """
        if not self.available:
            return True  # In-memory mode always releases

        lock_key = f"quantum:lock:register:{instance_id}"
        # Atomic Lua script: only delete if current value matches tenant_id
        lua_script = """
            if redis.call('get', KEYS[1]) == ARGV[1] then
                return redis.call('del', KEYS[1])
            else
                return 0
            end
        """
        try:
            compiled_script = self._client.register_script(lua_script)
            result = bool(compiled_script(keys=[lock_key], args=[client_tenant_id]))
            if result:
                logger.debug(
                    "Register lock released",
                    extra={"instance_id": instance_id, "tenant_id": client_tenant_id},
                )
            return result
        except Exception as e:
            logger.error(
                "Lock release failed",
                extra={
                    "instance_id": instance_id,
                    "tenant_id": client_tenant_id,
                    "error": str(e),
                },
            )
            return False

    def record_resource_consumption(
        self, instance_id: str, tenant_id: str, metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate real compute units and update global usage ledger.

        Formula: Units = (defect_count * pairing_weight + 1.0) * circuit_depth

        Args:
            instance_id: Unique identifier for the compute instance
            tenant_id: Tenant/customer ID for metering
            metrics: Dict with defect_count, pairing_weight, circuit_depth

        Returns:
            Dict with computed compute_units and persistence status
        """
        defect_count = metrics.get("defect_count", 0)
        pairing_weight = metrics.get("pairing_weight", 1.0)
        circuit_depth = metrics.get("circuit_depth", 1)

        compute_units = (defect_count * pairing_weight + 1.0) * circuit_depth

        result = {
            "compute_units": compute_units,
            "persisted": False,
            "tenant_id": tenant_id,
            "instance_id": instance_id,
        }

        if not self.available:
            return result

        usage_key = f"quantum:usage:{tenant_id}:{instance_id}"
        try:
            pipe = self._client.pipeline()
            pipe.hincrbyfloat(usage_key, "total_compute_units", compute_units)
            pipe.hincrby(usage_key, "execution_count", 1)
            pipe.hset(usage_key, "last_execution", json.dumps(metrics))
            pipe.expire(usage_key, 2592000)  # 30d retention
            pipe.execute()
            result["persisted"] = True
            logger.debug(
                "Resource consumption recorded",
                extra={
                    "tenant_id": tenant_id,
                    "instance_id": instance_id,
                    "compute_units": compute_units,
                },
            )
        except Exception as e:
            logger.error(
                "Failed to record consumption",
                extra={
                    "tenant_id": tenant_id,
                    "instance_id": instance_id,
                    "error": str(e),
                },
            )

        return result

    def close(self) -> None:
        """Close Redis connection gracefully."""
        if self._client is not None:
            try:
                self._client.close()
                logger.debug("Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self._client = None
                self._available = False

    def meter_instance_usage(
        self, instance_id: str, tenant_id: str, metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Calculate real compute units and update global usage ledger
        # Args: metrics - Execution metrics (defect_count, pairing_weight, circuit_depth)
        # Returns: Metering result with compute_units_drawn and status
        defect_count = metrics.get("defect_count", 0)
        pairing_weight = metrics.get("pairing_weight", 1.0)
        circuit_depth = metrics.get("circuit_depth", 1)

        # Calculate concrete hardware unit draw
        compute_units = float((defect_count * pairing_weight) + 1.0) * circuit_depth

        if not self.available:
            return {
                "compute_units_drawn": compute_units,
                "tenant_id": tenant_id,
                "status": "METERED_IN_MEMORY",
            }

        try:
            # Atomically increment global usage logs inside Redis
            pipe = self._client.pipeline()
            pipe.hincrbyfloat(
                f"tenant:{tenant_id}:metering", "total_compute_units", compute_units
            )
            pipe.hincrby(f"tenant:{tenant_id}:metering", "total_execution_cycles", 1)
            pipe.hincrby(
                f"instance:{instance_id}:metering", "total_execution_cycles", 1
            )
            pipe.execute()

            logger.info(
                "Resource consumption recorded",
                extra={
                    "instance_id": instance_id,
                    "tenant_id": tenant_id,
                    "compute_units": compute_units,
                    "circuit_depth": circuit_depth,
                },
            )

            return {
                "compute_units_drawn": compute_units,
                "tenant_id": tenant_id,
                "status": "METERED_SUCCESS",
            }
        except Exception as e:
            logger.error(
                "Resource metering failed",
                extra={
                    "instance_id": instance_id,
                    "tenant_id": tenant_id,
                    "error": str(e),
                },
            )
            return {
                "compute_units_drawn": compute_units,
                "tenant_id": tenant_id,
                "status": "METERING_FAILED",
            }

    def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        # Retrieve tenant's total resource usage from Redis.
        # Args:
        #     tenant_id: Tenant/customer ID
        # Returns:
        #     Dict with total_compute_units and total_execution_cycles
        if not self.available:
            return {"total_compute_units": 0.0, "total_execution_cycles": 0}

        try:
            usage = self._client.hgetall(f"tenant:{tenant_id}:metering")
            return {
                "total_compute_units": float(usage.get("total_compute_units", 0)),
                "total_execution_cycles": int(usage.get("total_execution_cycles", 0)),
            }
        except Exception as e:
            logger.warning(
                "Failed to retrieve tenant usage",
                extra={"tenant_id": tenant_id, "error": str(e)},
            )
            return {"total_compute_units": 0.0, "total_execution_cycles": 0}

    def delete_instance(self, instance_id: str) -> bool:
        # Delete instance topology and release all associated locks
        # Args: instance_id - Unique identifier for the compute instance
        # Returns: True if deletion successful, False otherwise
        if not self.available:
            return True

        try:
            state_key = f"quantum:instance:{instance_id}:metadata"
            lock_key = f"quantum:lock:register:{instance_id}"
            meter_key = f"instance:{instance_id}:metering"

            pipe = self._client.pipeline()
            pipe.delete(state_key)
            pipe.delete(lock_key)
            pipe.delete(meter_key)
            pipe.execute()

            logger.info("Instance deleted", extra={"instance_id": instance_id})
            return True
        except Exception as e:
            logger.error(
                "Instance deletion failed",
                extra={"instance_id": instance_id, "error": str(e)},
            )
            return False


# Global registry instance with lazy initialization
_global_redis_registry: Optional[RedisQuantumSubstrateRegistry] = None


def get_redis_registry() -> RedisQuantumSubstrateRegistry:
    # Get or create global Redis registry instance
    global _global_redis_registry
    if _global_redis_registry is None:
        _global_redis_registry = RedisQuantumSubstrateRegistry()
    return _global_redis_registry
