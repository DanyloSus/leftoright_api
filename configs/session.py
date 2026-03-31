from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .database import db_settings

engine = create_async_engine(
    db_settings.async_url,
    pool_size=db_settings.POOL_SIZE,
    max_overflow=db_settings.MAX_OVERFLOW,
    pool_timeout=db_settings.POOL_TIMEOUT,
    pool_recycle=db_settings.POOL_RECYCLE,
    pool_pre_ping=True,
)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionFactory() as session:
        yield session


AsyncSessionDep = Annotated[AsyncSession, Depends(get_session)]
