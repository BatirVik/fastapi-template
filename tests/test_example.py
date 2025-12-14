from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def test_example(db: AsyncSession, client: AsyncClient):
    result = await db.execute(text("select 2 + 2"))
    assert result.scalar_one() == 4

    resp = await client.get("/health")
    assert resp.status_code == 204
