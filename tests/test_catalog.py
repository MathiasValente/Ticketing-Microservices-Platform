import pytest  # type: ignore


@pytest.mark.asyncio
async def test_venue_and_event_catalog_flow(catalog_client):
    # 1. Create Venue
    venue_payload = {"name": "Madison Square Garden", "location": "New York, NY", "capacity": 20000}
    v_resp = await catalog_client.post("/catalog/venues", json=venue_payload)
    assert v_resp.status_code == 201
    venue_data = v_resp.json()
    venue_id = venue_data["id"]
    assert venue_data["name"] == venue_payload["name"]

    # 2. List Venues
    v_list_resp = await catalog_client.get("/catalog/venues")
    assert v_list_resp.status_code == 200
    assert len(v_list_resp.json()) == 1

    # 3. Create Event
    event_payload = {
        "title": "Rock Legends Live",
        "description": "Exclusive Stadium Show",
        "artist": "Rock Band",
        "venue_id": venue_id,
        "event_date": "2026-12-31T21:00:00Z",
        "seat_categories": [
            {"name": "VIP Floor", "price": 350.0, "total_seats": 50},
            {"name": "Standard Seat", "price": 100.0, "total_seats": 500},
        ],
    }
    e_resp = await catalog_client.post("/catalog/events", json=event_payload)
    assert e_resp.status_code == 201
    event_data = e_resp.json()
    event_id = event_data["id"]
    assert event_data["title"] == event_payload["title"]
    assert len(event_data["seat_categories"]) == 2

    # 4. Get Event Details
    e_get_resp = await catalog_client.get(f"/catalog/events/{event_id}")
    assert e_get_resp.status_code == 200
    assert e_get_resp.json()["id"] == event_id


@pytest.mark.asyncio
async def test_create_event_invalid_venue(catalog_client):
    event_payload = {
        "title": "Invalid Event",
        "artist": "Unknown",
        "venue_id": "non-existent-venue-id",
        "event_date": "2026-12-31T21:00:00Z",
        "seat_categories": [],
    }
    resp = await catalog_client.post("/catalog/events", json=event_payload)
    assert resp.status_code == 404
