import uuid
from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from services.checkout.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    reservation_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    ticket_id: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, default="PENDING", index=True) # PENDING, PAID, FAILED
    idempotency_key: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id: Mapped[str] = mapped_column(String, ForeignKey("orders.id"), nullable=False)
    transaction_reference: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False) # SUCCESS, FAILED
    payment_method: Mapped[str] = mapped_column(String, default="CREDIT_CARD")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

# Pydantic Schemas
class PaymentProcessSchema(BaseModel):
    reservation_id: str
    ticket_id: str
    user_id: str
    amount: float
    idempotency_key: str
    simulate_failure: bool | None = False

class OrderResponseSchema(BaseModel):
    id: str
    user_id: str
    reservation_id: str
    ticket_id: str
    amount: float
    status: str
    idempotency_key: str
    created_at: datetime
    class Config:
        from_attributes = True
