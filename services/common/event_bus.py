import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from services.common.redis_client import get_redis_client

logger = logging.getLogger("event_bus")
logger.setLevel(logging.INFO)

CHANNEL_TICKETING_EVENTS = "ticketing_events_channel"


class EventBus:
    """
    Lightweight Redis Pub/Sub Event Broker pattern for microservices.
    Enables asynchronous event messaging (e.g. payment.succeeded, payment.failed, reservation.expired).
    """

    @staticmethod
    async def publish(event_type: str, payload: dict[str, Any]) -> None:
        client = await get_redis_client()
        message = {"event_type": event_type, "payload": payload}
        raw_msg = json.dumps(message)
        await client.publish(CHANNEL_TICKETING_EVENTS, raw_msg)
        logger.info(f"[EVENT BUS] Published event '{event_type}': {payload}")

    @staticmethod
    async def listen(handler: Callable[[str, dict[str, Any]], Awaitable[None]]) -> None:
        client = await get_redis_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(CHANNEL_TICKETING_EVENTS)
        logger.info(f"[EVENT BUS] Subscribed to channel '{CHANNEL_TICKETING_EVENTS}'")

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    event_type = data.get("event_type")
                    payload = data.get("payload", {})
                    logger.info(f"[EVENT BUS] Received event '{event_type}'")
                    await handler(str(event_type), payload)
                except Exception as e:
                    logger.error(f"[EVENT BUS] Error processing event message: {e}")
