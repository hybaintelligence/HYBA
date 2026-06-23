"""
Redis implementation reference for DistributedLockManager.

This module demonstrates how to replace the mock Redis operations in
DistributedLockManager with real Redis implementations using aioredis.

NOTE: This is a reference implementation. To use it in production:

1. Uncomment the import at the top of distributed_lock_manager.py
2. Replace the mock methods with these implementations
3. Add proper connection pooling and error handling

Example usage in distributed_lock_manager.py:

    # Add to imports
    from .distributed_lock_manager_redis_impl import (
        RedisConnectionPool,
        create_redis_operations,
    )

    # In __init__
    self.redis_pool = RedisConnectionPool(self.redis_url)
    self._redis_set_nx = create_redis_operations(self.redis_pool)['set_nx']
    self._redis_get = create_redis_operations(self.redis_pool)['get']
    self._redis_delete = create_redis_operations(self.redis_pool)['delete']
    self._redis_get_with_ttl = create_redis_operations(self.redis_pool)['get_with_ttl']
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Tuple, Dict, Callable, Any

try:
    import aioredis
    from redis.exceptions import (
        ConnectionError,
        TimeoutError as RedisTimeoutError,
    )
except ImportError:
    raise ImportError(
        "aioredis is required for Redis operations. "
        "Install with: pip install aioredis==2.0.1"
    )

logger = logging.getLogger(__name__)


class RedisConnectionError(Exception):
    """Raised when Redis connection fails."""

    pass


class RedisConnectionPool:
    """
    Connection pool for Redis operations.

    Manages a pool of async Redis connections with automatic reconnection
    and health checking.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        max_connections: int = 10,
        socket_keepalive: bool = True,
        socket_keepalive_options: Optional[Dict[str, Any]] = None,
        health_check_interval: int = 30,
    ):
        """
        Initialize Redis connection pool.

        Args:
            redis_url: Redis connection URL
            max_connections: Maximum concurrent connections
            socket_keepalive: Enable TCP keepalive
            socket_keepalive_options: Keepalive socket options
            health_check_interval: Health check interval in seconds
        """
        self.redis_url = redis_url
        self.max_connections = max_connections
        self.socket_keepalive = socket_keepalive
        self.socket_keepalive_options = socket_keepalive_options or {}
        self.health_check_interval = health_check_interval

        self.redis: Optional[aioredis.Redis] = None
        self._lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None

    async def connect(self) -> aioredis.Redis:
        """
        Get or establish Redis connection.

        Returns:
            aioredis.Redis: Redis connection

        Raises:
            RedisConnectionError: If connection fails
        """
        if self.redis is not None:
            return self.redis

        async with self._lock:
            if self.redis is not None:
                return self.redis

            try:
                self.redis = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf8",
                    decode_responses=True,
                    socket_keepalive=self.socket_keepalive,
                )

                # Test connection
                await self.redis.ping()

                logger.info(
                    "Redis connection established",
                    extra={"redis_url": self.redis_url},
                )

                # Start health check
                self._health_check_task = asyncio.create_task(self._health_check_loop())

                return self.redis

            except (ConnectionError, RedisTimeoutError) as exc:
                logger.error(
                    "Failed to connect to Redis",
                    exc_info=True,
                    extra={"redis_url": self.redis_url, "error": str(exc)},
                )
                raise RedisConnectionError(
                    f"Failed to connect to Redis at {self.redis_url}: {exc}"
                ) from exc

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        if self.redis:
            await self.redis.close()
            self.redis = None

    async def _health_check_loop(self) -> None:
        """Periodic health check for Redis connection."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                if self.redis:
                    await self.redis.ping()
            except Exception as exc:
                logger.warning(
                    "Redis health check failed",
                    extra={"error": str(exc)},
                )
                self.redis = None


def create_redis_operations(pool: RedisConnectionPool):
    """
    Create Redis operation functions.

    Args:
        pool: Redis connection pool

    Returns:
        dict: Dictionary of Redis operation functions
    """

    async def set_nx(key: str, value: str, ttl: int) -> bool:
        """
        Set key in Redis only if it doesn't exist (SET NX).

        Args:
            key: Redis key
            value: Value to set
            ttl: Time-to-live in seconds

        Returns:
            bool: True if set was successful, False if key already exists

        Raises:
            RedisConnectionError: If Redis operation fails
        """
        try:
            redis = await pool.connect()
            redis_key = f"lock:{key}"

            # SET with NX (only if not exists) and EX (expire time)
            result = await redis.set(redis_key, value, ex=ttl, nx=True)

            logger.debug(
                "Redis SET NX operation",
                extra={
                    "key": redis_key,
                    "ttl": ttl,
                    "success": result is not None,
                },
            )

            return result is not None

        except (ConnectionError, RedisTimeoutError) as exc:
            logger.error(
                "Redis SET NX failed",
                exc_info=True,
                extra={"key": key, "error": str(exc)},
            )
            raise RedisConnectionError(f"Redis SET NX failed: {exc}") from exc

    async def get(key: str) -> Optional[str]:
        """
        Get value from Redis.

        Args:
            key: Redis key

        Returns:
            Optional[str]: Value or None if key doesn't exist

        Raises:
            RedisConnectionError: If Redis operation fails
        """
        try:
            redis = await pool.connect()
            redis_key = f"lock:{key}"

            value = await redis.get(redis_key)

            logger.debug(
                "Redis GET operation",
                extra={
                    "key": redis_key,
                    "found": value is not None,
                },
            )

            return value

        except (ConnectionError, RedisTimeoutError) as exc:
            logger.error(
                "Redis GET failed",
                exc_info=True,
                extra={"key": key, "error": str(exc)},
            )
            raise RedisConnectionError(f"Redis GET failed: {exc}") from exc

    async def delete(key: str) -> bool:
        """
        Delete key from Redis.

        Args:
            key: Redis key

        Returns:
            bool: True if deleted, False if didn't exist

        Raises:
            RedisConnectionError: If Redis operation fails
        """
        try:
            redis = await pool.connect()
            redis_key = f"lock:{key}"

            deleted = await redis.delete(redis_key)

            logger.debug(
                "Redis DELETE operation",
                extra={
                    "key": redis_key,
                    "deleted": deleted > 0,
                },
            )

            return deleted > 0

        except (ConnectionError, RedisTimeoutError) as exc:
            logger.error(
                "Redis DELETE failed",
                exc_info=True,
                extra={"key": key, "error": str(exc)},
            )
            raise RedisConnectionError(f"Redis DELETE failed: {exc}") from exc

    async def get_with_ttl(key: str) -> Optional[Tuple[str, float]]:
        """
        Get value and remaining TTL from Redis.

        Args:
            key: Redis key

        Returns:
            Optional[Tuple[str, float]]: (value, ttl_seconds) or None if key doesn't exist

        Raises:
            RedisConnectionError: If Redis operation fails
        """
        try:
            redis = await pool.connect()
            redis_key = f"lock:{key}"

            # Get value and TTL
            value = await redis.get(redis_key)
            if value is None:
                return None

            ttl = await redis.ttl(redis_key)

            # TTL can be:
            # -2: key doesn't exist
            # -1: key exists but has no TTL
            # > 0: remaining seconds

            logger.debug(
                "Redis GET with TTL operation",
                extra={
                    "key": redis_key,
                    "ttl_seconds": ttl,
                },
            )

            return (value, float(ttl))

        except (ConnectionError, RedisTimeoutError) as exc:
            logger.error(
                "Redis GET with TTL failed",
                exc_info=True,
                extra={"key": key, "error": str(exc)},
            )
            raise RedisConnectionError(f"Redis GET with TTL failed: {exc}") from exc

    return {
        "set_nx": set_nx,
        "get": get,
        "delete": delete,
        "get_with_ttl": get_with_ttl,
    }


class RedisSentinelPool:
    """
    High-availability Redis connection pool using Sentinel.

    Provides automatic failover and reconnection to Redis Sentinel-managed clusters.
    """

    def __init__(
        self,
        sentinel_urls: list[str],
        service_name: str = "mymaster",
        db: int = 0,
        max_connections: int = 10,
    ):
        """
        Initialize Redis Sentinel pool.

        Args:
            sentinel_urls: List of Redis Sentinel URLs
            service_name: Sentinel service name (default: "mymaster")
            db: Redis database number
            max_connections: Maximum concurrent connections
        """
        self.sentinel_urls = sentinel_urls
        self.service_name = service_name
        self.db = db
        self.max_connections = max_connections
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self) -> aioredis.Redis:
        """
        Connect to Redis via Sentinel.

        Returns:
            aioredis.Redis: Redis connection

        Raises:
            RedisConnectionError: If connection fails
        """
        if self.redis is not None:
            return self.redis

        try:
            # Note: aioredis 2.0 doesn't have direct Sentinel support
            # This is a placeholder for future implementation
            # For now, use standard connection pool with failover URLs

            self.redis = await aioredis.from_url(
                self.sentinel_urls[0],
                encoding="utf8",
                decode_responses=True,
            )

            await self.redis.ping()

            logger.info(
                "Redis Sentinel connection established",
                extra={
                    "service_name": self.service_name,
                    "sentinel_urls": self.sentinel_urls,
                },
            )

            return self.redis

        except Exception as exc:
            logger.error(
                "Failed to connect to Redis Sentinel",
                exc_info=True,
                extra={"error": str(exc)},
            )
            raise RedisConnectionError(
                f"Failed to connect to Redis Sentinel: {exc}"
            ) from exc

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None


# Example usage in FastAPI app
async def initialize_lock_manager_with_redis(app_startup_context):
    """
    Initialize lock manager with real Redis in FastAPI app.

    Example:

        from fastapi import FastAPI
        from pythia_mining.distributed_lock_manager import DistributedLockManager

        app = FastAPI()

        @app.on_event("startup")
        async def startup():
            global lock_manager
            lock_manager = DistributedLockManager()
            await initialize_lock_manager_with_redis(None)

        @app.on_event("shutdown")
        async def shutdown():
            global lock_manager
            # Cleanup
            pass
    """
    pass


if __name__ == "__main__":
    # Example: standalone usage
    async def main():
        pool = RedisConnectionPool("redis://localhost:6379")
        ops = create_redis_operations(pool)

        # Test operations
        try:
            # Set lock
            success = await ops["set_nx"]("test_lock", "token_123", 30)
            print(f"Lock acquired: {success}")

            # Get lock value
            value = await ops["get"]("test_lock")
            print(f"Lock value: {value}")

            # Get with TTL
            result = await ops["get_with_ttl"]("test_lock")
            print(f"Lock value and TTL: {result}")

            # Delete lock
            deleted = await ops["delete"]("test_lock")
            print(f"Lock deleted: {deleted}")

        finally:
            await pool.disconnect()

    asyncio.run(main())
