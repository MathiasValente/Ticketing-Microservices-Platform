import asyncio
from collections.abc import AsyncGenerator

import pytest  # type: ignore
from httpx import ASGITransport, AsyncClient  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # type: ignore
from sqlalchemy.pool import StaticPool  # type: ignore

from services.catalog.database import Base as CatalogBase, get_db as get_catalog_db
from services.catalog.main import app as catalog_app
from services.checkout.database import Base as CheckoutBase, get_db as get_checkout_db
from services.checkout.main import app as checkout_app
from services.gateway.database import Base as AuthBase, get_db as get_auth_db
from services.gateway.main import app as gateway_app
from services.inventory.database import Base as InventoryBase, get_db as get_inventory_db
from services.inventory.main import app as inventory_app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


async def create_test_db(base):
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(base.metadata.create_all)
    return engine, async_session


@pytest.fixture
async def auth_db_session() -> AsyncGenerator[AsyncSession, None]:
    engine, async_session = await create_test_db(AuthBase)
    async with async_session() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def catalog_db_session() -> AsyncGenerator[AsyncSession, None]:
    engine, async_session = await create_test_db(CatalogBase)
    async with async_session() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def inventory_db_session() -> AsyncGenerator[AsyncSession, None]:
    engine, async_session = await create_test_db(InventoryBase)
    async with async_session() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def checkout_db_session() -> AsyncGenerator[AsyncSession, None]:
    engine, async_session = await create_test_db(CheckoutBase)
    async with async_session() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def gateway_client(auth_db_session) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield auth_db_session

    gateway_app.dependency_overrides[get_auth_db] = override_get_db
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    gateway_app.dependency_overrides.clear()


@pytest.fixture
async def catalog_client(catalog_db_session) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield catalog_db_session

    catalog_app.dependency_overrides[get_catalog_db] = override_get_db
    transport = ASGITransport(app=catalog_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    catalog_app.dependency_overrides.clear()


@pytest.fixture
async def inventory_client(inventory_db_session) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield inventory_db_session

    inventory_app.dependency_overrides[get_inventory_db] = override_get_db
    transport = ASGITransport(app=inventory_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    inventory_app.dependency_overrides.clear()


@pytest.fixture
async def checkout_client(checkout_db_session) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield checkout_db_session

    checkout_app.dependency_overrides[get_checkout_db] = override_get_db
    transport = ASGITransport(app=checkout_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    checkout_app.dependency_overrides.clear()
