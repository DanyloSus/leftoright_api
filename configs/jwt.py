from typing import Annotated

from fastapi import Depends
from pydantic_settings import SettingsConfigDict

from .base import Config


class JWTConfig(Config):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        env_prefix="JWT_",
    )

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 108000


_jwt_settings = JWTConfig()


def get_jwt_config() -> JWTConfig:
    return _jwt_settings


JWTConfigDep = Annotated[JWTConfig, Depends(get_jwt_config)]
