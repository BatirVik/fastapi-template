import asyncio
from typing import Any
import pytest
from alembic.config import Config
from sqlalchemy import make_url
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.core import DB, Base
from httpx import ASGITransport, AsyncClient
from sqlalchemy.sql import text

from alembic import command
from app.app import app
from app.config import get_config

config = get_config()


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True, scope="session")
async def db_lifespan(worker_id: Any):
    test_database = f"test_{worker_id}"
    url = make_url(str(config.DB_URL))

    await DB.connect(url)

    async with DB.get_connection() as conn:
        conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        _ = await conn.execute(text(f"DROP DATABASE IF EXISTS {test_database}"))
        _ = await conn.execute(text(f"CREATE DATABASE {test_database}"))

    await DB.connect(url.set(database=test_database))

    alembic_config = Config("alembic.ini")
    alembic_config.attributes["engine"] = DB.engine
    await asyncio.to_thread(command.upgrade, alembic_config, "head")
    yield
    await asyncio.to_thread(command.downgrade, alembic_config, "base")


@pytest.fixture
async def db():
    async with DB.get_session() as session:
        yield session


@pytest.fixture(autouse=True, scope="function")
async def truncate_tables(db: AsyncSession):
    if not Base.metadata.tables:
        return
    tablenames = ", ".join(table.name for table in Base.metadata.sorted_tables)
    _ = await db.execute(text(f"TRUNCATE TABLE {tablenames} CASCADE"))
    await db.commit()


@pytest.fixture
async def client():
    ac = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    async with ac:
        yield ac
