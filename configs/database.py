from pydantic import Field

from .base import Config


class DatabaseConfig(Config):
    USER: str = Field(..., description="The username used to authenticate with the database")
    PASSWORD: str = Field(..., description="The password used to authenticate with the database")
    HOST: str = Field(..., description="The hostname or IP address of the database server")
    PORT: int = Field(..., description="The port number on which the database server is listening")
    NAME: str = Field(..., description="The name of the specific database to connect to")

    @property
    def sync_url(self) -> str:
        return f'postgresql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}'

    @property
    def async_url(self) -> str:
        return f'postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}'

    class Config:
        env_prefix = 'DB_'


db_settings = DatabaseConfig()
