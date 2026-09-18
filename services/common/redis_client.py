from typing import Any

import redis.asyncio as redis  # type: ignore

from services.common.config import settings

_redis_pool: Any = None


def get_redis_pool() -> Any:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL, decode_responses=True, max_connections=50
        )
    return _redis_pool


async def get_redis_client() -> Any:
    pool = get_redis_pool()
    return redis.Redis(connection_pool=pool)


async def close_redis_pool() -> None:
    global _redis_pool
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
