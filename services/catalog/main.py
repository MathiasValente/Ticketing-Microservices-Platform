from contextlib import asynccontextmanager

from fastapi import FastAPI  # type: ignore

from services.catalog.database import init_db
from services.catalog.routes import router as catalog_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Event & Catalog Service",
    description="Manages venues, concerts, and seating catalog",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(catalog_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "catalog_service"}
