"""SQLite-backed API cache and usage limiter for external data providers."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CacheResult:
    """Result returned by an API cache lookup."""

    hit: bool
    payload: dict[str, Any] | None
    cache_key: str


class DailyLimitExceeded(RuntimeError):
    """Raised when a provider daily limit has already been reached."""


class ApiCache:
    """Small local cache for protecting free-tier API limits.

    The cache stores provider responses and usage logs, but never stores API keys.
    It is intentionally backend-side only.
    """

    def __init__(self, db_path: str | Path = "data/cache/api_cache.sqlite3") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                create table if not exists api_cache (
                    cache_key text primary key,
                    provider text not null,
                    endpoint text not null,
                    response_json text not null,
                    expires_at text not null,
                    created_at text not null,
                    updated_at text not null
                );

                create table if not exists api_usage_logs (
                    id integer primary key autoincrement,
                    provider text not null,
                    endpoint text not null,
                    cache_key text,
                    cache_status text not null,
                    request_date text not null,
                    created_at text not null
                );
                """
            )

    @staticmethod
    def make_cache_key(provider: str, endpoint: str, params: dict[str, Any] | None = None) -> str:
        """Create a stable cache key from non-secret request fields."""
        normalized = json.dumps(params or {}, sort_keys=True, default=str)
        raw = f"{provider}:{endpoint}:{normalized}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def get(self, provider: str, endpoint: str, params: dict[str, Any] | None = None) -> CacheResult:
        """Read a cached payload if present and not expired."""
        cache_key = self.make_cache_key(provider, endpoint, params)
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "select response_json from api_cache where cache_key = ? and expires_at > ?",
                (cache_key, now),
            ).fetchone()
        if not row:
            return CacheResult(hit=False, payload=None, cache_key=cache_key)
        return CacheResult(hit=True, payload=json.loads(row["response_json"]), cache_key=cache_key)

    def set(
        self,
        provider: str,
        endpoint: str,
        params: dict[str, Any] | None,
        payload: dict[str, Any],
        ttl_hours: int,
    ) -> str:
        """Persist a response payload with a TTL."""
        cache_key = self.make_cache_key(provider, endpoint, params)
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=ttl_hours)
        with self._connect() as conn:
            conn.execute(
                """
                insert into api_cache (cache_key, provider, endpoint, response_json, expires_at, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?)
                on conflict(cache_key) do update set
                    response_json = excluded.response_json,
                    expires_at = excluded.expires_at,
                    updated_at = excluded.updated_at
                """,
                (
                    cache_key,
                    provider,
                    endpoint,
                    json.dumps(payload),
                    expires_at.isoformat(),
                    now.isoformat(),
                    now.isoformat(),
                ),
            )
        return cache_key

    def log_usage(self, provider: str, endpoint: str, cache_key: str | None, cache_status: str) -> None:
        """Log non-sensitive API usage metadata."""
        now = datetime.now(UTC)
        with self._connect() as conn:
            conn.execute(
                """
                insert into api_usage_logs (provider, endpoint, cache_key, cache_status, request_date, created_at)
                values (?, ?, ?, ?, ?, ?)
                """,
                (provider, endpoint, cache_key, cache_status, date.today().isoformat(), now.isoformat()),
            )

    def count_daily_misses(self, provider: str, request_date: date | None = None) -> int:
        """Count real provider calls for a given day, excluding cache hits."""
        day = (request_date or date.today()).isoformat()
        with self._connect() as conn:
            row = conn.execute(
                """
                select count(*) as count
                from api_usage_logs
                where provider = ? and request_date = ? and cache_status = 'miss'
                """,
                (provider, day),
            ).fetchone()
        return int(row["count"] if row else 0)

    def ensure_daily_limit(self, provider: str, endpoint: str, daily_limit: int, cache_key: str) -> None:
        """Block a provider call if the daily miss limit has been reached."""
        if self.count_daily_misses(provider) >= daily_limit:
            self.log_usage(provider, endpoint, cache_key, "blocked")
            raise DailyLimitExceeded(f"Daily {provider} API limit reached. Try cached data or wait until tomorrow.")
