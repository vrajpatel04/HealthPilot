from __future__ import annotations

import json
import logging
from typing import Any

from healthPilot.core.config import get_settings

logger = logging.getLogger(__name__)

_redis_client = None


async def redis_status() -> str:
    """Return 'ready', 'read-only', 'disabled', or 'failed' for startup logging."""
    settings = get_settings()
    if not settings.REDIS_URL:
        return "disabled"
    try:
        from redis.asyncio import Redis

        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        try:
            await client.ping()
            probe_key = "hp:write_probe"
            try:
                await client.set(probe_key, "1", ex=10)
                await client.delete(probe_key)
                return "ready"
            except Exception as exc:
                if "NoPermissionError" in type(exc).__name__ or "NOPERM" in str(exc):
                    return "read-only"
                raise
        finally:
            await client.aclose()
    except Exception:
        return "failed"


async def get_cache():
    global _redis_client
    settings = get_settings()
    if not settings.REDIS_URL:
        return NullCache()
    if _redis_client is None:
        try:
            from redis.asyncio import Redis

            _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            await _redis_client.ping()
        except Exception:
            return NullCache()
    return RedisCache(_redis_client)


class NullCache:
    async def get(self, key: str) -> str | None:
        return None

    async def set(self, key: str, value: str, ttl_seconds: int = 3600) -> None:
        return None

    async def delete(self, key: str) -> None:
        return None

    async def delete_pattern(self, pattern: str) -> None:
        return None


class RedisCache:
    def __init__(self, client) -> None:
        self.client = client

    async def get(self, key: str) -> str | None:
        try:
            return await self.client.get(key)
        except Exception:
            return None

    async def set(self, key: str, value: str, ttl_seconds: int = 3600) -> None:
        try:
            await self.client.set(key, value, ex=ttl_seconds)
        except Exception as exc:
            logger.warning("Redis SET failed for %s: %s", key, exc)
            return None

    async def delete(self, key: str) -> None:
        try:
            await self.client.delete(key)
        except Exception:
            return None

    async def delete_pattern(self, pattern: str) -> None:
        try:
            keys = [key async for key in self.client.scan_iter(match=pattern)]
            if keys:
                await self.client.delete(*keys)
        except Exception:
            return None


async def cache_get_json(key: str) -> Any | None:
    raw = await (await get_cache()).get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def cache_set_json(key: str, value: Any, ttl_seconds: int) -> None:
    await (await get_cache()).set(key, json.dumps(value, default=str), ttl_seconds)
