import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.checkout.models import Order, Payment, PaymentProcessSchema
from services.common.event_bus import EventBus

logger = logging.getLogger("payment_processor")

class PaymentProcessor:
    """
    Idempotent payment processing engine.
    Ensures payment transactions are executed once and emits asynchronous payment events.
    """

    @staticmethod
    async def process_payment(payload: PaymentProcessSchema, db: AsyncSession) -> Order:
        # Check idempotency key to prevent double charging
        result = await db.execute(select(Order).where(Order.idempotency_key == payload.idempotency_key))
        existing_order = result.scalar_one_or_none()
        if existing_order:
            logger.info(f"[PAYMENT IDEMPOTENCY] Returned existing order '{existing_order.id}' for key '{payload.idempotency_key}'")
            return existing_order

        # Create Order record
        order = Order(
            user_id=payload.user_id,
            reservation_id=payload.reservation_id,
            ticket_id=payload.ticket_id,
            amount=payload.amount,
            status="PENDING",
            idempotency_key=payload.idempotency_key
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)

        # Simulate Payment Gateway processing
        payment_success = not payload.simulate_failure
        payment_status = "SUCCESS" if payment_success else "FAILED"
        txn_ref = f"TXN-{uuid.uuid4().hex[:12].upper()}"

        payment = Payment(
            order_id=order.id,
            transaction_reference=txn_ref,
            status=payment_status,
            payment_method="CREDIT_CARD"
        )
        db.add(payment)

        if payment_success:
            order.status = "PAID"
            await db.commit()
            logger.info(f"[PAYMENT SUCCESS] Order '{order.id}' paid successfully. Txn Ref: {txn_ref}")
            
            # Publish event to Event Bus
            await EventBus.publish("payment.completed", {
                "order_id": order.id,
                "reservation_id": payload.reservation_id,
                "ticket_id": payload.ticket_id,
                "user_id": payload.user_id,
                "transaction_reference": txn_ref
            })
        else:
            order.status = "FAILED"
            await db.commit()
            logger.warning(f"[PAYMENT FAILED] Order '{order.id}' failed simulation. Txn Ref: {txn_ref}")
            
            # Publish failure event
            await EventBus.publish("payment.failed", {
                "order_id": order.id,
                "reservation_id": payload.reservation_id,
                "ticket_id": payload.ticket_id,
                "user_id": payload.user_id,
                "reason": "Payment gateway failure simulation"
            })

        await db.refresh(order)
        return order
