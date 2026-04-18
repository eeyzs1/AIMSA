import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.postgres import Base, get_db
from app.main import app

TEST_PG_HOST = os.environ.get("POSTGRES_HOST", "localhost")
TEST_PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
TEST_PG_USER = os.environ.get("POSTGRES_USER", "aimsa")
TEST_PG_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "aimsa_secret")
TEST_PG_DB = os.environ.get("POSTGRES_DB", "aimsa_test")

TEST_DB_URL = (
    f"postgresql+asyncpg://{TEST_PG_USER}:{TEST_PG_PASSWORD}"
    f"@{TEST_PG_HOST}:{TEST_PG_PORT}/{TEST_PG_DB}"
    f"?ssl=disable"
)

test_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args={"server_settings": {"jit": "off"}},
)
test_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with test_session() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
