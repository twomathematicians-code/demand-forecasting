"""Database session management with asyncpg connection pool."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import asyncpg
from src.utils.config import get_settings, Settings


class Database:
    """Async PostgreSQL connection pool manager.

    Usage:
        db = Database(settings)
        await db.connect()
        async with db.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM actuals LIMIT 10")
        await db.disconnect()
    """

    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()
        self._pool: asyncpg.Pool | None = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Database not connected. Call await db.connect() first.")
        return self._pool

    @property
    def is_connected(self) -> bool:
        return self._pool is not None

    async def connect(self) -> None:
        """Initialize the connection pool."""
        if self._pool is not None:
            return

        s = self._settings
        self._pool = await asyncpg.create_pool(
            host=s.db_host,
            port=s.db_port,
            user=s.db_user,
            password=s.db_password,
            database=s.db_name,
            min_size=s.db_min_connections,
            max_size=s.db_max_connections,
            command_timeout=60,
        )

    async def disconnect(self) -> None:
        """Close the connection pool gracefully."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def check_health(self) -> bool:
        """Verify database connectivity."""
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    async def execute(self, query: str, *args: Any) -> str:
        """Execute a statement and return the status."""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        """Execute a query and return all rows."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> asyncpg.Record | None:
        """Execute a query and return a single row."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        """Execute a query and return a single value."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def executemany(self, query: str, args_list: list[tuple]) -> None:
        """Execute a statement with multiple parameter sets."""
        async with self.pool.acquire() as conn:
            await conn.executemany(query, args_list)


# ── Module-level singleton ──

_db: Database | None = None


def get_db() -> Database:
    """Return the singleton Database instance."""
    global _db
    if _db is None:
        _db = Database()
    return _db


async def init_db() -> Database:
    """Initialize and return the database singleton."""
    db = get_db()
    if not db.is_connected:
        await db.connect()
    return db


async def close_db() -> None:
    """Close the database singleton if connected."""
    global _db
    if _db is not None and _db.is_connected:
        await _db.disconnect()
    _db = None


@asynccontextmanager
async def get_connection() -> AsyncIterator[asyncpg.Connection]:
    """Context manager that provides a connection from the pool."""
    db = get_db()
    if not db.is_connected:
        await db.connect()
    async with db.pool.acquire() as conn:
        yield conn
