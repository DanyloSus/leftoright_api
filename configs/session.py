from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .database import db_settings

engine = create_async_engine(db_settings.async_url)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionFactory() as session:
        yield session


AsyncSessionDep = Annotated[AsyncSession, Depends(get_session)]
