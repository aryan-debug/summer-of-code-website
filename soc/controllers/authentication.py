from datetime import datetime
from typing import TypedDict

import bcrypt
import jwt
from bevy import Bevy, Inject
from bevy.providers import bevy_method
from pydantic import Field

from soc.config import BaseSettingsModel
from soc.database import Database
from soc.database.models.users import UserModel
from soc.models.users import User


class AuthTokenDict(TypedDict):
    user_id: int
    username: str


class JWTSettings(BaseSettingsModel):
    private_key: str = Field(default=None, env="SOC_JWT_PRIVATE_KEY")
    public_key: str = Field(default=None, env="SOC_JWT_PUBLIC_KEY")
    algorithm: str = Field(default="HS256", env="SOC_JWT_ALGORITHM")


class DiscordSettings(BaseSettingsModel):
    client_id: str = Field(default="", env="SOC_DISCORD_CLIENT_ID")
    client_secret: str = Field(default="", env="SOC_DISCORD_CLIENT_SECRET")
    redirect_uri: str = Field(default="", env="SOC_DISCORD_REDIRECT_URI")


class AuthenticationSettings(BaseSettingsModel):
    __config_key__ = "authentication"

    salt_rounds: int = Field(default=12, env="SOC_AUTH_SALT_ROUNDS")
    salt_prefix: bytes = Field(default=b"2b", env="SOC_AUTH_SALT_PREFIX")
    admin_email: str = Field(default="", env="SOC_AUTH_ADMIN_EMAIL")
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    discord: DiscordSettings = Field(default_factory=DiscordSettings)


class Authentication(Bevy):
    @bevy_method
    async def authenticate_user(
        self, name: str, password: str, database: Database = Inject
    ) -> User | None:
        user = await database.users.get_by_name(name)
        if user and bcrypt.checkpw(password.encode(), user.password.encode()):
            return user

        return None

    @bevy_method
    async def register_user(
        self,
        name: str,
        password: str,
        email: str,
        settings: AuthenticationSettings = Inject,
        database: Database = Inject,
    ):
        salt = bcrypt.gensalt(settings.salt_rounds, settings.salt_prefix)
        hashed_password = bcrypt.hashpw(password.encode(), salt).decode()
        await database.users.create(name, hashed_password, email)

    @bevy_method
    def create_user_access_token(self, user: User | UserModel) -> str:
        return self.create_token(user_id=user.id, username=user.username)

    @bevy_method
    def create_email_access_token(self, username: str, email: str) -> str:
        return self.create_token(username=username, email=email)

    @bevy_method
    def create_token(self, _settings: AuthenticationSettings = Inject, **data) -> str:
        return jwt.encode(
            data | {"created": int(datetime.now().timestamp())},
            _settings.jwt.private_key,
            _settings.jwt.algorithm,
        )
