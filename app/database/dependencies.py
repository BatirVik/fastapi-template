from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.core import DB


async def get_session():
    async with DB.get_session() as session:
        yield session
        await session.commit()


SessionDepends = Annotated[AsyncSession, Depends(get_session)]
