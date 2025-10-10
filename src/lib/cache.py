"""Caching utilities for performance-sensitive operations."""

from __future__ import annotations

import os
import pickle
import sqlite3
import time
from enum import Enum
from threading import RLock
from typing import Any, Optional

from src.paths import PATHS


class CacheNamespace(str, Enum):
    """Namespaces used for persisted caches."""

    DISTANCE = "recommendation_distance"
    MILESTONES = "recommendation_milestones"


def _ensure_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def encode_cache_key(*parts: Any) -> str:
    """Create a deterministic cache key from multiple parts."""

    flattened: list[str] = []
    for part in parts:
        if isinstance(part, (list, tuple, set)):
            flattened.append(encode_cache_key(*part))
        else:
            flattened.append(str(part))
    return "|".join(flattened)


class SqliteCache:
    """Lightweight SQLite-backed cache with optional TTL support."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = RLock()
        _ensure_directory(os.path.dirname(db_path))
        self._initialise()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialise(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    namespace TEXT NOT NULL,
                    cache_key TEXT NOT NULL,
                    value BLOB NOT NULL,
                    expires_at REAL,
                    PRIMARY KEY (namespace, cache_key)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_cache_expiry
                    ON cache_entries (expires_at)
                """
            )
            connection.commit()

    def get(self, namespace: CacheNamespace, cache_key: str) -> Optional[Any]:
        """Fetch a cached value if available and not expired."""

        with self._lock, self._connect() as connection:
            now = time.time()
            connection.execute(
                "DELETE FROM cache_entries WHERE expires_at IS NOT NULL AND expires_at < ?",
                (now,),
            )
            cursor = connection.execute(
                """
                SELECT value FROM cache_entries
                WHERE namespace = ? AND cache_key = ?
                """,
                (namespace.value, cache_key),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return pickle.loads(row[0])

    def set(
        self,
        namespace: CacheNamespace,
        cache_key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Store a value in the cache."""

        expires_at = None
        if ttl_seconds is not None:
            expires_at = time.time() + ttl_seconds

        payload = pickle.dumps(value)

        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO cache_entries(namespace, cache_key, value, expires_at)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(namespace, cache_key) DO UPDATE SET
                    value = excluded.value,
                    expires_at = excluded.expires_at
                """,
                (namespace.value, cache_key, payload, expires_at),
            )
            connection.commit()

    def clear(self, namespace: Optional[CacheNamespace] = None) -> None:
        """Remove cache entries."""

        with self._lock, self._connect() as connection:
            if namespace is None:
                connection.execute("DELETE FROM cache_entries")
            else:
                connection.execute(
                    "DELETE FROM cache_entries WHERE namespace = ?",
                    (namespace.value,),
                )
            connection.commit()


_recommendation_cache: Optional[SqliteCache] = None


def get_recommendation_cache() -> SqliteCache:
    """Return the shared cache used by the recommendation engine."""

    global _recommendation_cache
    if _recommendation_cache is None:
        _recommendation_cache = SqliteCache(PATHS.RECOMMENDATION_CACHE_DB)
    return _recommendation_cache


def clear_recommendation_cache(namespace: Optional[CacheNamespace] = None) -> None:
    """Clear recommendation caches for the provided namespace."""

    get_recommendation_cache().clear(namespace)
