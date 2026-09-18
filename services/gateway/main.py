from contextlib import asynccontextmanager

import httpx  # type: ignore
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status  # type: ignore

from services.common.config import settings
from services.gateway.auth_routes import router as auth_router
from services.gateway.database import init_db
from services.gateway.rate_limiter import SlidingWindowRateLimiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema
    await init_db()
    yield


app = FastAPI(
    title="Ticketing Platform API Gateway & Auth Service",
    description="Entrypoint for ticketing microservices with rate-limiting and JWT proxying",
    version="1.0.0",
    lifespan=lifespan,
)

# Apply rate limiter middleware to API routes (100 req/min limit)
rate_limiter = SlidingWindowRateLimiter(requests_limit=100, window_seconds=60)

app.include_router(auth_router, prefix="/api/v1", dependencies=[Depends(rate_limiter)])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "gateway_auth"}


# Helper function to proxy requests to upstream microservices
async def proxy_request(service_url: str, path: str, request: Request) -> Response:
    url = f"{service_url}{path}"
    headers = dict(request.headers)
    headers.pop("host", None)

    body = await request.body()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.request(
                method=request.method, url=url, headers=headers, params=request.query_params, content=body
            )
            return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Upstream service connection failed: {exc}"
            ) from exc


# Gateway proxy routes to upstream microservices
@app.api_route("/api/v1/catalog/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catalog_proxy(path: str, request: Request, _=Depends(rate_limiter)):
    return await proxy_request(settings.CATALOG_SERVICE_URL, f"/catalog/{path}", request)


@app.api_route("/api/v1/inventory/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def inventory_proxy(path: str, request: Request, _=Depends(rate_limiter)):
    return await proxy_request(settings.INVENTORY_SERVICE_URL, f"/inventory/{path}", request)


@app.api_route("/api/v1/checkout/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def checkout_proxy(path: str, request: Request, _=Depends(rate_limiter)):
    return await proxy_request(settings.CHECKOUT_SERVICE_URL, f"/checkout/{path}", request)
