import httpx
import pytest
from bevy import Context
from sqlalchemy.ext.asyncio import AsyncEngine

from soc.api import api_app
from soc.context import context as _context
from soc.database.config import DatabaseSettings
from soc.database.models.base import BaseModel


async def _setup_tables(context: Context):
    engine = context.create(AsyncEngine)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)


async def _connect_db(context: Context):
    context.add(
        DatabaseSettings(driver="sqlite+aiosqlite"),
        use_as=DatabaseSettings,
    )


@pytest.fixture()
async def context():
    return _context()


@pytest.fixture()
async def client(context):
    api_app.dependency_overrides[_context] = lambda: context
    async with httpx.AsyncClient(app=api_app, base_url="http://localhost") as client:
        yield client


@pytest.mark.asyncio
async def test_database(client, context):
    response = await client.get("/")
    assert response.json() == {"message": "Hello World!"}
