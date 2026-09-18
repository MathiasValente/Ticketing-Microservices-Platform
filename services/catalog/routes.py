import json

from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore
from sqlalchemy import select  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore
from sqlalchemy.orm import selectinload  # type: ignore

from services.catalog.database import get_db
from services.catalog.models import (
    Event,
    EventCreateSchema,
    EventResponseSchema,
    SeatCategory,
    Venue,
    VenueCreateSchema,
    VenueResponseSchema,
)
from services.common.redis_client import get_redis_client

router = APIRouter(prefix="/catalog", tags=["Catalog"])

CATALOG_CACHE_KEY_EVENTS = "catalog:events:all"


@router.post("/venues", response_model=VenueResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_venue(payload: VenueCreateSchema, db: AsyncSession = Depends(get_db)):
    venue = Venue(**payload.model_dump())
    db.add(venue)
    await db.commit()
    await db.refresh(venue)
    return venue


@router.get("/venues", response_model=list[VenueResponseSchema])
async def list_venues(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Venue))
    return result.scalars().all()


@router.post("/events", response_model=EventResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_event(payload: EventCreateSchema, db: AsyncSession = Depends(get_db)):
    # Check if venue exists
    venue = await db.get(Venue, payload.venue_id)
    if not venue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")

    event = Event(
        title=payload.title,
        description=payload.description,
        artist=payload.artist,
        venue_id=payload.venue_id,
        event_date=payload.event_date,
    )
    db.add(event)
    await db.flush()

    for sc in payload.seat_categories:
        seat_cat = SeatCategory(event_id=event.id, name=sc.name, price=sc.price, total_seats=sc.total_seats)
        db.add(seat_cat)

    await db.commit()

    # Invalidate Redis catalog cache
    try:
        redis_client = await get_redis_client()
        await redis_client.delete(CATALOG_CACHE_KEY_EVENTS)
    except Exception:
        pass

    # Fetch with relationships loaded
    result = await db.execute(
        select(Event)
        .options(selectinload(Event.venue), selectinload(Event.seat_categories))
        .where(Event.id == event.id)
    )
    return result.scalar_one()


@router.get("/events", response_model=list[EventResponseSchema])
async def list_events(db: AsyncSession = Depends(get_db)):
    redis_client = await get_redis_client()
    try:
        cached = await redis_client.get(CATALOG_CACHE_KEY_EVENTS)
        if cached:
            data = json.loads(cached)
            return data
    except Exception:
        pass

    result = await db.execute(
        select(Event).options(selectinload(Event.venue), selectinload(Event.seat_categories))
    )
    events = result.scalars().all()
    events_data = [EventResponseSchema.model_validate(e).model_dump(mode="json") for e in events]

    try:
        await redis_client.set(CATALOG_CACHE_KEY_EVENTS, json.dumps(events_data), ex=30)  # cache for 30s
    except Exception:
        pass

    return events_data


@router.get("/events/{event_id}", response_model=EventResponseSchema)
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Event)
        .options(selectinload(Event.venue), selectinload(Event.seat_categories))
        .where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event
