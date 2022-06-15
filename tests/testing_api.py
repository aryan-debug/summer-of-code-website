import httpx
import jwt
import pytest
from bevy import Context
from sqlalchemy.ext.asyncio import AsyncEngine

from fuzzy import FuzzyValue
from soc.api import api_app
from soc.context import context as _context
from soc.controllers.authentication import AuthenticationSettings, JWTSettings
from soc.database.config import DatabaseSettings
from soc.database.models.base import BaseModel


@pytest.fixture()
async def context():
    return _context()


@pytest.fixture(autouse=True)
async def _setup_context(context: Context):
    context.add(
        DatabaseSettings(driver="sqlite+aiosqlite"),
        use_as=DatabaseSettings,
    )
    context.add(
        AuthenticationSettings(jwt=JWTSettings(private_key="TOP SECRET TEST KEY"))
    )


@pytest.fixture(autouse=True)
async def _setup_tables(context: Context):
    engine = context.create(AsyncEngine)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)


@pytest.fixture()
async def client(context):
    api_app.dependency_overrides[_context] = lambda: context
    async with httpx.AsyncClient(app=api_app, base_url="http://localhost") as client:
        yield client


@pytest.mark.asyncio
async def test_authentication_invalid_user(client):
    response = await client.post(
        "/authenticate", data={"username": "Bob", "password": "PASSWORD"}
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid user"}


@pytest.mark.asyncio
async def test_registration_authentication(client, context):
    response = await client.post(
        "/register",
        data={"username": "Bob", "password": "PASSWORD", "email": "bob@gmail.com"},
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "User successfully registered"}

    response = await client.post(
        "/authenticate", data={"username": "Bob", "password": "PASSWORD"}
    )
    json = response.json()
    assert response.status_code == 200
    assert json == {"access-token": FuzzyValue(str)}

    settings = context.get(AuthenticationSettings).jwt
    data = jwt.decode(json["access-token"], settings.private_key, settings.algorithm)
    assert data["username"] == "Bob"
