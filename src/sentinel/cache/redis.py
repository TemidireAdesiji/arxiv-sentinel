"""Redis cache store with deterministic key hashing."""

from __future__ import annotations

import hashlib
import json
from typing import Any, cast

import structlog

from sentinel.settings import CacheCfg

log = structlog.get_logger(__name__)


class CacheStore:
    """Exact-match response cache backed by Redis.

    Keys are SHA-256 digests of the canonical request
    parameters so lookups are O(1).
    """

    def __init__(
        self,
        host: str,
        port: int,
        *,
        password: str = "",
        db: int = 0,
        ttl_hours: int = 6,
    ) -> None:
        import redis

        url_parts = f"{host}:{port}/{db}"
        if password:
            url_parts = f":{password}@{url_parts}"
        self._r = redis.Redis(
            host=host,
            port=port,
            password=password or None,
            db=db,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        self._ttl = ttl_hours * 3600
        log.info(
            "cache_connected",
            host=host,
            port=port,
            db=db,
        )

    # -- public API -----------------------------------------------

    def lookup(
        self,
        **params: Any,
    ) -> dict[str, Any] | None:
        """Return cached response or *None* on miss."""
        key = self._digest(params)
        try:
            raw = cast("str | None", self._r.get(key))
        except Exception:
            log.debug("cache_read_failed", key=key)
            return None
        if raw is None:
            return None
        log.debug("cache_hit", key=key)
        return cast("dict[str, Any]", json.loads(raw))

    def store(
        self,
        response: dict[str, Any],
        **params: Any,
    ) -> None:
        """Persist a response under the hashed params."""
        key = self._digest(params)
        try:
            self._r.setex(key, self._ttl, json.dumps(response))
            log.debug("cache_stored", key=key)
        except Exception:
            log.debug("cache_write_failed", key=key)

    def is_available(self) -> bool:
        """Return *True* if Redis is reachable."""
        try:
            return bool(self._r.ping())
        except Exception:
            return False

    # -- internals ------------------------------------------------

    @staticmethod
    def _digest(params: dict[str, Any]) -> str:
        canon = json.dumps(params, sort_keys=True, default=str)
        return hashlib.sha256(canon.encode()).hexdigest()

    def close(self) -> None:
        self._r.close()


def create_cache_store(
    cfg: CacheCfg,
) -> CacheStore | None:
    """Factory: build a ``CacheStore``, or *None* on failure."""
    try:
        store = CacheStore(
            host=cfg.host,
            port=cfg.port,
            password=cfg.password,
            db=cfg.db,
            ttl_hours=cfg.ttl_hours,
        )
        if store.is_available():
            return store
        log.warning("cache_unavailable")
        return None
    except Exception as exc:
        log.warning("cache_init_failed", err=str(exc))
        return None
