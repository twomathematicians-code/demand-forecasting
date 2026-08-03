"""Redis cache manager with graceful fallback for demand forecasting."""

from __future__ import annotations

import json
import logging
from functools import wraps
from typing import Any, Callable

log = logging.getLogger(__name__)


class CacheManager:
    """Async Redis cache with graceful degradation.

    If Redis is unavailable, all operations silently pass through
    (cache misses) — never throws errors to the application layer.

    Usage:
        cache = CacheManager("redis://localhost:6379/0")
        await cache.connect()
        await cache.set("key", {"data": 123}, ttl=300)
        value = await cache.get("key")
        await cache.disconnect()
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._redis = None
        self._enabled = False

    @property
    def is_connected(self) -> bool:
        return self._enabled and self._redis is not None

    async def connect(self) -> None:
        """Initialize Redis connection. No-op if Redis unavailable."""
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                self.redis_url,
                socket_connect_timeout=2,
                socket_timeout=2,
                decode_responses=True,
            )
            await self._redis.ping()
            self._enabled = True
            log.info("Redis connected: %s", self.redis_url)
        except Exception as e:
            log.warning("Redis unavailable (%s). Caching disabled.", e)
            self._redis = None
            self._enabled = False

    async def disconnect(self) -> None:
        """Close Redis connection gracefully."""
        if self._redis:
            try:
                await self._redis.close()
            except Exception:
                pass
        self._redis = None
        self._enabled = False

    async def get(self, key: str) -> Any | None:
        """Retrieve a cached value. Returns None on miss or error."""
        if not self.is_connected:
            return None
        try:
            value = await self._redis.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Store a value in cache with TTL (seconds)."""
        if not self.is_connected:
            return
        try:
            await self._redis.set(key, json.dumps(value, default=str), ex=ttl)
        except Exception as e:
            log.debug("Cache set failed: %s", e)

    async def delete(self, pattern: str) -> None:
        """Delete keys matching a pattern."""
        if not self.is_connected:
            return
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
        except Exception as e:
            log.debug("Cache delete failed: %s", e)

    async def flush(self) -> None:
        """Clear all cached data."""
        if not self.is_connected:
            return
        try:
            await self._redis.flushdb()
        except Exception as e:
            log.debug("Cache flush failed: %s", e)


# ── Singleton ────────────────────────────────────────────

_cache: CacheManager | None = None


def get_cache() -> CacheManager:
    global _cache
    if _cache is None:
        from src.utils.config import get_settings
        _cache = CacheManager(get_settings().redis_url)
    return _cache


# ── Decorator ────────────────────────────────────────────

def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator: caches async function results in Redis.

    Cache key = key_prefix + function_name + str(args) + str(kwargs).
    On cache miss or Redis unavailable, calls the function normally.

    Usage:
        @cached(ttl=300, key_prefix="dashboard:")
        async def get_summary(product_id: str): ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            if not cache.is_connected:
                return await func(*args, **kwargs)

            # Build cache key
            key_parts = [key_prefix, func.__name__]
            key_parts.append(str(args))
            key_parts.append(str(sorted(kwargs.items())))
            cache_key = ":".join(key_parts)

            # Try cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                log.debug("Cache HIT: %s", cache_key)
                return cached_value

            # Miss — compute and store
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator
