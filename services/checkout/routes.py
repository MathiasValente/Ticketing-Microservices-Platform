from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore

from services.checkout.database import get_db
from services.checkout.models import Order, OrderResponseSchema, PaymentProcessSchema
from services.checkout.payment_processor import PaymentProcessor

router = APIRouter(prefix="/checkout", tags=["Checkout & Payment"])


@router.post("/pay", response_model=OrderResponseSchema, status_code=status.HTTP_200_OK)
async def execute_checkout(payload: PaymentProcessSchema, db: AsyncSession = Depends(get_db)):
    order = await PaymentProcessor.process_payment(payload, db)
    return order


@router.get("/orders/{order_id}", response_model=OrderResponseSchema)
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
