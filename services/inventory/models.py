import uuid
from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from services.inventory.database import Base


class TicketItem(Base):
    __tablename__ = "ticket_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    seat_category_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    seat_number: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, default="AVAILABLE", index=True) # AVAILABLE, HELD, SOLD
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    ticket_id: Mapped[str] = mapped_column(String, ForeignKey("ticket_items.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, default="PENDING", index=True) # PENDING, CONFIRMED, EXPIRED, CANCELLED
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

# Pydantic Schemas
class TicketCreateSchema(BaseModel):
    event_id: str
    seat_category_id: str
    seat_number: str
    price: float

class HoldRequestSchema(BaseModel):
    ticket_id: str
    user_id: str
    hold_ttl_seconds: int | None = 600 # 10 minutes default

class ReservationResponseSchema(BaseModel):
    id: str
    user_id: str
    ticket_id: str
    status: str
    expires_at: datetime
    created_at: datetime
    class Config:
        from_attributes = True

class TicketResponseSchema(BaseModel):
    id: str
    event_id: str
    seat_category_id: str
    seat_number: str
    price: float
    status: str
    class Config:
        from_attributes = True
