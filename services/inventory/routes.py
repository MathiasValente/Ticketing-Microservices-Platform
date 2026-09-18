from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore
from sqlalchemy import select  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore

from services.common.event_bus import EventBus
from services.inventory.database import get_db
from services.inventory.models import (
    HoldRequestSchema,
    Reservation,
    ReservationResponseSchema,
    TicketCreateSchema,
    TicketItem,
    TicketResponseSchema,
)
from services.inventory.reservation_engine import ReservationEngine

router = APIRouter(prefix="/inventory", tags=["Inventory & Booking"])


@router.post("/tickets", response_model=TicketResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_ticket(payload: TicketCreateSchema, db: AsyncSession = Depends(get_db)):
    ticket = TicketItem(
        event_id=payload.event_id,
        seat_category_id=payload.seat_category_id,
        seat_number=payload.seat_number,
        price=payload.price,
        status="AVAILABLE",
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/tickets/event/{event_id}", response_model=list[TicketResponseSchema])
async def list_event_tickets(event_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TicketItem).where(TicketItem.event_id == event_id))
    return result.scalars().all()


@router.post("/hold", response_model=ReservationResponseSchema, status_code=status.HTTP_201_CREATED)
async def hold_ticket(payload: HoldRequestSchema, db: AsyncSession = Depends(get_db)):
    """Core Flash-Sale Booking Endpoint.

    1. Executes atomic Redis Lua script lock to prevent race conditions.
    2. Updates PostgreSQL ticket status to HELD.
    3. Creates a temporary reservation record.
    """
    ticket_id = payload.ticket_id
    user_id = payload.user_id
    ttl = payload.hold_ttl_seconds or 600

    # Step 1: Attempt Atomic Redis Lua Lock
    locked, _lock_val = await ReservationEngine.try_acquire_hold(ticket_id, user_id, ttl)
    if not locked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seat is already locked or sold by another user. Flash sale conflict.",
        )

    # Step 2: Check & update database state
    ticket = await db.get(TicketItem, ticket_id)
    if not ticket or ticket.status != "AVAILABLE":
        # Rollback Redis lock if DB check fails
        await ReservationEngine.release_hold(ticket_id, user_id)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket is not available for reservation.")

    ticket.status = "HELD"
    expires_at = datetime.now(UTC) + timedelta(seconds=ttl)

    reservation = Reservation(user_id=user_id, ticket_id=ticket_id, status="PENDING", expires_at=expires_at)
    db.add(reservation)
    await db.commit()
    await db.refresh(reservation)

    # Publish event
    await EventBus.publish(
        "reservation.created",
        {
            "reservation_id": reservation.id,
            "ticket_id": ticket_id,
            "user_id": user_id,
            "price": ticket.price,
            "expires_at": expires_at.isoformat(),
        },
    )

    return reservation


@router.get("/reservations/{reservation_id}", response_model=ReservationResponseSchema)
async def get_reservation(reservation_id: str, db: AsyncSession = Depends(get_db)):
    reservation = await db.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
    return reservation
