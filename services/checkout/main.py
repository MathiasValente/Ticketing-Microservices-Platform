from contextlib import asynccontextmanager

from fastapi import FastAPI  # type: ignore

from services.checkout.database import init_db
from services.checkout.routes import router as checkout_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Checkout & Payment Service",
    description="Handles payment processing transactions, idempotency, and order confirmation events",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(checkout_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "checkout_service"}
