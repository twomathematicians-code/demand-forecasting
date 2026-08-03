"""Tests for Redis cache manager."""

import pytest

from src.cache.redis_cache import CacheManager


class TestCacheManager:
    def test_init(self):
        cache = CacheManager("redis://localhost:6379/0")
        assert not cache.is_connected

    def test_get_without_connect(self):
        """get/set should silently bypass when Redis is not connected."""
        import asyncio
        cache = CacheManager("redis://nonexistent:6379/0")
        # Cache is not connected, so get returns None
        val = asyncio.run(cache.get("key"))
        assert val is None
        # Set should not raise
        asyncio.run(cache.set("key", "value"))

    @pytest.mark.asyncio
    async def test_set_get_bypass_when_disconnected(self):
        cache = CacheManager("redis://nonexistent:6379/0")
        await cache.connect()  # Should fail gracefully
        assert not cache.is_connected
        await cache.set("test", "value")
        val = await cache.get("test")
        assert val is None

    def test_singleton(self):
        from src.cache.redis_cache import get_cache
        c1 = get_cache()
        c2 = get_cache()
        assert c1 is c2
