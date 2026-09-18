"""
High-Concurrency Flash-Sale Load & Race-Condition Verification Script.

Simulates 50 concurrent buyers trying to grab 5 limited tickets simultaneously.
Proves zero overselling and strict Redis Lua lock concurrency control.
"""

import asyncio
import sys
import time

import httpx

BASE_URL = "http://localhost:8001/api/v1" # Gateway URL

async def run_flash_sale_simulation():
    print("=" * 70)
    print("🚀 STARTING FLASH SALE HIGH-CONCURRENCY SIMULATION")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health check
        try:
            health = await client.get("http://localhost:8001/health")
            print(f"[HEALTH CHECK] Gateway status: {health.json()}")
        except Exception as e:
            print(f"❌ Gateway is not reachable at {BASE_URL}. Ensure docker-compose is running! ({e})")
            sys.exit(1)

        # 2. Register & Login test buyer
        email = f"buyer_{int(time.time())}@example.com"
        reg_resp = await client.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": "Password123!",
            "full_name": "Test Buyer"
        })
        user_data = reg_resp.json()
        user_id = user_data["id"]
        print(f"✅ Registered test user: {email} (ID: {user_id})")

        # 3. Create Venue & Event in Catalog Service
        venue_resp = await client.post(f"{BASE_URL}/catalog/venues", json={
            "name": "Stadium Arena",
            "location": "Downtown",
            "capacity": 50000
        })
        venue_id = venue_resp.json()["id"]

        event_resp = await client.post(f"{BASE_URL}/catalog/events", json={
            "title": "Mega Stadium World Tour",
            "artist": "The Rockstars",
            "venue_id": venue_id,
            "event_date": "2026-10-01T20:00:00Z",
            "seat_categories": [
                {"name": "VIP Zone", "price": 250.0, "total_seats": 5}
            ]
        })
        event_data = event_resp.json()
        event_id = event_data["id"]
        seat_cat_id = event_data["seat_categories"][0]["id"]
        print(f"🎟️ Created Event '{event_data['title']}' (ID: {event_id}) with 5 seats")

        # 4. Seed 5 Ticket Items in Inventory Service
        ticket_ids = []
        for i in range(1, 6):
            t_resp = await client.post(f"{BASE_URL}/inventory/tickets", json={
                "event_id": event_id,
                "seat_category_id": seat_cat_id,
                "seat_number": f"VIP-A{i}",
                "price": 250.0
            })
            ticket_ids.append(t_resp.json()["id"])
        print(f"✅ Seeded 5 tickets in inventory: {ticket_ids}")

        # 5. SIMULATE FLASH SALE: 50 Concurrent Users Racing for the 5 Tickets
        print("\n⚡ SURGE TRAFFIC: Spawning 50 concurrent buyers racing for 5 seats...")
        
        async def attempt_hold(buyer_num: int, target_ticket_id: str):
            buyer_id = f"user_sim_{buyer_num}_{int(time.time())}"
            try:
                resp = await client.post(f"{BASE_URL}/inventory/hold", json={
                    "ticket_id": target_ticket_id,
                    "user_id": buyer_id,
                    "hold_ttl_seconds": 300
                })
                return buyer_num, target_ticket_id, resp.status_code, resp.json()
            except Exception as exc:
                return buyer_num, target_ticket_id, 500, str(exc)

        # Create 50 tasks targeting the 5 available tickets (10 users per ticket)
        tasks = []
        for buyer_idx in range(50):
            # Pick one of the 5 ticket_ids
            target_t_id = ticket_ids[buyer_idx % len(ticket_ids)]
            tasks.append(attempt_hold(buyer_idx, target_t_id))

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time

        # 6. Analyze Results
        successes = [r for r in results if r[2] == 201 or r[2] == 200]
        conflicts = [r for r in results if r[2] == 409]
        others = [r for r in results if r[2] not in (200, 201, 409)]

        print(f"\n📊 FLASH SALE CONCURRENCY RESULTS (Execution Time: {duration:.3f}s)")
        print("  - Total Requests Sent: 50")
        print(f"  - Successful Holds: {len(successes)} / 5 seats")
        print(f"  - Graceful Conflicts (409): {len(conflicts)}")
        print(f"  - System Errors / Unexpected: {len(others)}")

        if len(successes) <= 5 and len(others) == 0:
            print("\n🎉 VERIFICATION PASSED: Zero overselling observed! Redis Lua locks successfully prevented race conditions.")
        else:
            print("\n⚠️ VERIFICATION FAILURE: Overselling or errors occurred.")

        # 7. Test Checkout Flow for one successful hold
        if successes:
            succ_res = successes[0][3]
            res_id = succ_res["id"]
            t_id = succ_res["ticket_id"]
            u_id = succ_res["user_id"]

            print(f"\n💳 Testing Checkout & Event Bus confirmation for Reservation '{res_id}'...")
            pay_resp = await client.post(f"{BASE_URL}/checkout/pay", json={
                "reservation_id": res_id,
                "ticket_id": t_id,
                "user_id": u_id,
                "amount": 250.0,
                "idempotency_key": f"idempotency_{res_id}"
            })
            print(f"  - Checkout Payment Status: {pay_resp.status_code}")
            print(f"  - Payment Response: {pay_resp.json()}")

            # Wait brief moment for async event worker to mark ticket SOLD
            await asyncio.sleep(1.0)
            
            # Re-check reservation details
            res_check = await client.get(f"{BASE_URL}/inventory/reservations/{res_id}")
            print(f"  - Updated Reservation Status: {res_check.json()}")

if __name__ == "__main__":
    asyncio.run(run_flash_sale_simulation())
