import time
from typing import Any

from fastapi import HTTPException, Request, status  # type: ignore

from services.common.redis_client import get_redis_client


class SlidingWindowRateLimiter:
    """
    Redis-backed sliding window rate limiter.
    Limits request rates per IP or client to protect microservices from DDoS/flash-sale spikes.
    """
    def __init__(self, requests_limit: int = 60, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds

    async def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client is not None else "127.0.0.1"
        key = f"rate_limit:{client_ip}:{request.url.path}"
        current_time = time.time()
        window_start = current_time - self.window_seconds

        try:
            redis_client = await get_redis_client()

            pipe = redis_client.pipeline(transaction=True)
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.zcard(key)
            pipe.expire(key, self.window_seconds)
            res: list[Any] = await pipe.execute()

            request_count = int(res[2]) if res and len(res) > 2 else 0

            if request_count > self.requests_limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {self.requests_limit} requests per {self.window_seconds} seconds.",
                )
        except HTTPException:
            raise
        except Exception:
            # Fallback gracefully if Redis is unavailable during offline unit testing
            pass
