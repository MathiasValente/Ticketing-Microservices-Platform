import logging

from services.common.event_bus import EventBus
from services.inventory.database import AsyncSessionLocal
from services.inventory.models import Reservation, TicketItem
from services.inventory.reservation_engine import ReservationEngine

logger = logging.getLogger("inventory_worker")
logger.setLevel(logging.INFO)

async def handle_event(event_type: str, payload: dict):
    logger.info(f"[INVENTORY WORKER] Handling event '{event_type}' with payload: {payload}")
    
    async with AsyncSessionLocal() as db:
        if event_type == "payment.completed":
            reservation_id = payload.get("reservation_id")
            ticket_id = payload.get("ticket_id")
            user_id = payload.get("user_id")

            reservation = await db.get(Reservation, reservation_id)
            ticket = await db.get(TicketItem, ticket_id)

            if reservation and ticket:
                reservation.status = "CONFIRMED"
                ticket.status = "SOLD"
                await db.commit()
                logger.info(f"[INVENTORY WORKER] Reservation '{reservation_id}' CONFIRMED, Ticket '{ticket_id}' marked as SOLD")

        elif event_type == "payment.failed":
            reservation_id = payload.get("reservation_id")
            ticket_id = payload.get("ticket_id")
            user_id = payload.get("user_id")

            reservation = await db.get(Reservation, reservation_id)
            ticket = await db.get(TicketItem, ticket_id)

            if reservation and ticket:
                reservation.status = "CANCELLED"
                ticket.status = "AVAILABLE"
                await db.commit()
                
                # Release Redis Lua lock
                if user_id:
                    await ReservationEngine.release_hold(ticket_id, user_id)
                logger.info(f"[INVENTORY WORKER] Reservation '{reservation_id}' CANCELLED, Ticket '{ticket_id}' returned to AVAILABLE")

async def start_event_listener():
    logger.info("[INVENTORY WORKER] Starting event listener loop...")
    await EventBus.listen(handle_event)
