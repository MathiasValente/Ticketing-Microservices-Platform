from unittest.mock import AsyncMock, patch

import pytest  # type: ignore


@pytest.mark.asyncio
async def test_idempotent_payment_processing(checkout_client):
    pay_payload = {
        "reservation_id": "res-001",
        "ticket_id": "ticket-001",
        "user_id": "user-001",
        "amount": 250.0,
        "idempotency_key": "unique_idempotency_key_12345",
    }

    with patch("services.common.event_bus.EventBus.publish", new_callable=AsyncMock) as mock_pub:
        # First payment attempt
        resp1 = await checkout_client.post("/checkout/pay", json=pay_payload)
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["status"] == "PAID"
        order_id = data1["id"]

        # Verify event was published
        mock_pub.assert_called_once()
        assert mock_pub.call_args[0][0] == "payment.completed"

        # Second payment attempt with exact same idempotency key
        resp2 = await checkout_client.post("/checkout/pay", json=pay_payload)
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["id"] == order_id  # Returned exact same order, zero double-charge!


@pytest.mark.asyncio
async def test_payment_failure_simulation(checkout_client):
    fail_payload = {
        "reservation_id": "res-002",
        "ticket_id": "ticket-002",
        "user_id": "user-002",
        "amount": 100.0,
        "idempotency_key": "failed_txn_key_999",
        "simulate_failure": True,
    }

    with patch("services.common.event_bus.EventBus.publish", new_callable=AsyncMock) as mock_pub:
        resp = await checkout_client.post("/checkout/pay", json=fail_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "FAILED"

        # Verify failure event was published
        mock_pub.assert_called_once()
        assert mock_pub.call_args[0][0] == "payment.failed"
