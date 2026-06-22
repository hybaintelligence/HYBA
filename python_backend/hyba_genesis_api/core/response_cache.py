"""Small Redis-backed response cache with in-memory fallback for static capability maps."""
from __future__ import annotations

import json
import time
from typing import Any

from pythia_mining.redis_state_registry import get_redis_registry

_MEMORY_CACHE: dict[str, tuple[float, Any]] = {}


def get_cached_json(key: str) -> Any | None:
    redis_registry = get_redis_registry()
    if redis_registry.available and redis_registry.client is not None:
        cached = redis_registry.client.get(key)
        if cached:
            if isinstance(cached, bytes):
                cached = cached.decode("utf-8")
            return json.loads(cached)
    item = _MEMORY_CACHE.get(key)
    if item and item[0] > time.time():
        return item[1]
    if item:
        _MEMORY_CACHE.pop(key, None)
    return None


def set_cached_json(key: str, value: Any, ttl_seconds: int = 300) -> Any:
    redis_registry = get_redis_registry()
    if redis_registry.available and redis_registry.client is not None:
        redis_registry.client.setex(key, ttl_seconds, json.dumps(value, default=str))
    _MEMORY_CACHE[key] = (time.time() + ttl_seconds, value)
    return value


def clear_response_cache() -> None:
    _MEMORY_CACHE.clear()
