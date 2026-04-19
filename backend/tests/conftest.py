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


def _make_engine():
    return create_async_engine(
        TEST_DB_URL,
        echo=False,
        pool_pre_ping=True,
        connect_args={"server_settings": {"jit": "off"}},
    )


async def override_get_db():
    engine = _make_engine()
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def setup_db():
    engine = _make_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
