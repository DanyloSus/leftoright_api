from typing import List

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .base import Config


class CorsConfig(Config):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        env_prefix="CORS_",
    )

    ALLOW_ORIGINS: List[str] = Field(..., description="CORS allowed origins")
    ALLOW_METHODS: List[str] = Field(..., description="CORS allowed methods")
    ALLOW_HEADERS: List[str] = Field(..., description="CORS allowed headers")


_cors_settings = CorsConfig()


def get_cors_config() -> CorsConfig:
    return _cors_settings
