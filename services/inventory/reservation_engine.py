import logging

from services.common.redis_client import get_redis_client

logger = logging.getLogger("reservation_engine")

LUA_ACQUIRE_TICKET_HOLD = """
local lock_key = KEYS[1]
local lock_value = ARGV[1]
local ttl_ms = tonumber(ARGV[2])

if redis.call("EXISTS", lock_key) == 0 then
    redis.call("SET", lock_key, lock_value, "PX", ttl_ms)
    return 1
else
    return 0
end
"""

LUA_RELEASE_TICKET_HOLD = """
local lock_key = KEYS[1]
local lock_value = ARGV[1]

if redis.call("GET", lock_key) == lock_value then
    return redis.call("DEL", lock_key)
else
    return 0
end
"""

class ReservationEngine:
    """
    High-Concurrency Atomic Reservation Engine powered by Redis Lua Scripts.
    Guarantees strict single-assignment zero-oversell locks during massive flash sale traffic spikes.
    """

    @staticmethod
    async def try_acquire_hold(ticket_id: str, user_id: str, ttl_seconds: int = 600) -> tuple[bool, str | None]:
        client = await get_redis_client()
        lock_key = f"lock:ticket:{ticket_id}"
        lock_value = f"user:{user_id}"
        ttl_ms = ttl_seconds * 1000

        try:
            # Execute atomic Lua script
            result = await client.eval(LUA_ACQUIRE_TICKET_HOLD, 1, lock_key, lock_value, ttl_ms)
            if result == 1:
                logger.info(f"[LUA LOCK SUCCESS] Ticket '{ticket_id}' locked for User '{user_id}' with TTL {ttl_seconds}s")
                return True, lock_value
            else:
                logger.warning(f"[LUA LOCK CONFLICT] Ticket '{ticket_id}' already locked by another user")
                return False, None
        except Exception as e:
            logger.error(f"[LUA LOCK ERROR] Error executing Redis lock Lua script: {e}")
            raise e

    @staticmethod
    async def release_hold(ticket_id: str, user_id: str) -> bool:
        client = await get_redis_client()
        lock_key = f"lock:ticket:{ticket_id}"
        lock_value = f"user:{user_id}"

        try:
            result = await client.eval(LUA_RELEASE_TICKET_HOLD, 1, lock_key, lock_value)
            return result == 1
        except Exception as e:
            logger.error(f"[LUA UNLOCK ERROR] Error executing Redis release Lua script: {e}")
            return False
