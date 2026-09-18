import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI  # type: ignore

from services.inventory.database import init_db
from services.inventory.routes import router as inventory_router
from services.inventory.worker import start_event_listener


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Start background event listener task
    worker_task = asyncio.create_task(start_event_listener())
    yield
    worker_task.cancel()


app = FastAPI(
    title="Inventory & Booking Service",
    description="High-concurrency atomic seat reservation engine powered by Redis Lua locks",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(inventory_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "inventory_service"}
