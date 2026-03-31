from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

import redis.asyncio as redis
from fastapi import Depends

from configs.redis import RedisConfigDep


@asynccontextmanager
async def _get_redis(config: RedisConfigDep) -> AsyncGenerator[redis.Redis, None]:
    redis_client = redis.Redis(host=config.HOST, port=config.PORT, db=0)
    try:
        yield redis_client
    finally:
        await redis_client.aclose()


RedisClientDep = Annotated[AsyncGenerator[redis.Redis, None], Depends(_get_redis)]
