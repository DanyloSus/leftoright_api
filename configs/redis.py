from typing import Annotated

from fastapi import Depends
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .base import Config


class RedisConfig(Config):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    HOST: str = Field(..., description="redis host", alias="REDIS_HOST")
    PORT: int = Field(..., description="redis port", alias="REDIS_PORT")

    @property
    def url(self):
        return f"redis://{self.HOST}:{self.PORT}"


_redis_settings = RedisConfig()


def get_redis_config() -> RedisConfig:
    return _redis_settings


RedisConfigDep = Annotated[RedisConfig, Depends(get_redis_config)]
