from unittest.mock import AsyncMock, patch

import pytest  # type: ignore


@pytest.mark.asyncio
async def test_ticket_creation_and_listing(inventory_client):
    ticket_payload = {
        "event_id": "event-123",
        "seat_category_id": "cat-456",
        "seat_number": "A1",
        "price": 150.0,
    }
    t_resp = await inventory_client.post("/inventory/tickets", json=ticket_payload)
    assert t_resp.status_code == 201
    t_data = t_resp.json()
    assert t_data["seat_number"] == "A1"
    assert t_data["status"] == "AVAILABLE"

    list_resp = await inventory_client.get("/inventory/tickets/event/event-123")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


@pytest.mark.asyncio
async def test_hold_ticket_success_and_conflict(inventory_client):
    # Seed ticket
    t_resp = await inventory_client.post(
        "/inventory/tickets",
        json={"event_id": "event-999", "seat_category_id": "cat-999", "seat_number": "B10", "price": 200.0},
    )
    ticket_id = t_resp.json()["id"]

    # Mock Redis Lua Script lock to succeed for first user and fail for second user
    with (
        patch(
            "services.inventory.reservation_engine.ReservationEngine.try_acquire_hold", new_callable=AsyncMock
        ) as mock_hold,
        patch("services.common.event_bus.EventBus.publish", new_callable=AsyncMock),
    ):
        mock_hold.return_value = (True, "user:buyer-1")

        hold_resp1 = await inventory_client.post(
            "/inventory/hold", json={"ticket_id": ticket_id, "user_id": "buyer-1", "hold_ttl_seconds": 300}
        )
        assert hold_resp1.status_code == 201
        res1_data = hold_resp1.json()
        assert res1_data["status"] == "PENDING"
        assert res1_data["user_id"] == "buyer-1"

        # Simulate second user attempting to hold same locked ticket
        mock_hold.return_value = (False, None)
        hold_resp2 = await inventory_client.post(
            "/inventory/hold", json={"ticket_id": ticket_id, "user_id": "buyer-2", "hold_ttl_seconds": 300}
        )
        assert hold_resp2.status_code == 409
