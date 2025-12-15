from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, ClassVar, override
from uuid import UUID

from sqlalchemy import URL, MetaData, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import get_config
from app.logger import logger

config = get_config()


class DB:
    engine: AsyncEngine | None = None
    session_factory: async_sessionmaker[AsyncSession] | None = None

    @classmethod
    async def connect(cls, url: str | URL) -> None:
        if cls.engine or cls.session_factory:
            await cls.disconnect()

        engine = create_async_engine(
            url,
            pool_size=config.DB_POOL_SIZE,
            max_overflow=config.DB_MAX_OVERFLOW,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_timeout=30,
        )
        session_factory = async_sessionmaker(
            engine, autoflush=False, expire_on_commit=False
        )
        async with engine.connect():
            pass

        cls.engine = engine
        cls.session_factory = session_factory

        logger.info("Database connected")

    @classmethod
    async def disconnect(cls) -> None:
        if cls.engine:
            await cls.engine.dispose()
            cls.engine = None
            cls.session_factory = None
            logger.info("Database disconnected")

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        if not cls.engine:
            raise RuntimeError("Database not connected")
        async with cls.engine.connect() as conn:
            yield conn

    @classmethod
    @asynccontextmanager
    async def get_session(cls):
        if not cls.session_factory:
            raise RuntimeError("Database not connected")
        async with cls.session_factory() as session:
            yield session


NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_ix",
    "uq": "%(table_name)s_%(column_0_name)s_uq",
    "ck": "%(table_name)s_%(constraint_name)s_ck",
    "fk": "%(table_name)s_%(column_0_name)s_fk",
    "pk": "%(table_name)s_pk",
}


class Base(DeclarativeBase):
    metadata: ClassVar[MetaData] = MetaData(naming_convention=NAMING_CONVENTION)

    type_annotation_map: dict[Any, Any] = {
        datetime: postgresql.TIMESTAMP(True),
        UUID: postgresql.UUID(True),
    }


class BaseMixin:
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=func.uuidv7(),  # POSTGRES version >= 18
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    @override
    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.id})"
