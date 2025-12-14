import asyncio
from typing import Any
import pytest
from alembic.config import Config
from app.database.core import DB, Base
from httpx import ASGITransport, AsyncClient
from pydantic import PostgresDsn
from sqlalchemy.exc import ProgrammingError
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
    test_db_name = f"test_{worker_id}"
    await DB.connect(config.POSTGRES_URL.encoded_string())

    async with DB.get_connection() as conn:
        _ = await conn.execution_options(isolation_level="AUTOCOMMIT")
        try:
            _ = await conn.execute(text(f"DROP DATABASE {test_db_name}"))
        except ProgrammingError:
            pass

        _ = await conn.execute(text(f"CREATE DATABASE {test_db_name}"))

    # Reconnect to newly created test database
    host_info = config.POSTGRES_URL.hosts()[0]
    url = PostgresDsn.build(
        scheme=config.POSTGRES_URL.scheme,
        username=host_info.get("username"),
        password=host_info.get("password"),
        host=host_info.get("host"),
        port=host_info.get("port"),
        path=test_db_name,
    ).encoded_string()
    await DB.connect(url)

    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", url)
    await asyncio.get_event_loop().run_in_executor(
        None, command.upgrade, alembic_config, "head"
    )
    yield
    await asyncio.get_event_loop().run_in_executor(
        None, command.upgrade, alembic_config, "base"
    )


@pytest.fixture(autouse=True, scope="function")
async def truncate_tables():
    async with DB.get_session() as db:
        tablenames = ", ".join(table.name for table in Base.metadata.sorted_tables)
        if tablenames:
            _ = await db.execute(text(f"TRUNCATE TABLE {tablenames} CASCADE"))
            await db.commit()
    yield


@pytest.fixture
async def db():
    async with DB.get_session() as session:
        yield session


@pytest.fixture
async def client():
    ac = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    async with ac:
        yield ac
