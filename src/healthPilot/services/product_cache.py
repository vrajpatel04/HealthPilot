import hashlib
import json
from typing import Any

from healthPilot.cache.redis_cache import cache_get_json, cache_set_json, get_cache
from healthPilot.core.config import get_settings


def _list_cache_key(**params: Any) -> str:
    payload = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"products:list:{digest}"


async def invalidate_product_cache() -> None:
    await (await get_cache()).delete_pattern("products:*")


async def get_cached_product_list(**params: Any) -> dict[str, Any] | None:
    return await cache_get_json(_list_cache_key(**params))


async def set_cached_product_list(payload: dict[str, Any], **params: Any) -> None:
    settings = get_settings()
    await cache_set_json(_list_cache_key(**params), payload, settings.PRODUCT_LIST_CACHE_TTL)


async def get_cached_product_detail(product_id: str) -> dict[str, Any] | None:
    return await cache_get_json(f"products:detail:{product_id}")


async def set_cached_product_detail(product_id: str, payload: dict[str, Any]) -> None:
    settings = get_settings()
    await cache_set_json(f"products:detail:{product_id}", payload, settings.PRODUCT_DETAIL_CACHE_TTL)
