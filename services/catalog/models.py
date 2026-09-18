import uuid
from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.catalog.database import Base


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    events: Mapped[list["Event"]] = relationship("Event", back_populates="venue")

class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    artist: Mapped[str] = mapped_column(String, nullable=False)
    venue_id: Mapped[str] = mapped_column(String, ForeignKey("venues.id"), nullable=False)
    event_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String, default="UPCOMING") # UPCOMING, LIVE, COMPLETED, CANCELLED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    venue: Mapped["Venue"] = relationship("Venue", back_populates="events")
    seat_categories: Mapped[list["SeatCategory"]] = relationship("SeatCategory", back_populates="event", cascade="all, delete-orphan")

class SeatCategory(Base):
    __tablename__ = "seat_categories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(String, ForeignKey("events.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False) # e.g. "VIP Front Row", "General Admission", "Section 101"
    price: Mapped[float] = mapped_column(Float, nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)

    event: Mapped["Event"] = relationship("Event", back_populates="seat_categories")

# Pydantic Schemas
class VenueCreateSchema(BaseModel):
    name: str
    location: str
    capacity: int

class VenueResponseSchema(VenueCreateSchema):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class SeatCategoryCreateSchema(BaseModel):
    name: str
    price: float
    total_seats: int

class SeatCategoryResponseSchema(SeatCategoryCreateSchema):
    id: str
    event_id: str
    class Config:
        from_attributes = True

class EventCreateSchema(BaseModel):
    title: str
    description: str | None = None
    artist: str
    venue_id: str
    event_date: datetime
    seat_categories: list[SeatCategoryCreateSchema]

class EventResponseSchema(BaseModel):
    id: str
    title: str
    description: str | None
    artist: str
    venue_id: str
    event_date: datetime
    status: str
    venue: VenueResponseSchema | None
    seat_categories: list[SeatCategoryResponseSchema]
    created_at: datetime
    class Config:
        from_attributes = True
